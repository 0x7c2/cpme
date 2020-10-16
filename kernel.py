#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE
import logme
import func

menu_text = "Kernel Parameters"
menu_item = [	["Search FIREWALL kernel parameters",		"kernel.search_kernel(True, 'fw')"],
		["Search SIM kernel paramaters",                "kernel.search_kernel(True, 'sim')"],
		["Search Kernel Tables",			"kernel.search_table(True)"],
		["Print all FIREWALL kernel parameters", 	"kernel.print_kernel(True, 'fw')"],
		["Print all SIM kernel parameters",		"kernel.print_kernel(True, 'sim')"],
		["Print all Kernel Tables",			"kernel.print_table(True)"],
                ["Back to Main Menu",	 			"menu_set('main')"]]

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

def search_table(printRes):
	s = input("Enter search string: ")
	print_table(printRes, s)

def print_table(printRes, search = ""):
	global results
	title = "Kernel table"
	if search != "":
		search = "| grep '"+search+"'"
	logme.loader()
	out, err = func.execute_command('fw tab | grep "\-\-\-\-\-\-\-\-" | sed "s/\-\-\-\-\-\-\-\-//g" | sort '+search)
	for line in out:
		logme.loader()
		data = line.strip('\n')
		results.append([title + " ("+data+")", "", "INFO"])
	if printRes:
		print_results()


def search_kernel(printRes, ktype):
	s = input("Enter search string: ")
	print_kernel(printRes, ktype, s)

def print_kernel(printRes = False, ktype = "fw", search = "", vorgabe = []):
	global results
	title = "Kernel/"+ktype
	if ktype == "fw":
		ktxt = "$FWDIR/boot/modules/fw_kern*.o"
	else:
		ktxt = "$PPKDIR/boot/modules/sim_kern*.o"
	if search == "":
		out, err = func.execute_command('modinfo -p ' + ktxt + ' | sort -u | grep int | cut -d ":" -f1 | xargs -n1 fw ctl get int')
	elif len(vorgabe) > 0:
		sStr = ""
		for entry in vorgabe:
			if sStr != "":
				sStr = sStr + "|"
			sStr = sStr + entry[0]
		out, err = func.execute_command('modinfo -p ' + ktxt + ' | sort -u | grep int | cut -d ":" -f1 | grep -E "(' + sStr + ')" | xargs -n1 fw ctl get int')
	else:
		out, err = func.execute_command('modinfo -p ' + ktxt + ' | sort -u | grep int | cut -d ":" -f1 | grep ' + search + ' | xargs -n1 fw ctl get int')
	for line in out:
		logme.loader()
		raw = line.strip('\n').split('=')
		if len(raw) < 2:
			continue
		field = raw[0].strip(' ')
		val = raw[1].strip(' ')
		state = "INFO"
		for entry in vorgabe:
			if entry[0] == field:
				if str(entry[1]) != str(val):
					state = "WARN"
		results.append([title + " (" + str(field) + ")", str(val), str(state), "Kernel"])
	if printRes:
		print_results()

def check_all():
	print_results()


def print_results():
	global results
	logme.results(results)
	results = []
