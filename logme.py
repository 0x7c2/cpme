#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

import time
import os
import sys
import func
from operator import itemgetter
import inspect

version = "v0.22"
width = 80
loader_val = 0
loader_char = ["-", "\\", "|", "/", "#"]

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def tr(corner = False, txtLeft = "", txtRight = ""):
        global width
        fillme = width-4
        fillme = fillme - len(txtLeft)
        fillme = fillme - len(txtRight)
        if corner:
                print("+-" + txtLeft + fillme*"-" + txtRight + "-+")
        else:
                print(width*"-")

def menu_title(title):
	global width
	fillme = width-2
	tr(True, version, "by-0x7c2")
	filltxt1 = int((fillme-len(title))/2)
	filltxt2 = fillme-filltxt1-len(title)
	print("|" + filltxt1*" " + title + filltxt2*" " + "|")
	tr(True)

def menu_footer():
	tr(True)

def menu_entry(title):
	global width
	fillme = width-3
	filltxt = fillme-len(title)
	print("| " + title + filltxt*" " + "|")

def results(res):
	global width
	size = width-4
	new_res = results_remove_duplicates(res)
	for entry in new_res:
		value = ""
		vallen = 0
		if entry[1] != "":
			vallen = len(entry[1])
			value = bcolors.OKBLUE + str(entry[1]) + bcolors.ENDC
		fillme = size-len(entry[0])-6-vallen
		state = str(entry[2])
		if state == "PASS":
			state = bcolors.OKGREEN + state + bcolors.ENDC
		if state == "WARN":
			state = bcolors.WARNING + state + bcolors.ENDC
		if state == "FAIL":
			state = bcolors.FAIL + state + bcolors.ENDC
		print("|-> " + str(entry[0]) + " " + fillme*"." + value + " " + state)


def results_remove_duplicates(res):
	new_res = []
	for item in res:
		if item not in new_res:
			new_res.append(item)
	return new_res


def html_category_descrpition(cat = ""):
	categories = {}
	categories["Firewall"] 		= "Specific things about FireWall-1 Product"
	categories["GAiA"]		= "Operating System related stuff"
	categories["CoreXL"]		= "CoreXL statistics, loadbalancing traffic over all configured cpus"
	categories["Deployment Agent"]	= "Specific things from deployment agent, for example available updates"
	categories["Filesystem"]	= "Local filesystem on this physical box"
	categories["ClusterXL"]		= "Cluster related information"
	categories["CPU"]		= "CPU usage, data obtained from cpview history"
	categories["Kernel"]		= "Firewall kernel related settings"
	categories["Licensing"]		= "Most complex topic, check point licensing ;-)"
	categories["Log Files"]		= "Try to find errors or any other warning in the log files"
	categories["Memory"]		= "Memory usage and failed allocations, data obtained from cpview history"
	categories["SecureXL"]		= "SecureXL configuration and statistics"
	# ...
	if cat == "":
		return categories
	else:
		return categories[cat]


def html_table_header(cat):
	html  = ""
	html += "<a name='" + cat + "'></a> \n"
	html += "<div class='container'> \n"
	html += "<h2>" + cat + "</h2> \n"
	if cat in html_category_descrpition():
		html += "<p>" + html_category_descrpition(cat) + "</p> \n"
	html += "<table class='table'> \n"
	html += " <thead> \n"
	html += "  <tr class='d-flex'> \n"
	html += "   <th class='col-7'>Topic</th> \n"
	html += "   <th class='col-3'>Detail</th> \n"
	html += "   <th class='col-2'>State</th> \n"
	html += "  </tr> \n"
	html += " </thead> \n"
	html += " <tbody> \n"
	return html

def html_table_footer():
	html  = ""
	html += " </tbody> \n"
	html += "</table> \n"
	html += "</div> \n"
	return html

def html_table_item(topic, detail, state):
	formatme = " class='d-flex table-success "+state+"'"
	if state == "WARN":
		formatme = " class='d-flex table-warning "+state+"'"
	if state == "FAIL":
		formatme = " class='d-flex table-danger "+state+"'"
	if state == "INFO":
		formatme = " class='d-flex table-info "+state+"'"
	html  = ""
	html += "  <tr" + formatme + "> \n"
	html += "   <td class='col-7'>" + topic + "</td> \n"
	html += "   <td class='col-3'>" + detail + "</td> \n"
	html += "   <td class='col-2'>" + state + "</td> \n"
	html += "  </tr> \n"
	return html


def html_table_out(res):
	html = ""
	last = ""
	sort_res = sorted(res, key=itemgetter(3))
	for entry in sort_res:
		category = entry[3]
		topic    = entry[0]
		detail   = entry[1]
		state    = entry[2]
		if last != category:
			if last != "":
				html += html_table_footer()
			html += html_table_header(category)
			last = category
		html += html_table_item(topic, detail, state)
	html += html_table_footer()
	return html


def html_badge_build(class_array, count, state):
	(c, txt) = class_array
	html  = ""
	# html += "  <input type='checkbox' class='form-check-input' id='cbox_"+state+"' onclick='toggleme(\""+state+"\")' checked> \n"
	# html += "  <label class='form-check-label' for='cbox_"+state+"'> \n"
	# html += "   <span class='badge badge-" + c + "'>" + str(count) + " " + txt + "</span> \n"
	# html += "  </label> \n"
	html += "  <label for='cbox_"+state+"' class='btn btn-"+c+"'>" + str(count) + " " + txt
	html += "   <input type='checkbox' id='cbox_"+state+"' class='badgebox' onclick='toggleme(\""+state+"\")' checked>"
	html += "   <span class='badge'>&check;</span> "
	html += "  </label> \n"
	return html

def html_badge_build_class(state):
	if state == "PASS":
		return ("success", "Passed")
	if state == "WARN":
		return ("warning", "Warning(s)")
	if state == "INFO":
		return ("info", "Information(s)")
	if state == "FAIL":
		return ("danger", "Failed")
	return ("secondary", "Unknown")


def html_badge_out(res):
	html = ""
	last = ""
	count = 0
	sort_res = sorted(res, key=itemgetter(2))
	for entry in sort_res:
		state = entry[2]
		if last != state:
			if last != "":
				html += html_badge_build(html_badge_build_class(last), count, last)
			last = state
			count = 0
		count = count + 1
	html += html_badge_build(html_badge_build_class(last), count, last)
	return html


def html_build_nav(res):
	last = ""
	cats = []
	sort_res = sorted(res, key=itemgetter(3))
	for entry in sort_res:
		if last != entry[3]:
			cats.append(entry[3])
			last = entry[3]
	html  = ""
	html += "<nav class='navbar navbar-expand-xl navbar-light bg-light fixed-top'> \n"
	html += " <a class='navbar-brand' href='#'>CPme - Report</a> \n"
	html += " <button class='navbar-toggler' type='button' data-toggle='collapse' data-target='#navbarSupportedContent' aria-controls='navbarSupportedContent' aria-expanded='false' aria-label='Toggle navigation'> \n"
	html += "  <span class='navbar-toggler-icon'></span> \n"
	html += " </button> \n"
	html += " <div class='collapse navbar-collapse' id='navbarSupportedContent'> \n"
	html += "  <ul class='nav navbar-nav'> \n"
	for e in cats:
		html += "   <li class='nav-item'><a class='nav-link' href='#" + e + "'>" + e + "</a></li> \n"
	html += "  </ul> \n"
	html += " </div> \n"
	html += "</nav> \n"
	return html


def html_build_footer(res):
	html  = ""
	html += "<nav class='navbar fixed-bottom navbar-expand-sm navbar-light bg-light navbar-print' style='padding: 0px;'> \n"
	html += "&nbsp;"
	html += "</nav> \n"
	return html


def html_intro_item(title, val):
	html  = ""
	html += " <div class='row'> \n"
	html += "  <div class='col-2'><b>"+title+"</b></div> \n"
	html += "  <div class='col-10'>"+val+"</div> \n"
	html += " </div> \n"
	return html

def html_intro_item_cli(title, cmd):
	out, err = func.execute_command(cmd)
	return html_intro_item(title, out.read().strip('\n'))

def html_intro(res):
	html  = ""
	html += "<div class='container jumbotron'> \n"
	html += html_intro_item_cli("Hostname", "hostname")
	html += html_intro_item_cli("CP Version", "fw ver")
	html += html_intro_item_cli("Kernel", "uname -a")
	if func.isFirewall():
		html += html_intro_item_cli("Policy", "fw stat | grep -v 'POLICY' | awk '{ print $2 }'")
		html += html_intro_item_cli("Blades", "enabled_blades")
	html += html_intro_item_cli("Uptime", "uptime")
	html += html_intro_item("CPme Version", version + " (by Simon Brecht, https://github.com/0x7c2/cpme/)")
	html += html_intro_item_cli("Created", "date")
	html += html_intro_item("Status", html_badge_out(res))
	html += "</div> \n"
	return html

def html_out(res):
	new_res = results_remove_duplicates(res)
	html  = ""
	html += "<!DOCTYPE html> \n"
	html += "<html lang='en'> \n"
	html += "<head> \n"
	html += " <title>CPme - HTML Report</title> \n"
	html += " <meta charset='utf-8'> \n"
	html += " <meta name='viewport' content='width=device-width, initial-scale=1'> \n"
	html += " <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css'> \n"
	html += " <script src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js'></script> \n"
	html += " <script src='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.0/js/bootstrap.min.js'></script> \n"
	html += " <style> \n"
	html += "  @media print { \n"
	html += "   body { \n"
	html += "     padding-bottom: 70px; \n"
	html += "   } \n"
	html += "   .navbar-print { \n"
	html += "     display: block; \n"
	html += "     border-width:0 !important; \n"
	html += "   } \n"
	html += "  } \n"
	html += "  .badgebox \n"
	html += "  { \n"
	html += "    opacity: 0; \n"
	html += "  } \n"
	html += "  .badgebox + .badge \n"
	html += "  { \n"
	html += "    text-indent: -999999px; \n"
	html += "    width: 27px; \n"
	html += "  } \n"
	html += "  .badgebox:focus + .badge \n"
	html += "  { \n"
	html += "    box-shadow: inset 0px 0px 5px; \n"
	html += "  } \n"
	html += "  .badgebox:checked + .badge \n"
	html += "  { \n"
	html += "    text-indent: 0; \n"
	html += "  } \n"
	html += " </style> \n"
	html += " <script type='text/javascript'> \n"
	html += "  function toggleme(className) { \n"
	html += "   elements = document.getElementsByClassName(className); \n"
	html += "   for (var i = 0; i < elements.length; i++) { \n"
	html += "    if (document.getElementById('cbox_'+className).checked == false) { \n"
	html += "     elements[i].classList.remove('d-flex'); \n"
	html += "     elements[i].style.display = 'none'; \n"
	html += "    } else { \n"
	html += "     elements[i].classList.add('d-flex'); \n"
	html += "     elements[i].style.display = 'inline'; \n"
	html += "    } \n"
	html += "   } \n"
	html += "  } \n"
	html += " </script> \n"
	html += "</head> \n"
	html += "<body style='padding-top: 65px; padding-bottom: 70px; font-size: 14px;'> \n"
	html += html_build_nav(new_res)
	html += html_intro(new_res)
	html += html_table_out(new_res)
	html += html_build_footer(new_res)
	html += "</body> \n"
	html += "</html> \n"
	return html


def info():
	global version
	print("CPme - CheckPoint Report/Analytic Tool, " + version + " (by S.Brecht, https://github.com/0x7c2/cpme/)")


def info_version():
	readme = open('README.md', 'r')
	lines = readme.readlines()
	output = False
	for lineraw in lines:
		line = lineraw.strip('\n').replace('`','')
		if line == "## History":
			output = True
		if line == "## Donation":
			output = False
		if output:
			if "##" in line:
				tmp = line.replace('## ', '')
				print("+" + (len(tmp)+2)*"-" + "+")
				print("| " + tmp + " |")
				print("+" + (len(tmp)+2)*"-" + "+")
			else:
				print(line)


def usage():
	print("")
	print("usage: cpme              Run interactive mode")
	print("   or: cpme [arguments]  With arguments, run non interactive mode")
	print("")
	print("Arguments:")
	print("  --html                 Run all checks and create HTML report")
	print("  --cli                  Run all checks and create CLI report")
	print("  --update               Try to initiate self-update for CPme")
	print("  --version              Print version and other information")
	print("")



def loader(txt = "Collecting data..."):
	global loader_val
	global loader_char
	loader_len = len(loader_char)
	if loader_val >= loader_len:
		loader_val = 0
	parentname = inspect.stack()[1][3]
	parentname = parentname[:25]
	while len(parentname) < 25:
		parentname += " "
	print("[" + parentname + "] " + txt + " " + loader_char[loader_val], end='\r')
	loader_val = loader_val + 1


def banner():
        os.system('clear')
        print("")
        print("")
        print(7*" " + 13*"#")
        print(7*" " + 13*"#")
        print(7*" " +  2*"#")
        print(7*" " +  2*"#")
        print(7*" " +  2*"#")
        print(7*" " +  2*"#")
        print(7*" " + 13*"#")
        print(7*" " + 13*"#")
        print("")
        print("")
        time.sleep(0.1)
        os.system('clear')
        print("")
        print("")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#" + 8*" " + 2*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#")
        print("")
        print("")
        time.sleep(0.1)
        os.system('clear')
        print("")
        print("")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#" + 8*" " + 2*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#" + 13*" " + 10*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#" + 13*" " + 10*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#")
        print("")
        print("")
        time.sleep(0.1)
        os.system('clear') 
        print("")
        print("")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " + 13*"#" +  2*" " + 12*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#" + 8*" " + 2*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#" + 13*" " + 10*"#" + 2*" " + 8*"#")
        print(7*" " +  2*"#" + 13*" " + 12*"#" + 13*" " + 10*"#" + 2*" " + 2*"#" + 4*" " + 2*"#")
        print(7*" " +  2*"#" + 13*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 8*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#")
        print(7*" " + 13*"#" +  2*" " +  2*"#" + 23*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 2*"#" + 2*" " + 8*"#")
        print("")
        print("")
        time.sleep(0.5)
        i = 1
        while i<width:
                print(i*"=", end='\r')
                time.sleep(0.01)
                i = i + 1
        print("")
        time.sleep(2)
        os.system('clear')
