#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

import threading
import datetime

import logme
import func
import time
import json
import os

menu_text = "Management Options"
menu_item = [	["Run all checks",				"mgmt.check_all(True)"],
		["Enable API for all IPs",			"mgmt.api_enable(True)"],
		["Restart Management API",			"mgmt.api_restart(True)"],
		["Reset Hit Count",				"mgmt.reset_hitcount(True)"],
		["Check Global Properties",			"mgmt.mgmt_check_firewall_properties(True)"],
		["Check Remote Access - Topology Update",	"mgmt.mgmt_check_vpn_ras_topoupdate(True)"],
		["Check VPN Proposals - Remote Access",		"mgmt.mgmt_check_vpn_prop_ras(True)"],
		["Check VPN Proposals - Star Communities",	"mgmt.mgmt_check_vpn_prop_star(True)"],
		["Check VPN Proposals - Mesh Communities",	"mgmt.mgmt_check_vpn_prop_mesh(True)"],
		["Check Malware Classification Mode",		"mgmt.mgmt_check_malware_classification(True)"],
		["Check ICA / Certificates: SIC",		"mgmt.mgmt_check_ica_certs('SIC', True)"],
		["Check ICA / Certificates: IKE",		"mgmt.mgmt_check_ica_certs('IKE', True)"],
                ["Back to Main Menu",	 			"menu_set('main')"]]

results = []
config = {}
waitforme = False

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

def loader():
	global waitforme
	waitforme = True
	while waitforme:
		logme.loader()
		time.sleep(0.5)


def mgmt_check_ica_certs(kind = 'SIC', printRes = False):
	global results
	logme.loader()
	title = "Checking ICA/"+kind+" Certs"
	certs = {}
	process = True
	out, err = func.execute_command("cpca_client lscert -kind " + kind)
	for line in out:
		logme.loader()
		tmp = line.replace(" = ", "=")
		if "Subject" in tmp:
			tmp_subject = tmp.strip('\n').replace('Subject=','')
		if "Kind" in tmp:
			tmp_line = tmp.strip('\n').split()
			tmp_status = tmp_line[0].replace('Status=','')
			tmp_kind   = tmp_line[1].replace('Kind=','')
			tmp_serial = tmp_line[2].replace('Serial=','')
			if "Revoked" in tmp:
				process = False
			else:
				process = True
			if tmp_subject in certs:
				if "Valid" in tmp_status:
					process = True
				else:
					process = False
		if "Not_Before" in tmp:
			tmp_dates = tmp.strip('\n').split('_')
			tmp_from = tmp_dates[1].replace('Before: ','').replace('Not','').strip(' ')
			tmp_to   = tmp_dates[2].replace('After: ','').strip(' ')
			if process:
				certs[tmp_subject] = { "status": tmp_status, "kind": tmp_kind, "serial": tmp_serial, "valid_from": tmp_from, "valid_to": tmp_to }
	date_w = datetime.datetime.now()
	date_w = date_w + datetime.timedelta(weeks=+12)
	date_f = datetime.datetime.now()
	date_f = date_f + datetime.timedelta(weeks=+4)
	for c in certs:
		detail = certs[c]['valid_to']
		date_a = datetime.datetime.strptime(certs[c]['valid_to'], '%a %b %d %H:%M:%S %Y')
		state = "PASS"
		if date_w > date_a:
			state = "WARN"
		if date_f > date_a:
			state = "FAIL"
		results.append([title + " [" + c[:21] + "]", detail, state, "Certificates"])
	if printRes:
		print_results()



def reset_hitcount(printRes = False):
	# sk111162
	print("")
	s = input("Would you like to continue? [Y/n]: ")
	print("")
	if s.lower() == "y" or s.lower() == "":
		print("[psql_client] Deleting data from hitcount table ...")
		out,err = func.execute_command('echo -e "begin;\ndelete from hitcount;\nend;" | psql_client monitoring postgres', True)
		print("Done!")
		print("")


def api_restart(printRes = False):
	global results
	global waitforme
	title = "Restarting Management API"
	t = threading.Thread(target=loader)
	t.start()
	out, err = func.execute_command("api restart")
	if "API started successfully" in out.read():
		state = "PASS"
	else:
		state = "FAIL"
	results.append([title, "", state])
	waitforme = False
	t.join()
	if printRes:
		print_results()

def mgmt_check_malware_classification(printRes = False):
	global results
	title = "Check Malware Classification Config"
	out, err = func.execute_command('cat /opt/CPsuite-R80.30/fw1/conf/malware_config | grep -A 5 "resource_classification_mode"')
	for line in out:
		if "=" in line:
			tmp = line.strip('\n').strip(' ').split('=')
			state = "WARN"
			service = tmp[0]
			if tmp[1] == "bg":
				action = "background"
			else:
				action = tmp[1]
			if service == "dns" and action == "background":
				state = "PASS"
			if (service == "http" or service == "smb" or service == "smtp" or service == "ftp") and action == "policy":
				state = "PASS"
			results.append([title + " [Service: " + service + "]", action, state, "Thread Prevention"])
	if printRes:
		print_results()


def api_enable(printRes = False):
	global results
	global waitforme
	title = "Enable API for all IPs"
	t = threading.Thread(target=loader)
	t.start()
	out, err = func.execute_command('mgmt_cli -r true set api-settings accepted-api-calls-from "All IP addresses"')
	if "succeeded" in out.read():
		state = "PASS"
	else:
		state = "FAIL"
	results.append([title, "", state])
	waitforme = False
	t.join()
	api_restart()
	if printRes:
		print_results()


def mgmt_fetch_uid_firewall_properties():
	logme.loader()
	out, err = func.execute_command('mgmt_cli show-generic-objects name "firewall_properties" -r true -f json')
	data = json.load(out)
	return data['objects'][0]['uid']

def mgmt_fetch_firewall_properties():
	global config
	logme.loader()
	if not 'firewall_properties' in config:
		uid = mgmt_fetch_uid_firewall_properties()
		logme.loader()
		out, err = func.execute_command('mgmt_cli show generic-object uid "' + uid + '" -r true -f json')
		data = json.load(out)
		config['firewall_properties'] = data
	return config

def mgmt_check_firewall_properties(printRes = False):
	global results
	logme.loader()
	title = "Global Properties"
	cfg = mgmt_fetch_firewall_properties()
	logme.loader()
	check = []
	check.append([	"fwDropOutOfStateIcmp",		True,	"WARN",	"Drop Out of State: ICMP"	])
	check.append([	"fwDropOutOfStateUdp",		True,	"WARN",	"Drop Out of State: UDP"	])
	check.append([	"fwAllowOutOfStateTcp",		0,	"WARN",	"Drop Out of State: TCP"	])
	check.append([	"fwDropOutOfStateSctp",		True,	"WARN",	"Drop Out of State: SCTP"	])
	check.append([	"logImpliedRules",		True,	"INFO",	"Log implied Rules"		])
	check.append([	"natAutomaticArp",		True,	"INFO",	"Automatic NAT - ARP"		])
	check.append([	"natAutomaticRulesMerge",	True,	"INFO",	"Merge manual NAT Rules"	])
	check.append([	"natDstClientSide",		True,	"FAIL",	"Translate DST on Client Side"	])
	check.append([	"udpreply",			True,	"WARN",	"Accept statful UDP replies"	])
	check.append([	"allowDownloadContent",		True,	"INFO",	"Allow Download Content"	])
	check.append([	"allowUploadContent",		False,	"INFO",	"Improve product experience.."	])
	check.append([	"fw1enable",			True,	"WARN",	"Imp.Rules: Control Connections"])
	check.append([	"raccessenable",		True,	"WARN",	"Imp.Rules: RAS Connections"	])
	check.append([	"outgoing",			True,	"WARN", "Imp.Rules: Outgoing from GW"	])
	check.append([	"acceptOutgoingToCpServices",	True,	"WARN", "Imp.Rules: Gateway to CP"	])

	tmo = []
	tmo.append([	"tcpstarttimeout",		25,	"TCP start timeout"	])
	tmo.append([	"tcptimeout",			3600,	"TCP session timeout"	])
	tmo.append([	"tcpendtimeout",		20,	"TCP end timeout"	])
	tmo.append([	"tcpendtimeoutCern",		5,	"TCP end timeout, R80.20 and higher"	])
	tmo.append([	"udptimeout",			40,	"UDP virtual session timeout"		])
	tmo.append([	"icmptimeout",			30,	"ICMP virtual session timeout"		])
	tmo.append([	"othertimeout",			60,	"Other Protocol session timeout"	])
	tmo.append([	"sctpstarttimeout",		30,	"SCTP start timeout"	])
	tmo.append([	"sctptimeout",			3600,	"SCTP session timeout"	])
	tmo.append([	"sctpendtimeout",		20,	"SCTP end timeout"	])

	for c in check:
		logme.loader()
		if cfg['firewall_properties'][c[0]] == c[1]:
			state = "PASS"
			detail = ""
		else:
			state = c[2]
			detail = str(cfg['firewall_properties'][c[0]])
		results.append([title + " [" + c[3] + "]", detail, state, title])

	error = False
	tmp = []
	for t in tmo:
		logme.loader()
		if cfg['firewall_properties'][t[0]] == t[1]:
			state = "PASS"
			detail = ""
		else:
			state = "WARN"
			detail = str(cfg['firewall_properties'][t[0]])
			error = True
		tmp.append([title + " [" + t[2] + "]", detail, state, title])
	if error:
		results = results + tmp
	else:
		results.append([title + " [Session Timeouts]", "", "PASS", title])

	if printRes:
		print_results()


def mgmt_check_vpn_ras_topoupdate(printRes = False):
	global results
	cfg = mgmt_fetch_firewall_properties()
	title = "Remote Access Clients, Topology Update"
	state = "PASS"
	detail = ""
	if cfg['firewall_properties']['desktopUpdateFrequency'] == 0:
		state = "WARN"
		detail = "disabled"
	results.append([title, detail, state, "Remote Access"])
	if printRes:
		print_results()



def mgmt_check_vpn_prop_ras_item(val, unwanted):
	state = "PASS"
	txt = ""
	cfg = mgmt_fetch_firewall_properties()
	for v in cfg['firewall_properties'][val]:
		if v in unwanted:
			state = "WARN"
			if txt != "":
				txt += ", "
			txt += v
	return (txt, state)
			


def mgmt_check_vpn_prop_ras(printRes = False):
	global results
	logme.loader()
	title = "VPN Proposals - Remote Access"
	logme.loader()
	unwanted_hash = []
	unwanted_hash.append("MD5")
	unwanted_hash.append("SHA1")

	unwanted_enc = []
	unwanted_enc.append("DES")
	unwanted_enc.append("D3DES")
	unwanted_enc.append("AES_MINUS_128")

	unwanted_p1_hash = unwanted_hash
	unwanted_p1_enc  = unwanted_enc

	unwanted_p2_hash = unwanted_hash
	unwanted_p2_enc  = unwanted_enc

	(detail, state) = mgmt_check_vpn_prop_ras_item("desktopIkeP1HashAlgs", unwanted_p1_hash)
	results.append([title + " [Phase1: Hash]", detail, state, "Remote Access"])
	(detail, state) = mgmt_check_vpn_prop_ras_item("desktopIkeP1EncAlgs", unwanted_p1_enc)
	results.append([title + " [Phase1: Encryption]", detail, state, "Remote Access"])
	(detail, state) = mgmt_check_vpn_prop_ras_item("desktopIpsecDataIntegrityAlgs", unwanted_p2_hash)
	results.append([title + " [Phase2: Hash]", detail, state, "Remote Access"])
	(detail, state) = mgmt_check_vpn_prop_ras_item("desktopIpsecEncAlgs", unwanted_p2_enc)
	results.append([title + " [Phase2: Encryption]", detail, state, "Remote Access"])

	if printRes:
		print_results()


def mgmt_check_vpn_prop_s2s_item(p1, p2):
	unwanted_hash = []
	unwanted_hash.append("MD5")
	unwanted_hash.append("SHA1")
	unwanted_enc = []
	unwanted_enc.append("CAST")
	unwanted_enc.append("DES")
	unwanted_enc.append("3DES")
	unwanted_enc.append("AES-128")
	state = "PASS"
	detail = ""
	logme.loader()
	if p1["data-integrity"].upper() in unwanted_hash:
		state = "WARN"
		detail = "P1-Hash: " + p1["data-integrity"].upper()
	if p1["encryption-algorithm"].upper() in unwanted_enc:
		state = "WARN"
		if detail != "":
			detail += ", "
		detail += "P1-Enc: "+ p1["encryption-algorithm"].upper()
	if p2["data-integrity"].upper() in unwanted_hash:
		state = "WARN"
		if detail != "":
			detail += ", "
		detail += "P2-Hash: " + p2["data-integrity"].upper()
	if p2["encryption-algorithm"].upper() in unwanted_enc:
		state = "WARN"
		if detail != "":
			detail += ", "
		detail += "P2-Enc: " + p2["encryption-algorithm"].upper()
	return (detail, state)
		

def mgmt_check_vpn_prop_s2s(table1, table2, fname):
	global results
	logme.loader()
	title = "VPN-"+fname+" Proposals"
	out, err = func.execute_command('mgmt_cli -r true '+table1+' -f json')
	data = json.load(out)
	for p in data['objects']:
		logme.loader()
		out1, err1 = func.execute_command('mgmt_cli -r true '+table2+' uid ' + p['uid'] + ' -f json')
		data1 = json.load(out1)
		logme.loader()
		(detail, state) = mgmt_check_vpn_prop_s2s_item(data1['ike-phase-1'], data1['ike-phase-2'])
		results.append([title + " [" + data1['name'] + "]", detail, state, "VPN Communities"])
		logme.loader()


def mgmt_check_vpn_prop_star(printRes = False):
	mgmt_check_vpn_prop_s2s('show-vpn-communities-star', 'show-vpn-community-star', 'Star')
	if printRes:
		print_results()
	

def mgmt_check_vpn_prop_mesh(printRes = False):
        mgmt_check_vpn_prop_s2s('show-vpn-communities-meshed', 'show-vpn-community-meshed', 'Mesh')
        if printRes:
                print_results()



def check_all(printRes = False):
	mgmt_check_firewall_properties()
	mgmt_check_vpn_prop_ras()
	mgmt_check_vpn_ras_topoupdate()
	mgmt_check_vpn_prop_star()
	mgmt_check_vpn_prop_mesh()
	mgmt_check_malware_classification()
	mgmt_check_ica_certs('SIC')
	mgmt_check_ica_certs('IKE')
	if printRes:
		print_results()


def print_results():
	global results
	logme.results(results)
	results = []
