#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE, STDOUT
import logme
import os
import func
import sys
import time
import datetime
import signal
import threading

menu_text = "Troubleshooting Options"
menu_item = [	["Run fw monitor with filter",		"troubleshooting.fwmonitor()"],
		["Run tcpdump with filter",             "troubleshooting.tcpdump()"],
		["Run tcpdump, capture fragmented packets","troubleshooting.tcpdump('-i any \"(ip[6:2] & 0x1fff) != 0\" -nn')"],
		["Run zdebug with options",		"troubleshooting.zdebug()"],
		["Print connection table - raw",	"troubleshooting.print_table('connections')"],
		["Print connection table - formatted",	"troubleshooting.print_table('connections', True)"],
		["Clear connection table (ALL!)",	"troubleshooting.clear_table('connections')"],
		["Clear specific connections from table","troubleshooting.clear_table_input('connections')"],
		["STOP CheckPoint Services",		"troubleshooting.run_cpstop()"],
		["STOP CheckPoint Services and keep policy","troubleshooting.run_cpstop('-fwflag -proc')"],
		["UNLOAD Security/TP Policy",		"troubleshooting.load_policy(False)"],
		["FETCH  Security/TP Policy",		"troubleshooting.load_policy(True)"],
		["Disable Antispoofing",		"troubleshooting.run_spoofing(0)"],
		["Enable Antispoofing",			"troubleshooting.run_spoofing(1)"],
		["ClusterXL Status",			"troubleshooting.clusterxl_status()"],
		["SecureXL DoS Mitigation Status",	"troubleshooting.run_securexl_dos()"],
		["Display VPN Tunnel Status",		"troubleshooting.print_vpn()"]]

if func.isFirewall() and not func.isFWUserMode():
	menu_item.append(["TOP 15 heavy F2F Connections (specific worker)",	"troubleshooting.select_f2f_stats()"])
	menu_item.append(["TOP 15 heavy F2F Connections (all worker!)",	"troubleshooting.print_f2f_stats(-1)"])

if func.isFirewall() and func.isFWUserMode():
	menu_item.append(["Display user-mode cpu ressources",	"troubleshooting.run_top('-H -p `pidof fwk`')"])

if func.isFirewall():
	menu_item.append(["Measure kernel delay (EXPERIMENTAL!)",	"troubleshooting.fwkern_delay()"])
	menu_item.append(["Disable IPS on the fly",	"troubleshooting.run_ips(False)"])
	menu_item.append(["Enable  IPS on the fly",	"troubleshooting.run_ips(True)"])

menu_item.append(["Print heavy conns detected by CoreXL",	"troubleshooting.print_heavy_conn()"])
menu_item.append(["Back to Main Menu",	 		"menu_set('main')"])


def get_results(clear = False):
        global results
        res = results
        if clear:
                results = []
        return res

def add_text():
        return menu_text

def add_item():
        return menu_item

def print_results():
	global results
	logme.results(results)
	results = []

connections = {}
match_forward = 0
match_reverse = 0
stopme = False
local_ips = []

def fwkern_get_ifaces():
	global local_ips
	ipaddr = []
	out, err = func.execute_command("ifconfig | grep 'inet addr'")
	for line in out:
		tmp = line.replace('inet addr:','').split()
		ipaddr.append(tmp[0])
	local_ips = ipaddr


def fwkern_check_inbound(iface):
	tmp = iface.split(":")
	tmp = tmp[1].split("[")[0]
	if "i" == str(tmp):
		return True
	else:
		return False


def fwkern_calc_delay(time1, time2):
	t1 = datetime.datetime.strptime(time1, '%H:%M:%S.%f')
	t2 = datetime.datetime.strptime(time2, '%H:%M:%S.%f')
	delay = str(t2 - t1)[6:]
	return delay


def fwkern_parse(one, two):
	global connections
	global match_forward
	global match_reverse
	global local_ips
	l1 = one.split()
	l2 = two.split()
	worker    = l1[0]
	date      = l1[1]
	time      = l1[2]
	interface = l1[3]
	src       = l1[4]
	dst       = l1[6]
	len       = l1[8].replace("len=", "")
	id        = l1[9]
	src_port  = l2[1]
	dst_port  = l2[3]
	tuple     = (src, src_port, dst, dst_port)
	tuple_r   = (dst, dst_port, src, src_port)
	# filter out connection from or to gateway
	if src in local_ips or dst in local_ips:
		return
	# check forward connection mapping
	if tuple in connections:
		if fwkern_check_inbound(interface):
			connections[tuple]["in"] = time
		else:
			connections[tuple]["out"] = time
			connections[tuple]["delay"] = fwkern_calc_delay(connections[tuple]["in"], connections[tuple]["out"])
			connections[tuple]["bytes"] = str(int(connections[tuple]["bytes"]) + int(len))
		match_forward = match_forward + 1
		return
	# check reverse connection mapping
	if tuple_r in connections:
		if fwkern_check_inbound(interface):
			connections[tuple_r]["in"] = time
		else:
			connections[tuple_r]["out"] = time
			connections[tuple_r]["delay"] = fwkern_calc_delay(connections[tuple_r]["in"], connections[tuple_r]["out"])
			connections[tuple_r]["bytes"] = str(int(connections[tuple_r]["bytes"]) + int(len))
		match_reverse = match_reverse + 1
		return
	connections[tuple] = {"worker": worker, "time": time, "interface": interface, "id": id, "len": len, "in": time, "out": "-1", "delay": "-1", "bytes": "0"}


def fwkern_start():
	global stopme
	stopme = False
	fwkern_get_ifaces()
	cmd = "fw monitor -T -m iO"
	p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True, bufsize=1, universal_newlines=True)
	for line in iter(p.stdout.readline, b''):
		if stopme:	return
		tmp = line.strip('\n')
		# exclude other protocols than tcp or udp
		if "(TCP)" in tmp or "(UDP)" in tmp:
			# matched first line of output
			line_first = tmp
		if "TCP:" in tmp or "UDP:" in tmp:
			# matched second line
			line_second = tmp
			fwkern_parse(line_first, line_second)
	p.stdout.close()
	p.wait()
	stopme = True


def fwkern_output():
	global connections
	global stopme
	global match_forward
	global match_reverse
	max = 25
	CURSOR_UP_ONE = '\x1b[1A'
	ERASE_LINE = '\x1b[2K'
	printed = False
	print("** Starting Kernel Debug! Just wait a second...")
	print("** Press CTRL+C to exit.")
	print("")
	time.sleep(10)
	try:
		while(True):
			if printed:
				for i in range(1, count + 5):
					sys.stdout.write(CURSOR_UP_ONE)
					sys.stdout.write(ERASE_LINE)
			count = 0
			if stopme: break
			output = "* Last Update: " + str(datetime.datetime.now())
			output = output + "\n" + "* Seen connections count: " + str(len(connections))
			output = output + "\n" + "* Matching Tuples; Forward=" + str(match_forward) + " , Reverse=" + str(match_reverse) + "\n\n" 
			for key, val in reversed(sorted(connections.items(), key=lambda item: item[1]["delay"])):
				if val["delay"] != "-1":
					if count > max:	break
					if stopme:	break
					delay = str(val["delay"])
					bytes = str(val["bytes"])
					mylen = 55
					mylen = mylen - len(str(key))
					output = output + (str(key) + mylen*" " + ", Delay: " + str(delay) + " seconds, bytes: " + str(bytes)) + "\n"
					count = count + 1
			sys.stdout.write(output)
			sys.stdout.flush()
			printed = True
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	print("** Stopping Kernel Debug! Just wait a second...")
	stopme = True


def fwkern_delay():
	global stopme
	t1 = threading.Thread(target=fwkern_start)
	t1.start()
	fwkern_output()
	stopme = True
	t1.join()
	os.system("fw monitor -U")
	print("** Done!")
	

def ip2hex(ipaddr):
	if ipaddr != "":
		a = ipaddr.split('.')
		b = hex(int(a[0]))[2:].zfill(2) + hex(int(a[1]))[2:].zfill(2) + hex(int(a[2]))[2:].zfill(2) + hex(int(a[3]))[2:].zfill(2)
		b = b.replace('0x', '')
		b = b.lower()
		return b
	else:
		return "ffffffff".lower()


def run_ips(ena):
	print("")
	if ena:
		cmd = "ips on"
	else:
		cmd = "ips off -n"
	func.confirm(cmd)
	print("")


def run_securexl_dos():
	print("")
	cmd = "fwaccel dos config get ; fwaccel dos stats get"
	print("Executing command:")
	print(cmd)
	os.system(cmd)
	print("")


def run_spoofing(val):
	print("")
	print("Modify kernel parameters for spoofing:")
	cmd = "fw ctl set int fw_antispoofing_enabled " + str(val)
	func.confirm(cmd)
	cmd = "fw ctl set int fw_local_interface_anti_spoofing " + str(val)
	func.confirm(cmd)
	print("")

def run_cpstop(parms = ""):
	print("")
	print("Stopping CheckPoint Services...")
	cmd = "cpstop " + parms
	func.confirm(cmd)
	print("")


def print_heavy_conn():
	print("")
	print("Printing heavy connections:")
	print("fw ctl multik print_heavy_conn")
	print(" ")
	os.system("fw ctl multik print_heavy_conn")
	print("")

def run_top(filter = ""):
	print("")
	print("Running top command:")
	cmd = "top " + filter
	print(cmd)
	print("")
	os.system(cmd)
	print("")


def zdebug():
	print("")
	print("Defaults listed in brackets, just press return")
	print("to accept. Press STRG+C to stop debug!")
	print("")
	buf = input("Enter buffer  [1024]: ")
	if buf != "":
		buf = "-buf " + buf + " "
	mod = input("Enter module  [fw]  : ")
	if mod != "":
		mod = "-m " + mod
	opt = input("Enter options [drop]: ")
	if opt == "":
		opt = "drop"
	print("")
	fil = input("Enter grep filter []: ")
	if fil != "":
		fil = " grep -i '"+fil+"'"
	cmd = "fw ctl zdebug " + buf + mod + " + " + opt + fil
	print("")
	print("Executing command:")
	print(cmd)
	print("")
	os.system(cmd)
	print("")
	print("Resetting kernel filter...")
	cmd = "fw ctl debug 0"
	print(cmd)
	os.system(cmd)
	print("")


def load_policy(ena):
	print("")
	if ena:
		s = input("Enter Security Management Server IP: ")
		cmd = "fw fetch " + s
		print("")
		func.confirm(cmd)
		print("")
		cmd = "fw amw fetch " + s
		func.confirm(cmd)
	else:
		cmd = "fw unloadlocal"
		func.confirm(cmd)
		print("")
		cmd = "fw amw unload"
		func.confirm(cmd)
		


def fwmonitor():
	print("Example(s) for filter string:")
	print("host(1.1.1.1)")
	print("net(192.168.0.0,24)")
	print("icmp")
	print("")
	s = input("Enter filter string: ")
	print("")
	print("Executing command:")
	cmd = 'fw monitor -e "accept ' + s + ';"'
	print(cmd)
	print("")
	os.system(cmd)


def tcpdump(filter = ""):
	if filter == "":
		print("Example(s) for interface:")
		print("eth1")
		print("eth6.101")
		print("")
		print("Example(s) for filter string:")
		print("host 1.1.1.1")
		print("icmp")
		print("")
		int = input("Enter interface    : ")
		fil = input("Enter filter string: ")
		print("")
		cmd = "tcpdump -i " + int + " -s0 -nnnnn -vvvvvv " + fil
	else:
		cmd = "tcpdump " + filter
	print("Executing command:")
	print(cmd)
	print("")
	os.system(cmd)


def print_vpn():
	vpn_table_tab = "local_meta_sas"
	vpn_table = []
	vpn_links = {}
	logme.loader()
	out, err = func.execute_command("fw tab -t " + vpn_table_tab + " -u | awk 'NR>3 { print $0 }' | grep -v '\->'")
	for line in out:
		logme.loader()
		tmp = line.strip("\n").strip("<").strip(">")
		tmp = tmp.split(",")
		if len(tmp) > 10:
			vpn_table.append(tmp)
	out, err = func.execute_command("fw tab -t resolved_link -u | awk 'NR>3 { print $0 }'")
	for line in out:
		logme.loader()
		tmp = line.strip("\n").strip("<").strip(">")
		remote_id = tmp.split(';')[0]
		data = tmp.split(',')
		if not remote_id in vpn_links and len(data) > 10:
			vpn_links[remote_id] = data[1].strip(' ')
	print(" %-8s %17s %17s %20s %20s" % ("ID", "Remote IP", "Resolved Link", "Local Subnet", "Remote Subnet"))
	print(" " + 86*"=")
	for e in vpn_table:
		tunnel_id     = e[10].strip(' ')
		remote_ip     = func.hex2ip(e[0])
		if e[0] in vpn_links:
			remote_link   = func.hex2ip(vpn_links[e[0]])
		else:
			remote_link   = "0.0.0.0"
		local_subnet  = func.calc_subnet(func.hex2ip(e[1]), func.hex2ip(e[2]))
		remote_subnet = func.calc_subnet(func.hex2ip(e[3]), func.hex2ip(e[4]))
		print(" %-8s %17s %17s %20s %20s" % (tunnel_id, remote_ip, remote_link, local_subnet, remote_subnet))



def print_table(fwtab, formatted = False):
	print("")
	cmd = "fw tab -t " + fwtab + " -u"
	if formatted:
		cmd = cmd + " -f"
	print("Executing command:")
	print(cmd)
	print("")
	os.system(cmd)
	print("")


def clear_table_input(fwtab):
	print("Please enter common ip addresses. If you wish to disable filter, just")
	print("leave those fields empty.")
	print("")
	ip_src = input("Enter source ip     : ")
	ip_dst = input("Enter destination ip: ")
	print("")
	if ip_src != "":
		iphex_src = ip2hex(ip_src)
		print("Filter: source = " + ip_src + " (" + iphex_src + ")")
	else:
		iphex_src = ""
	if ip_dst != "":
		iphex_dst = ip2hex(ip_dst)
		print("Filter: destination = " + ip_dst + " (" + iphex_dst + ")")
	else:
		iphex_dst = ""
	clear_table(fwtab, iphex_src, iphex_dst)

def clear_table(fwtab, iphex_src = "", iphex_dst = ""):
	a = input("Should i really CLEAR table? [y/N] ")
	if a.lower() != "y":
		print("Aborting !")
		return False
	out, err = func.execute_command("fw tab -t " + fwtab + " -u | awk 'NR>3 {print $1$2$3$4$5$6}' | sed 's/<//g' | sed 's/>//g' | sed 's/;//g'")
	for line in out:
		delete = False
		conn = line.strip('\n')
		fields = conn.split(',')
		if len(fields) < 5:
			continue
		if iphex_src != "":
			if iphex_src == fields[1]:
				delete = True
		if iphex_dst != "":
			if iphex_dst == fields[3]:
				delete = True
		if iphex_src == "" and iphex_dst == "":
			delete = True
		if delete:
			print("-> Deleting Connection: " + conn)
			os.system("fw tab -t " + fwtab + " -x -e " + conn + " >/dev/null 2>&1")



def clusterxl_status():
	cmd = "cphaprob state ; cphaprob -a if"
	print("")
	print("Executing:")
	print(cmd)
	print("")
	os.system(cmd)



def change_f2f_stats(worker_id, val):
	os.system("echo " + str(val) + " > /proc/cpkstats/fw_worker_" + str(worker_id) + "_stats")


def getall_f2f_worker():
	workers = []
	for filename in os.listdir("/proc/cpkstats/"):
		if "fw_worker_" in filename and "_stats" in filename and not "raw" in filename:
			workers.append(int(filename.replace("fw_worker_","").replace("_stats","")))
	return workers


def select_f2f_stats():
	print("")
	all = getall_f2f_worker()
	w = input("Enter fw_worker id for statistics: ")
	print("")
	error = False
	try:
		w_i = int(w)
		if not w_i in all:
			error = True
	except:
		error = True
	if error:
		print("fw_worker id is invalid !")
		print("valid ids are:")
		print(all)
		return
	print_f2f_stats(w_i)
	


def print_f2f_stats(worker_id):
	# enabling worker debug for f2f
	if worker_id < 0:
		# print all workers
		workers = getall_f2f_worker()
		for worker in workers:
			print("Enabling Debug on fw_worker[" + str(worker) + "] ...")
			change_f2f_stats(worker, 1)
	else:
		print("Single fw_worker[" + str(worker_id) + "] selected...")
		change_f2f_stats(worker_id, 1)
		workers = []
		workers.append(worker_id)

	output = ""
	stats = []
	stats_sort = []
	CURSOR_UP_ONE = '\x1b[1A'
	ERASE_LINE = '\x1b[2K'

	print(" ")
	print("Entering Loop, press CTRL+C to exit.")
	print("Refreshing statistics every second..")
	print(" ")
	print(" ")
	# Field begins:
        #       2         12       20              35             49
	print(" Worker     Type     Cycles          Time ago       Data")
	print(" ============================================================================================================")

	try:
		while True:
			for n in stats_sort:
				sys.stdout.write(CURSOR_UP_ONE)
				sys.stdout.write(ERASE_LINE)
			output = ""
			stats.clear()
			for worker in workers:	
				for line in func.tail_and_head('/proc/cpkstats/fw_worker_' + str(worker) + '_stats', 18, 16):
					raw = str(line).replace('\t','').replace('\n','')
					raw = raw.split()
					s_worker  = worker
					s_type    = raw[0].replace(':','')
					s_cycles  = int(raw[1])
					s_timeago = int(raw[2])
					raw = raw[3:]
					s_data    = ' '.join(raw)
					new = { 'worker': s_worker, 'type': s_type, 'cycles': s_cycles, 'timeago': s_timeago, 'data': s_data }
					stats.append(new)
			stats_sort = sorted(stats, key=lambda k: k['cycles'], reverse=True)
			stats_sort = stats_sort[:15]
			for s in stats_sort:
				output += " " + func.str_pad(s["worker"], 2) + 10*" " + s["type"] + 5*" " + func.str_pad(s["cycles"], 10, padLeft = True) + 6*" " + func.str_pad(s["timeago"], 3, padLeft = True) + 12*" " + s["data"] + "\n"
			sys.stdout.write(output)
			sys.stdout.flush()
			time.sleep(1)

	except KeyboardInterrupt:
		pass

	print(" ")
	print(" ")

	# disabling worker debug for f2f
	for worker in workers:
		print("Disabling Debug on fw_worker[" + str(worker) + "] ...")
		change_f2f_stats(worker, 0)
