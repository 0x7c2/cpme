#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE
import logme
import health
import kernel
import files
import func

menu_text = "Performance Analysis"
menu_item = [	["Run all tests",                       "performance.check_all(True, True)"],
		["Check CPU, memory and interfaces",	"performance.check_cpumemif(True)"]]

if func.isFirewall():
	menu_item.append(["Check SecureXL statistics",		"performance.check_securexl(True)"])
	menu_item.append(["Check Modules",			"performance.check_modules(True)"])
	menu_item.append(["Check Multi Queue",			"performance.check_multiq(True)"])
	menu_item.append(["Check Prio Queue",			"performance.check_prioq(True)"])

menu_item.append(["Back to Main Menu",	 		"menu_set('main')"])

results = []

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


def check_all(printRes = False, runAll = False):
	global results
	if runAll:
		check_cpumemif()
	if func.isFirewall():
		check_securexl()
		check_modules()
		check_multiq()
		check_prioq()
	if runAll:
		files.check_all(False, "all")
	results = results + files.get_results(True)
	if printRes:
		print_results()

def check_cpumemif(printRes = False):
	global results
	if func.isFirewall():
		health.check_failedalloc()
	health.check_cpu()
	health.check_memory()
	health.check_interfaces()
	results = health.get_results(True)
	if printRes:
		print_results()


def check_securexl(printRes = False):
	global results
	title = "SecureXL"
	feature = False
	out, err = func.execute_command("fwaccel stat | grep -v Template")
	for line in out:
		state = "FAIL"
		data = line.strip('\n').split('|')
		if len(data) < 4 or data[1].replace(" ","") == "" or data[1].replace(" ","") == "Id":
			continue
		id = data[1].replace(" ", "")
		type = data[2].replace(" ", "")
		status = data[3].replace(" ", "")
		if status != "enabled":
			state = "WARN"
		else:
			state = "PASS"
			feature = True
		results.append([title + " (Instance: " + id + ", Name: " + type + ", Status: " + status + ")", "", state, "SecureXL"])
	if feature:
		out, err = func.execute_command("fwaccel stat| grep Templates | sed s/\ \ */\/g| sed s/Templates//g")
		for line in out:
			state = "FAIL"
			data = line.strip('\n').split(":")
			if len(data) < 2:
				continue
			if "disabled" in data[1]:
				state = "WARN"
			if "enabled" in data[1]:
				state = "PASS"
			results.append([title + " (" + data[0] + " Templates)", data[1], state, "SecureXL"]) 
		out, err = func.execute_command("fwaccel stats -s  | sed 's/  */ /g' | sed 's/\t/ /g'")
		for line in out:
			state = "PASS"
			data = line.strip('\n').split(":")
			if len(data) < 2:
				continue
			field = data[0].strip(' ')
			valraw = data[1].strip(' ').split(" ")
			valnum = valraw[0]
			valper = int(str(valraw[1]).replace('(','').replace(')','').replace('%',''))
			if "Accelerated conns" in field and valper < 30:
				state = "WARN"
			if "Accelerated pkts" in field and valper < 50:
				state = "WARN"
			if "F2Fed" in field and valper > 40:
				state = "FAIL"
			results.append([title + " (" + field + ")", valnum + "(" + str(valper) + "%)", state, "SecureXL"]) 

	if printRes:
		print_results()

def check_modules(printRes = False):
	global results
	modules = [	["fwmultik_dynamic_dispatcher_enabled", 1]]
	kernel.print_kernel(False, "fw", "none", modules)
	results = results + kernel.get_results(True)
	if printRes:
		print_results()

def check_prioq(printRes = False):
	global results
	title = "Prio Queue"
	out, err = func.execute_command("fw ctl multik print_heavy_conn | wc -l")
	counter = out.read().strip('\n')
	modules = [	["fwmultik_prio_queues_enabled", 1]]
	kernel.print_kernel(False, "fw", "none", modules)
	prioqres = kernel.get_results(True)
	if counter != "0":
		if prioqres[0][1] != "1":
			prioqres[0][2] = "FAIL"
			state = "FAIL"
		else:
			state = "INFO"
		results.append([title, "found heavy connections!", state, "Firewall"])
	else:
		if prioqres[0][1] != "1":
			prioqres[0][2] = "WARN"
	results = results + prioqres
	if printRes:
		print_results()

def check_multiq(printRes = False):
	global results
	title = "Multi Queue"
	if func.fwVersion == "R80.40":
		out, err = func.execute_command("mq_mng --show -a")
	else:
		out, err = func.execute_command("cpmq get -a")
	multiq_enabled = "FAIL"
	multiq_possible = "FAIL"
	detail_pos = ""
	detail_en = ""
	out_str = out.read()
	err_str = err.read()
	if "NO MULTIQUEUE SUPPORTED" in out_str.upper() or "NO MULTIQUEUE SUPPORTED" in err_str.upper():
		multiq_possible = "WARN"
		detail_pos = "No IGBx interfaces"
		multiq_enabled = "INFO"
		detail_en = "not possible"
	else:
		add_if = False
		iflist = ""
		iflist_on = ""
		for line in out_str.split('\n'):
			if "Active igb" in line or "Active ixgbe" in line:
				multiq_enabled = "WARN"
				multiq_possible = "INFO"
				add_if = True
			if "[On]" in line:
				multiq_enabled = "PASS"
				multiq_possible = "PASS"
				if iflist_on != "":
					iflist_on = iflist_on + ", "
				iflist_on = iflist_on + line.split(" ")[0]
			if line == "":
				add_if = False
			if add_if and not "ACTIVE" in line.upper():
				if iflist != "":
					iflist = iflist + ", "
				iflist = iflist + line.split(" ")[0]
			detail_pos = iflist
			if iflist_on != "":
				detail_en = iflist_on
			else:
				detail_en = "none"

	results.append([title + " (Available Interfaces)", detail_pos, multiq_possible, "Firewall"])
	results.append([title + " (Enabled Interfaces)", detail_en, multiq_enabled, "Firewall"])

	if printRes:
		print_results()

def print_results():
        global results
        logme.results(results)
        results = []

