#!/opt/CPsuite-R80.40/fw1/Python/bin/python3

#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

print("")
print("** CPme is starting, wait a second...")
print("")

import os, sys, sqlite3
from array import array
from subprocess import Popen, PIPE

import logme
import func
import health
import kernel
import files
import performance
import tuning
import troubleshooting
import mgmt
import rulebase
import gaia

menu_cur = "main"
menu_wait = True
menu_text = {}
menu_item = {}
menu_exec = {}

menu_text["main"] = "Main Menu"
menu_item["main"] = [["GAiA Operating System",	"menu_set('gaia')"],
		["Health Analysis", 	"menu_set('health')"],
		["Files Analysis",	"menu_set('files')"],
		["Performance Analysis","menu_set('performance')"]]

if func.isFirewall():
	menu_item["main"].append(["Kernel Parameters",	"menu_set('kernel')"])
	menu_item["main"].append(["Tuning Options",	"menu_set('tuning')"])
	menu_item["main"].append(["Troubleshooting Options", "menu_set('troubleshooting')"])

if func.isManagement():
	menu_item["main"].append(["Management Options",	"menu_set('mgmt')"])
	menu_item["main"].append(["Manage/Optimize Rulebase", "menu_set('rulebase')"])

menu_item["main"].append(["Create HTML Report", "func.make_report_html()"])

menu_text["gaia"] = gaia.add_text()
menu_item["gaia"] = gaia.add_item()

menu_text["health"] = health.add_text()
menu_item["health"] = health.add_item()

menu_text["files"] = files.add_text()
menu_item["files"] = files.add_item()

menu_text["performance"] = performance.add_text()
menu_item["performance"] = performance.add_item()

menu_text["kernel"] = kernel.add_text()
menu_item["kernel"] = kernel.add_item()

menu_text["tuning"] = tuning.add_text()
menu_item["tuning"] = tuning.add_item()

menu_text["troubleshooting"] = troubleshooting.add_text()
menu_item["troubleshooting"] = troubleshooting.add_item()

menu_text["mgmt"] = mgmt.add_text()
menu_item["mgmt"] = mgmt.add_item()

menu_text["rulebase"] = rulebase.add_text()
menu_item["rulebase"] = rulebase.add_item()

def menu_set(pos):
	global menu_cur
	global menu_wait
	menu_wait = False
	menu_cur = pos

def menu_display(topic):
	global menu_cur
	global menu_wait
	menu_wait = True
	os.system('clear')
	print(" ")
	logme.menu_title(menu_text[topic])
	counter = 0
	for entry in menu_item[topic]:
		counter = counter + 1
		logme.menu_entry(str(counter) + ". " + str(entry[0]))
	logme.menu_entry("0. Exit from Script")
	logme.menu_footer()
	try:
		choice = input("Enter your choice [0-" + str(counter) + "]: ")
		try:
			choice_num = int(choice)
		except:
			choice_num = 999999
		if choice_num == 0:
			print(" ")
			sys.exit()
		if choice_num > -1 and choice_num < (counter+1):
			exec_menu = menu_item[topic][choice_num-1][1]
			print(" ")
			eval(exec_menu)
		else:
			print("Wrong menu selection...")
	except EOFError:
		pass


isFirewall   = bool(func.get_cpregistry("FW","ProdActive"))
isManagement = bool(func.get_cpregistry("MGMT", "ProdActive"))

if len(sys.argv) < 2:
	logme.banner()
	loop = True
	while loop:
		menu_display(menu_cur)
		if menu_wait:
			print(" ")
			print(" ")
			b = input("Press Return to continue....")

else:
	if sys.argv[1] == "--html":
		# printout html report
		logme.info()
		func.make_report_html()
	elif sys.argv[1] == "--cli":
		# printout cli report
		logme.info()
		func.make_report_cli()
	else:
		logme.usage()
