#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE
import sqlite3
import time
import logme
import files
import func
import kernel

menu_text = "Health Analysis"
menu_item = [   ["Run all checks",              "health.check_all(True)"],
		["Check memory usage",		"health.check_memory(True)"],
		["Check disk space",		"health.check_diskspace(True)"],
		["Check cpu usage",		"health.check_cpu(True)"],
		["Check system crash",		"health.check_crash(True)"],
		["Check system logfiles",	"health.check_log_system(True)"],
		["Check processes",		"health.check_process(True)"],
		["Check NTP and Time",		"health.check_ntp(True)"]]

if func.isFirewall():
	menu_item.append(["Check Firewall Fragments",	"health.check_fw_fragments(True)"])
	menu_item.append(["Check kernel table overflow", "health.check_table_overflow(True)"])
	menu_item.append(["Check Aggressive Aging",	"health.check_fw_aggressive(True)"])
	menu_item.append(["Check memory allocations",    "health.check_failedalloc(True)"])
	menu_item.append(["Check interface statistics",  "health.check_interfaces(True)"])
	menu_item.append(["Check licensing",		"health.check_licensing(True)"])
	menu_item.append(["Check overlapping encdoms",	"health.check_overlap_encdom(True)"])
	menu_item.append(["Check SIC State",             "health.check_sic_state(True)"])
	menu_item.append(["Check firewall mode",	"health.check_fw_mode(True)"])
	menu_item.append(["Check blade update status",	"health.check_blade_update(True)"])
	menu_item.append(["Check CoreXL dispatcher stats",	"health.check_dispatcher(True)"])
	menu_item.append(["Check CoreXL connections",	"health.check_multik_stat(True)"])
	menu_item.append(["Check active Blades",	"health.check_blades(True)"])

if func.isFirewall() and func.isCluster():
	menu_item.append(["Check ClusterXL state",      "health.check_clusterxl_state(True)"])
	menu_item.append(["Check ClusterXL sync stat",	"health.check_clusterxl_sync(True)"])
	menu_item.append(["Check ClusterXL PNotes",	"health.check_clusterxl_pnote(True)"])
	menu_item.append(["Check fwha_version",		"health.check_fwha_version(True)"])
	if func.fwVersion() == "R80.30" or func.fwVersion() == "R80.40":
		menu_item.append(["Check ClusterXL CCP",	"health.check_clusterxl_ccp(True)"])
	if func.fwVersion() == "R80.40":
		menu_item.append(["Check ClusterXL Multiversion", "health.check_clusterxl_release(True)"])

if func.isManagement():
	menu_item.append(["Check Management Status",	"health.check_mgmt_status(True)"])
	menu_item.append(["Check Management API",	"health.check_mgmt_api(True)"])
	menu_item.append(["Check GUI Clients",		"health.check_mgmt_gui(True)"])
	menu_item.append(["Check Database Locks",	"health.check_mgmt_dblock(True)"])
	menu_item.append(["Check Database Verifications","health.check_mgmt_validations(True)"])
	menu_item.append(["Check IPS Update Status",	"health.check_mgmt_updateips(True)"])

if len(func.ipmiInfo())>0:
	menu_item.append(["Check IPMI Sensor Database",	"health.check_ipmi_sensor(True)"])


menu_item.append(["Back to Main Menu", 		"menu_set('main')"])

def add_text():
        return menu_text

def add_item():
        return menu_item

results = []


def get_results(clear = False):
	global results
	res = results
	if clear:
		results = []
	return res


def check_ipmi_sensor(printRes = False):
	global results
	title = "IPMI Sensor"
	for e in func.ipmiInfo():
		sensor = e[0].strip(' ')
		value  = e[1].strip(' ')
		vtype  = e[2].strip(' ')
		sstate = e[3].strip(' ')
		if value != "na" and value != "0x0" and value != "0.000":
			state = "WARN"
			if sstate == "ok":
				state = "PASS"
			if sstate == "na":
				state = "INFO"
			detail = value + " " + vtype
			results.append([title + " [" + sensor + "]", detail, state, "IPMI Sensor"])
	if printRes:
		print_results()



def check_blade_update(printRes = False):
	global results
	title = "Check blade update status"
	stat = [	["URL Filtering",	"urlf", 0],
			["AntiBot",		"antimalware", 0],
			["AntiVirus",		"antimalware", 1],
			["Application Control",	"appi", 0]]
	i = 0
	oldcmd = ""
	while i < len(stat):
		logme.loader()
		newcmd = "cpstat -f update_status " + stat[i][1] + " | grep 'Update status'"
		if oldcmd != newcmd:
			out, err = func.execute_command(newcmd)
			oldcmd = newcmd
			data = out.read().split('\n')
		val = stat[i][2]
		line = data[val].split(':')[1].strip(' ').strip('\n')
		state = "FAIL"
		detail = ""
		if line == "-" or line == "":
			state = "INFO"
			detail = "not active"
		if line == "up-to-date":
			state = "PASS"
			detail = "up-to-date"
		results.append([title + " (" + stat[i][0] + ")", detail, state, "Updates"])
		i = i + 1
	if printRes:
		print_results()

def check_fw_mode(printRes = False):
	global results
	title = "Check firewall mode"
	logme.loader()
	out, err = func.execute_command("lsmod")
	data = out.read()
	state = "FAIL"
	detail = "Could not determine"
	if "fwmod" in data:
		detail = "User Mode"
		state = "WARN"
	if "fw_0" in data:
		detail = "Kernel Mode"
		state = "INFO"
	results.append([title, detail, state, "Firewall"])
	if printRes:
		print_results()


def check_mgmt_gui(printRes = False):
	global results
	title = "Checking GUI Clients"
	logme.loader()
	out, err = func.execute_command("cp_conf client get")
	data = out.read().replace('\n','').strip(' ')
	state = "PASS"
	detail = ""
	if data == "Any":
		state = "WARN"
		detail = "Any"
	results.append([title, detail, state, "Management"])
	if printRes:
		print_results()



def check_blades(printRes = False):
	global results
	title = "Checking active Blades"
	logme.loader()
	out, err = func.execute_command("fw stat -b AMW")
	for line in out:
		logme.loader()
		if ":" in line:
			tmp = line.strip('\n').split(":")
			blade  = tmp[0].strip(' ')
			status = tmp[1].strip(' ')
		else:
			blade = ""
			status = ""
		if ("enable" in status.lower() or "disable" in status.lower()) and "fileapp_ctx_enabled" not in status.lower():
			results.append([title + " (" + blade + ")", status, "INFO", "Blades"])
			if blade == "IPS" and "enable" in status.lower():
				out, err = func.execute_command('cat $FWDIR/state/local/AMW/local.set | grep -A15 malware_profiles | grep ":name" | awk "{print $2}" | tr -d "()"')
				for l in out:
					results.append(["Thread Prevention Policy", l.strip('\n').replace(':name ', ''), "INFO", "Blades"])
	if printRes:
		print_results()
		



def check_dispatcher(printRes = False):
	global results
	title = "Checking Dispatcher statistics"
	logme.loader()
	out, err = func.execute_command("fw ctl pstat -m | grep -i 'fwmultik enqueue fail stats' -A 22 | grep -v 'fail stats:'")
	data = out.read().split('\n')
	error = False
	for d in data:
		tmp = d.split(":")
		if len(tmp) < 2:
			continue
		field = tmp[0].replace('\t','').strip(' ')
		val   = tmp[1].strip(' ')
		if val != '0':
			error = True
			results.append([title + " [" + field + "]", val, "WARN", "CoreXL"])
	if not error:
		results.append([title, "", "PASS", "CoreXL"])
	if printRes:
		print_results()


def check_mgmt_dblock(printRes = False):
	global results
	title = "Checking Database Locks"
	logme.loader()
	out, err = func.execute_command("psql_client cpm postgres -c \"select applicationname,objid,creator,state,numberoflocks,numberofoperations,creationtime,lastmodifytime from worksession where state = 'OPEN' and (numberoflocks != '0' or numberofoperations != '0');\" | tail -n2 | head -n1")
	data = out.read().replace('\n','')
	state = "WARN"
	detail = data
	if data == "(0 rows)":
		state = "PASS"
		detail = ""
	results.append([title, detail, state, "Management"])
	if printRes:
		print_results()

def check_mgmt_validations(printRes = False):
	global results
	title = "Checking validations"
	logme.loader()
	out, err = func.execute_command("mgmt_cli -r true --unsafe true show validations")
	data = out.read().split('\n')
	for d in data:
		if "-total" in d:
			tmp = d.split(":")
			typ = tmp[0]
			val = tmp[1].strip(' ')
			state = "WARN"
			detail = val
			if val == "0":
				state = "PASS"
				detail = ""
			results.append([title + " [" + typ + "]", detail, state, "Management"])
	if printRes:
		print_results()


def check_clusterxl_sync(printRes = False):
	global results
	title = "Checking ClusterXL Sync"
	logme.loader()
	fields = ["Lost updates", "Lost bulk update events", "Oversized updates not sent", "Sent reject notifications", "Received reject notifications"]
	out, err = func.execute_command("cphaprob syncstat")
	data = out.read().split('\n')
	error = False
	for d in data:
		# check sync status
		if "Sync status" in d:
			tmp = d.split(":")
			field = tmp[0].strip(' ')
			val = tmp[1].strip(' ')
			if val == "OK":
				state = "PASS"
				detail = ""
			else:
				state = "FAIL"
				detail = val
			results.append([title + " [" + field + "]", detail, state, "ClusterXL"])
		# check statistics
		for f in fields:
			if f in d:
				val = d.replace(f, '').replace('.','').strip()
				if val != "0":
					state = "WARN"
					detail = val
					error = True
					results.append([title + " [" + f + "]", detail, state, "ClusterXL"])
	if not error:
		results.append([title + " [Statistics]", "", "PASS", "ClusterXL"])
	if printRes:
		print_results()


def check_mgmt_updateips(printRes = False):
	global results
	title = "Checking IPS Update Status"
	logme.loader()
	out, err = func.execute_command("mgmt_cli -r true --unsafe true show-ips-status | grep update-available")
	data = out.read().replace('\n','')
	state = "WARN"
	detail = data
	if data == "update-available: false":
		state = "PASS"
		detail = ""
	results.append([title, detail, state, "Management"])
	if printRes:
		print_results()



def check_mgmt_api(printRes = False):
	global results
	title = "Checking Management API Status"
	logme.loader()
	out, err = func.execute_command("echo y | api status | grep Overall | awk '{ print $4 }'")
	data = out.read().strip('\n').strip(' ')
	state = "FAIL"
	if data == "Started":
		state = "PASS"
	results.append([title, data, state, "Management"])
	if printRes:
		print_results()

def check_mgmt_status(printRes = False):
	global results
	title = "Checking Management Status"
	logme.loader()
	out, err = func.execute_command("cpstat mg | grep Status | awk '{print $2}'")
	data = out.read().strip('\n').strip(' ')
	state = "FAIL"
	if data == "OK":
		state = "PASS"
	results.append([title, data, state, "Management"])
	if printRes:
		print_results()


def check_overlap_encdom(printRes = False):
	global results
	title = "Checking overlapping encryption domain"
	logme.loader()
	out, err = func.execute_command("vpn overlap_encdom | grep -c 'No overlapping encryption domain.'")
	data = out.read().strip('\n')
	state = "FAIL"
	if data == "1":
		state = "PASS"
	results.append([title, "", state, "VPN"])
	if printRes:
		print_results()


def check_ntp(printRes = False):
	global results
	title = "Checking NTP and Time"
	logme.loader()
	out, err = func.execute_command("ntpstat | grep -ic 'synchronised to'")
	data = int(out.read().strip('\n'))
	state = "FAIL"
	if data > 0:
		state = "PASS"
	results.append([title, "", state, "GAiA"])
	if printRes:
		print_results()


def check_licensing(printRes = False):
	global results
	title = "Checking licensing"
	logme.loader()
	out, err = func.execute_command("cpstat os -f licensing | grep '|' | awk 'NR>1 {print $0}'")
	for line in out:
		logme.loader()
		state = "FAIL"
		data = line.strip('\n').split('|')
		blade = data[2].strip(" ")
		status = data[3].strip(" ")
		expiration = data[4].strip(" ")
		active = data[6].strip(" ")
		quota = data[7].strip(" ")
		used = data[8].strip(" ")
		if status == "Not Entitled":
			state = "INFO"
		if status == "Expired" and active == "0":
			state = "WARN"
		if status == "Entitled":
			state = "PASS"
		results.append([title + " (Blade: "+blade+")", status, state, "Licensing"])
	if printRes:
		print_results()


def check_sic_state(printRes = False):
	global results
	title = "Checking SIC State"
	logme.loader()
	out, err = func.execute_command("cp_conf sic state")
	state = "FAIL"
	for line in out:
		logme.loader()
		data = line.strip('\n')
		if data != "":
			detail = data
			if "Trust established" in data:
				state = "PASS"
			results.append([title, detail, state, "Management"])
	if printRes:
		print_results()


def check_fw_fragments(printRes = False):
	global results
	title = "Checking Firewall Fragments"
	logme.loader()
	out, err = func.execute_command("cpstat -f fragments fw | awk 'NR>2 {print $0}'")
	for line in out:
		logme.loader()
		data = line.strip('\n')
		if data != "":
			state = "FAIL"
			d = data.split(":")
			field = d[0].strip(' ')
			value = d[1].strip(' ')
			if int(value) < 100:
				state = "WARN"
			if value == "0":
				state = "PASS"
			results.append([title + " (" + field + ")", value, state, "Firewall"])
	if printRes:
		print_results()


def check_table_overflow(printRes = False):
	global results
	title = "Check kernel table overflow"
	logme.loader()
	tables = ['connections', 'fwx_cache']
	for t in tables:
		logme.loader()
		out, err = func.execute_command("fw tab -t " + t + " | grep limit")
		out = out.read().strip('\n').split(',')
		if out[len(out)-1].strip(' ') == "unlimited":
			results.append([title + " [" + t + "]", "unlimited", "PASS", "Firewall"])
		else:
			logme.loader()
			t_limit = int(out[len(out)-1].replace('limit ','').strip(' '))
			out, err = func.execute_command("fw tab -t " + t + " -s | grep " + t)
			out = out.read().strip('\n').split()
			t_peak = int(out[4])
			t_val  = int(out[3])
			m = False
			if t_peak > (t_limit * 0.9):
				results.append([title + " [" + t + "]", "peak: " + str(t_peak) + "/" + str(t_limit), "WARN", "Firewall"])
				m = True
			if t_val > (t_limit * 0.9):
				results.append([title + " [" + t + "]", "current: " + str(t_val) + "/" + str(t_limit), "FAIL", "Firewall"])
				m = True
			if not m:
				results.append([title + " [" + t + "]", str(t_val) + "/" + str(t_limit), "PASS", "Firewall"])
	if printRes:
		print_results()


def check_failedalloc(printRes = False):
	global results
	title = "Checking failed memory allocations"
	logme.loader()
	out, err = func.execute_command('fw ctl pstat | grep -ioE "[0-9]+ failed" | grep -vc "0 failed"')
	out = out.read().strip('\n')
	state = "FAIL"
	if out == "0":
		state = "PASS"
	results.append([title, "", state, "Memory"])
	if printRes:
		print_results()

def check_log_system(printRes = False):
	global results
	logme.loader()
	FWDIR = func.get_path("FWDIR")
	CPDIR = func.get_path("CPDIR")
	title = "Checking logs"
	#
	#	Format:	[file,			search,		exclude]
	#
	logfiles = [	["/var/log/messages*", "fail|error", "xpand|failover"], 
			[CPDIR + "/log/cpd.elg","fail|error","PROVIDER-1|PA_status"]]

	if func.isFirewall():
		logfiles.append(["/var/log/routed.log","fail|error", "xpand|failover"])
		logfiles.append([FWDIR + "/log/fwd.elg","failed",    "discntd"])

	if func.isManagement():
		logfiles.append([FWDIR + "/log/fwm.elg","failed",    "none"])

	for log in logfiles:
		logme.loader()
		out, err = func.execute_command('cat ' + log[0] + ' | grep -viE "('+log[2]+')" | grep -icE "('+log[1]+')"')
		out = out.read().strip('\n')
		state = "PASS"
		detail = ""
		if out != "0":
			state = "FAIL"
			detail = out + " messages"
		results.append([title + " (" + log[0] + ")", detail, state, "Log Files"])
	if printRes:
		print_results()

def check_crash(printRes = False):
	global results
	title = "Checking crashes"
	logme.loader()
	out, err = func.execute_command("ls -l /var/log/crash")
	for line in out:
		logme.loader()
		tmp = line.strip('\n')
		if 'total 0' == tmp:
			results.append([title + " [/var/log/crash]", "", "PASS", "Process"])
		if 'admin' in tmp:
			f = tmp.split()
			f = f[len(f)-1]
			results.append([title + " [/var/log/crash]", f, "FAIL", "Process"])
	out, err = func.execute_command("ls -l /var/log/dump/usermode")
	for line in out:
		logme.loader()
		tmp = line.strip('\n')
		if 'total 0' == tmp:
			results.append([title + " [/var/log/dump/usermode]", "", "PASS", "Process"])
		if 'admin' in tmp:
			f = tmp.split()
			f = f[len(f)-1]
			results.append([title + " [/var/log/dump/usermode]", f, "FAIL", "Process"])
	if printRes:
		print_results()


def check_interfaces(printRes = False):
	global results
	title = "Checking interface statistics"
	values_rx = ["rx_dropped", "rx_crc_errors", "rx_errors", "rx_fifo_errors", "rx_frame_errors", "rx_length_errors", "rx_missed_errors", "rx_over_errors"]
	values_tx = ["tx_aborted_errors", "tx_carrier_errors", "tx_dropped", "tx_errors", "tx_fifo_errors", "tx_heartbeat_errors", "tx_window_errors"]
	logme.loader()
	out, err = func.execute_command('ls -1 /sys/class/net | grep -vE "(lo|bond|vpn|sit|\.)"')
	for line in out:
		logme.loader()
		interface = line.strip('\n')
		i = 0
		error = False
		while i<len(values_rx):
			logme.loader()
			read, err = func.execute_command('cat /sys/class/net/'+interface+'/statistics/'+values_rx[i])
			val = read.read().strip('\n')
			state = "PASS"
			detail = ""
			if val != "0":
				state = "FAIL"
				detail = val
				error = True
			results.append([title + " (" + interface + " - " + values_rx[i] + ")", detail, state, "Networking"])
			i = i + 1
		if not error:
			for t in values_rx:
				results.pop()
			results.append([title + " (" + interface + " - rx/all" + ")", "", "PASS", "Networking"])
		i = 0
		error = False
		while i<len(values_tx):
			logme.loader()
			read, err = func.execute_command('cat /sys/class/net/'+interface+'/statistics/'+values_tx[i])
			val = read.read().strip('\n')
			state = "PASS"
			detail = ""
			if val != "0":
				state = "FAIL"
				detail = val
				error = True
			results.append([title + " (" + interface + " - " + values_rx[i] + ")", detail, state, "Networking"])
			i = i + 1
		if not error:
			for t in values_tx:
				results.pop()
			results.append([title + " (" + interface + " - tx/all" + ")", "", "PASS", "Networking"])
	if printRes:
		print_results()

def check_diskspace(printRes = False):
	global results
	title = "Checking available disk space"
	logme.loader()
	out, err = func.execute_command("df -h | sed s/\ \ */\;/g | cut -d ';' -f 6,4 | awk 'NR>1 {print $1}'")
	for line in out:
		logme.loader()
		state = "FAIL"
		data = str(line).strip('\n').split(";")
		if len(data) < 2:
			continue
		if "M" in data[0]:
			state = "WARN"
		if "G" in data[0]:
			state = "PASS"
		if data[1] == "/boot" or data[1] == "/dev/shm":
			state = "PASS"
		results.append([title + " (" + data[1] + ")", data[0], state, "Storage"]) 
	if printRes:
		print_results()



def check_cpu(printRes = False):
	global results
	title = "Checking CPU usage"
	logme.loader()
	if func.isFirewall():
		out, err = func.execute_command("fw ctl affinity -l")
		affinity = out.read()
	else:
		affinity = ""
	dbcur = func.execute_sqlite_query("select name_of_cpu,max(cpu_usage) from UM_STAT_UM_CPU_UM_CPU_ORDERED_TABLE group by name_of_cpu;")
	for row in dbcur:
		worker = ""
		nic = ""
		daemon = ""
		logme.loader()
		cpu = row[0]
		for line in affinity.split('\n'):
			logme.loader()
			if "CPU "+str(cpu)+'#' in line +'#':
				if "Kernel" in line:
					if worker != "":
						worker = worker + ", "
					worker = worker + line.split(":")[0].replace("Kernel ", "")
				elif "Daemon" in line:
					daemon = "Daemon(s), "
				else:
					if nic != "":
						nic = nic + ", "
					nic = nic + line.split(":")[0]
		load = str(row[1]).split(".")[0]
		state = "PASS"
		if int(load) > 85 and nic != "":
			state = "FAIL"
		elif int(load) > 85 and nic == "":
			state = "WARN"
		if nic != "":
			nic = nic + ", "
		results.append([title + " (peak - CPU " + str(cpu) + "): " + daemon + nic + worker, load + "%", state, "CPU"])
	dbcur = func.execute_sqlite_query("select name_of_cpu,avg(cpu_usage) from UM_STAT_UM_CPU_UM_CPU_ORDERED_TABLE group by name_of_cpu;")
	for row in dbcur:
		worker = ""
		nic = ""
		daemon = ""
		logme.loader()
		cpu = row[0]
		for line in affinity.split('\n'):
			logme.loader()
			if "CPU "+str(cpu)+'#' in line+'#':
				if "Kernel" in line:
					if worker != "":
						worker = worker + ", "
					worker = worker + line.split(":")[0].replace("Kernel ", "")
				elif "Daemon" in line:
					daemon = "Daemon(s), "
				else:
					if nic != "":
						nic = nic + ", "
					nic = nic + line.split(":")[0]
		load = str(row[1]).split(".")[0]
		state = "PASS"
		if int(load) > 50:
			state = "WARN"
		if int(load) > 50 and nic != "":
			state = "FAIL"
		if int(load) > 85 and worker != "":
			state = "FAIL"
		if nic != "":
			nic = nic + ", "
		results.append([title + " (avg - CPU " + str(cpu) + "): " + daemon + nic + worker, load + "%", state, "CPU"])
	dbcur.close()
	if printRes:
		print_results()


def check_memory(printRes = False):
	global results
	title = "Checking memory usage"
	mem_total = 0
	mem_avg = 0
	mem_peak = 0
	dbcur = func.execute_sqlite_query("select max(real_total) from UM_STAT_UM_MEMORY;")
	for row in dbcur:
		logme.loader()
		mem_total = row[0]

	dbcur = func.execute_sqlite_query("select avg(real_used) from UM_STAT_UM_MEMORY;")
	for row in dbcur:
		logme.loader()
		mem_avg = row[0]

	dbcur = func.execute_sqlite_query("select max(real_used) from UM_STAT_UM_MEMORY;")
	for row in dbcur:
		logme.loader()
		mem_peak = row[0]

	dbcur.close()
	mem_avg_used = int(str(mem_avg/mem_total*100).split(".")[0])
	mem_peak_used = int(str(mem_peak/mem_total*100).split(".")[0])

	state = "PASS"
	if mem_avg_used > 70:
		state = "WARN"
	if mem_avg_used > 90:
		state = "FAIL"
	results.append([title + " (average)", str(mem_avg_used)+"%", state, "Memory"])

	state = "PASS"
	if mem_peak_used > 80:
		state = "WARN"
	results.append([title + " (peak)", str(mem_peak_used)+"%", state, "Memory"])

	out, err = func.execute_command("free -g | grep -i swap | awk '{print $3,$4}'")
	data = out.read().strip('\n').split(" ")
	used = data[0]
	avail = data[1]
	percent = str(int(used) / int(avail) * 100).split(".")[0]
	state = "WARN"
	if percent == "0":
		state = "PASS"
	results.append([title + " (swap)", percent + "%", state, "Memory"])

	if printRes:
		print_results()



def check_process(printRes = False):
	global results
	title = "Checking process"
	out, err = func.execute_command("cpwd_admin list | awk 'NR>1 { print $1,$2,$4 }'")
	for line in out:
		logme.loader()
		data = line.strip('\n').split(" ")
		proc = data[0]
		pid = data[1]
		start = data[2]
		state = "PASS"
		detail = ""
		if start != "1":
			state = "WARN"
			detail = "Process restarted!"
		if not pid.isdigit():
			state = "FAIL"
			detail = "PID missing!"
		results.append([title + " (" + proc + ")", detail, state, "Process"])

	out, err = func.execute_command("ps auxw | grep -E '(Z|defunct)'")
	title = "Checking zombie processes"
	error = False
	for line in out:
		logme.loader()
		if not "grep" in line and not "%CPU" in line:
			data = line.strip('\n').split()
			pid = data[1]
			stat = data[7]
			cmd = data[10]
			state = "FAIL"
			detail = pid + " - " + cmd
			results.append([title, detail, state, "Process"])
			error = True
	if not error:
		results.append([title, "", "PASS", "Process"])
	if printRes:
		print_results()

def check_clusterxl_state(printRes = False):
	global results
	title = "Checking ClusterXL state"
	logme.loader()
	#kernel.print_kernel(False, "fw", "fwha_cluster_instance_id")
	#kernel_clusterid = kernel.get_results(True)
	if func.isCluster():
		# clusterid is set
		out, err = func.execute_command("cphaprob state | head -n 7 | tail -n 2 | sed 's/(local)//g' | awk '{ print $5,$4 }'")
		for line in out:
			data = line.strip('\n').split(" ")
			node = data[0]
			stat = data[1]
			state = "PASS"
			detail = stat
			if stat != "ACTIVE" and stat != "STANDBY":
				state = "FAIL"
				detail = stat
			results.append([title + " ("+node+")", detail, state, "ClusterXL"])
	else:
		results.append([title, "not cluster member!", "PASS", "ClusterXL"])
	if printRes:
		print_results()


def check_clusterxl_ccp(printRes = False):
	global results
	title = "Checking ClusterXL CCP Encryption"
	state = "INFO"
	detail = ""
	out, err = func.execute_command("cphaprob ccp_encrypt")
	for line in out:
		tmp = line.strip('\n').strip(' ')
		if tmp != "":
			detail = tmp
	results.append([title, detail, state, "ClusterXL"])
	if printRes:
		print_results()


def check_clusterxl_release(printRes = False):
	global results
	title = "Checking ClusterXL Multiversion"
	state = "INFO"
	handle = False
	out, err = func.execute_command("cphaprob release")
	for line in out:
		tmp = line.strip('\n')

		if handle and tmp != "":
			a = tmp.split()
			if "Mismatch" in a[len(a)-1]:
				detail = a[len(a)-3] + " " + a[len(a)-2] + " " + a[len(a)-1]
				state = "WARN"
			else:
				detail = a[len(a)-2] + " " + a[len(a)-1]
			id = tmp.replace(detail, '').strip(' ')
			results.append([title + " [ID: "+id+"]", detail, state, "ClusterXL"])

		if "ID" in tmp:
			handle = True
	if printRes:
		print_results()



def check_clusterxl_pnote(printRes = False):
	global results
	title = "Checking ClusterXL PNotes"
	logme.loader()
	out, err = func.execute_command("cpstat ha -f all")
	t = False
	table = ""
	for line in out:
		if line.strip(" ").strip('\n') == "":
			t = False
		if t and "|" in line and not "Descr" in line and not "-----" in line:
			data = line.split('|')
			p_name = data[1].strip(' ')
			p_stat = data[2].strip(' ')
			if p_stat != "OK":
				state = "FAIL"
				detail = p_stat
			else:
				state = "PASS"
				detail = ""
			results.append([title + " [" + p_name + "]", detail, state, "ClusterXL"])
		if "Problem Notification table" in line:
			t = True
	if printRes:
		print_results()


def check_fw_aggressive(printRes = False):
	global results
	title = "Checking Aggressive Aging"
	logme.loader()
	out, err = func.execute_command("fw ctl pstat | grep Aggre")
	data = out.read().strip('\n').strip(' ')
	if data == "Aggressive Aging is enabled, not active":
		state = "PASS"
		detail = ""
	else:
		state = "WARN"
		detail = data
	results.append([title, detail, state, "Firewall"])
	if printRes:
		print_results()


def check_multik_stat(printRes = False):
	global results
	title = "Checking CoreXL connections"
	logme.loader()
	stats = []
	out, err = func.execute_command("fw ctl multik stat")
	for line in out:
		if not "ID" in line and not "-----" in line:
			data = line.split('|')
			id = data[0].strip(' ')
			active = data[1].strip(' ')
			cpu = int(data[2])
			conns = int(data[3])
			peak = int(data[4])
			stats.append([active, cpu, conns, peak])
	state = "PASS"
	detail = ""
	for a in stats:
		for b in stats:
			if int(a[2]) > (int(b[2]) * 1.5) or int(a[3]) > (int(b[3]) * 1.3):
				#print(str(a[2]) + " vs " + str(b[2]))
				state = "WARN"
				detail = "check CoreXL balancing"
	results.append([title, detail, state, "CoreXL"])
	if printRes:
		print_results()


def check_fwha_version(printRes = False):
	global results
	title = "Checking fwha_version"
	logme.loader()
	kernel.print_kernel(False, "fw", "fwha_version")
	results = results + kernel.get_results(True)
	if printRes:
		print_results()



def check_all(printRes = False):
	check_diskspace()
	check_cpu()
	check_memory()
	check_crash()
	check_log_system()
	check_process()
	check_ntp()
	if func.isFirewall():
		check_fw_fragments()
		check_fw_aggressive()
		check_table_overflow()
		check_failedalloc()
		check_interfaces()
		check_sic_state()
		check_overlap_encdom()
		check_licensing()
		check_blade_update()
		check_dispatcher()
		check_multik_stat()
		check_blades()
	if func.isFirewall() and func.isCluster():
		check_clusterxl_state()
		check_clusterxl_sync()
		check_clusterxl_pnote()
		check_fwha_version()
		if func.fwVersion() == "R80.30" or func.fwVersion() == "R80.40":
			check_clusterxl_ccp()
		if func.fwVersion() == "R80.40":
			check_clusterxl_release()
	if func.isManagement():
		check_mgmt_status()
		check_mgmt_api()
		check_mgmt_gui()
		check_mgmt_dblock()
		check_mgmt_validations()
		check_mgmt_updateips()
	if len(func.ipmiInfo())>0:
		check_ipmi_sensor()
	if printRes:
		print_results()

def print_results():
	global results
	logme.results(results)
	results = []
