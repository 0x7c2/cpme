#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

import hashlib
import os
import logme
import func


menu_text = "GAiA Operating System"
menu_item = [	["Run all checks",			"gaia.check_all(True)"],
		["Check GAiA Proxy Config",		"gaia.gaia_check_proxy(True)"],
		["Connectivity Check to CP",		"gaia.gaia_connectivity_check(True)"],
		["Dynamic Routing Instances",		"gaia.gaia_check_dr_cfg(True)"],
		["Check DHCP Relay Config",		"gaia.gaia_check_dhcp_relay(True)"],
		["Check Deployment Agent Version",	"gaia.gaia_check_cpuse_agent_version(True)"],
		["Check Deployment Agent Pending Reboot","gaia.gaia_check_cpuse_agent_pending_reboot(True)"],
		["Check Packages available for install", "gaia.gaia_check_cpuse_agent_available(True)"],
		["Check Scheduled Backup Config",	"gaia.gaia_check_backup_scheduled(True)"],
		["Check GAiA Snapshots",		"gaia.gaia_check_snapshots(True)"]]

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

def print_results():
	global results
	logme.results(results)
	results = []


def gaia_get_value(str, getSingleValue = True):
	logme.loader()
	retVal = False
	parent = str.split(':')
	parent = parent[0]
	out, err = func.execute_command("dbget -rv " + parent)
	for o in out:
		if str in o:
			if not getSingleValue and not retVal:
				retVal = []
			if getSingleValue:
				retVal = o.replace(str, '').strip(' ').strip('\n')
			else:
				retVal.append(o.replace(str, '').strip(' ').strip('\n'))
	return retVal


def gaia_check_backup_scheduled(printRes = False):
	global results
	title = "Check Scheduled Backup Config"
	bkp = gaia_get_value("backup-scheduled")
	if bkp:
		state = "PASS"
		detail = "configured"
	else:
		state = "WARN"
		detail = "not-configured"
	results.append([title, detail, state, "GAiA"])
	if printRes:
		print_results()


def gaia_check_snapshots(printRes = False):
	global results
	title = "Check GAiA Snapshots"
	found = False
	out, err = func.execute_command("lvs | grep -v 'wi-ao'  | tail -n +2")
	for o in out:
		cols = o.split()
		found = True
		name = cols[0].strip(' ').strip('\n')
		vg   = cols[1].strip(' ').strip('\n')
		attr = cols[2].strip(' ').strip('\n')
		size = cols[3].strip(' ').strip('\n')
		detail = vg + " / " + name + " (" + size + ")"
		if "hwdiag" in name or "fcd_GAIA" in name:
			results.append([title, detail, "INFO", "GAiA"])
		else:
			results.append([title, detail, "WARN", "GAiA"])
	if not found:
		results.append([title, "none", "INFO", "GAiA"])
	if printRes:
		print_results()


def gaia_check_cpuse_agent_version(printRes = False):
	global results
	logme.loader()
	detail = "build "
	state = "PASS"
	title = "Check Deployment Agent Version"
	out, err = func.execute_command('cpvinfo $DADIR/bin/DAService | grep -E "Build|Minor"')
	for o in out:
		if detail != "build ":
			detail += ", "
		data = o.split('=')
		detail += data[1].strip('\n').strip(' ')
	logme.loader()
	out, err = func.execute_command('$DADIR/bin/da_cli da_status | grep -c "up to date"')
	data = int(out.read().strip('\n').strip(' '))
	if data < 1:
		state = "FAIL"
		detail += "new version available"
	results.append([title, detail, state, "Deployment Agent"])
	if printRes:
		print_results()

def gaia_check_cpuse_agent_pending_reboot(printRes = False):
	global results
	logme.loader()
	title = "Check Deployment Agent Pending Reboot"
	state = "PASS"
	detail = ""
	out, err = func.execute_command('$DADIR/bin/da_cli is_pending_reboot | grep -c "no reboot"')
	data = int(out.read().strip('\n').strip(' '))
	if data < 1:
		state = "FAIL"
		detail = "reboot pending"
	results.append([title, detail, state, "Deployment Agent"])
	if printRes:
		print_results()


def gaia_check_cpuse_agent_available(printRes = False):
	global results
	logme.loader()
	title = "Check Packages available for install"
	state = "PASS"
	detail = ""
	out, err = func.execute_command('$DADIR/bin/da_cli packages_info status=available | grep filename')
	for o in out:
		data = o.split(':')
		pkg = data[1].strip('\n').strip(' ').replace('"','').replace(',','')
		if "BLINK" not in pkg.upper() and "FRESH" not in pkg.upper():
			state = "WARN"
			detail = pkg
			results.append([title, detail, state, "Deployment Agent"])
	if state == "PASS":
		results.append([title, "up-to-date", state, "Deployment Agent"])
	if printRes:
		print_results()



def gaia_check_proxy(printRes = False):
	global results
	logme.loader()
	title = "Check GAiA Proxy Config"
	proxy_addr = gaia_get_value('proxy:ip-address')
	proxy_port = gaia_get_value('proxy:port')
	detail = "direct"
	state = "PASS"
	if proxy_addr:
		state = "INFO"
		detail = proxy_addr + ":" + proxy_port
	results.append([title, detail, state, "GAiA"])
	if printRes:
		print_results()			


def gaia_check_dhcp_relay(printRes = False):
	global results
	logme.loader()
	gaia_path = "routed:instance:default:bootpgw:interface"
	title = "Check DHCP-Relay Config"
	cfg = gaia_get_value(gaia_path, False)
	found = False
	if cfg:
		for c in cfg:
			if not ":" in c[1:]:
				data = c[1:].split(' ')
				relay_if = data[0]
				relay_vip = gaia_get_value(gaia_path + ":" + relay_if + ":primary")
				relay_srv = gaia_get_value(gaia_path + ":" + relay_if + ":relayto:host", False)
				prefix = ""
				state = "INFO"
				if relay_vip:
					prefix = "VIP: " + relay_vip + ", "
				else:
					if func.isCluster:
						prefix = "missing VIP! "
						state = "WARN"
				for r in relay_srv:
					results.append(["DHCP-Relay [" + relay_if + "]", prefix + "Server: " + r[1:].split(' ')[0].strip('\n'), state, "GAiA"])
					found = True
	if not found:
		results.append([title, "not active", "PASS", "GAiA"])
	if printRes:
		print_results()


def gaia_check_dr_cfg(printRes = False):
	global results
	logme.loader()
	title = "Dynamic Routing Instances"
	protocols = [ "ospf2", "ospf3", "pim", "bgp" ]
	found = False
	for p in protocols:
		ret = gaia_get_value('routed:instance:default:' + p, False)
		if ret and ("interface" in str(ret) or "peeras" in str(ret)):
			results.append([title + " [" + p.upper() + "]", "enabled", "INFO", "GAiA"])
			found = True
	if not found:
		results.append([title, "not configured", "PASS", "GAiA"])
	if printRes:
		print_results()



def gaia_get_curl_cli_proxy_str():
	retVal = ""
	proxy_addr = gaia_get_value('proxy:ip-address')
	proxy_port = gaia_get_value('proxy:port')
	if proxy_addr:
		retVal = "--proxy http://" + proxy_addr + ":" + proxy_port + " "
	return retVal


def gaia_connectivity_check(printRes = False):
	global results
	logme.loader()
	urls = []
	title = "GAiA Connectivity"
	urls.append(['http://cws.checkpoint.com/APPI/SystemStatus/type/short','Social Media Widget Detection'])
	urls.append(['http://cws.checkpoint.com/URLF/SystemStatus/type/short','URL Filtering Cloud Categorization'])
	urls.append(['http://cws.checkpoint.com/AntiVirus/SystemStatus/type/short','Virus Detection'])
	urls.append(['http://cws.checkpoint.com/Malware/SystemStatus/type/short','Bot Detection'])
	urls.append(['https://updates.checkpoint.com/','IPS Updates'])
	urls.append(['http://dl3.checkpoint.com','Download Service Updates '])
	urls.append(['https://usercenter.checkpoint.com/usercenter/services/ProductCoverageService','Contract Entitlement '])
	urls.append(['https://usercenter.checkpoint.com/usercenter/services/BladesManagerService','Software Blades Manager Service'])
	urls.append(['http://resolver1.chkp.ctmail.com','Suspicious Mail Outbreaks'])
	urls.append(['http://download.ctmail.com','Anti-Spam'])
	urls.append(['http://te.checkpoint.com','Threat Emulatin'])
	urls.append(['http://teadv.checkpoint.com','Threat Emulation Advanced'])
	urls.append(['http://kav8.zonealarm.com/version.txt','Deep inspection'])
	urls.append(['http://kav8.checkpoint.com','Traditional Anti-Virus'])
	urls.append(['http://avupdates.checkpoint.com/UrlList.txt','Traditional Anti-Virus, Legacy URL Filtering'])
	urls.append(['http://sigcheck.checkpoint.com/Siglist2.txt','Download of signature updates'])
	urls.append(['http://secureupdates.checkpoint.com','Manage Security Gateways'])
	urls.append(['https://productcoverage.checkpoint.com/ProductCoverageService','Makes sure the machines contracts are up-to-date'])
	urls.append(['https://sc1.checkpoint.com/sc/images/checkmark.gif','Download of icons and screenshots from Check Point media storage servers'])
	urls.append(['https://sc1.checkpoint.com/za/images/facetime/large_png/60342479_lrg.png','Download of icons and screenshots from Check Point media storage servers'])
	urls.append(['https://sc1.checkpoint.com/za/images/facetime/large_png/60096017_lrg.png','Download of icons and screenshots from Check Point media storage servers'])
	urls.append(['https://push.checkpoint.com','Push Notifications '])
	urls.append(['http://downloads.checkpoint.com','Download of Endpoint Compliance Updates'])

	proxy = gaia_get_curl_cli_proxy_str()

	for url in urls:
		logme.loader()
		out, err = func.execute_command('curl_cli -Lisk ' + proxy + url[0] + ' | head -n1')
		data = out.read().strip('\n').strip(' ')
		if "OK" in data or "Found" in data or "Moved" in data or "Connection established" in data:
			state = "PASS"
			detail = ""
		else:
			state = "FAIL"
			detail = data
		results.append([title + " [" + url[1][0:34] + "...]", detail, state, "GAiA"])

	if printRes:
		print_results()



def check_all(printRes = False):
	gaia_check_proxy()
	gaia_connectivity_check()
	gaia_check_dr_cfg()
	gaia_check_dhcp_relay()
	gaia_check_cpuse_agent_version()
	gaia_check_cpuse_agent_pending_reboot()
	gaia_check_cpuse_agent_available()
	gaia_check_backup_scheduled()
	gaia_check_snapshots()
	if printRes:
		print_results()
