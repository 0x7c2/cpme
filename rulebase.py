#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

import threading
from getpass import getpass
from datetime import datetime
import logme
import func
import time
import json
import ipaddress

menu_text = "Manage/Optimize Rulebase"
menu_item = [	["Disable Zero Hit Rules",			"rulebase.disable_or_move_rules(True, [], True)"],
		["Move Disabled Rules",				"rulebase.disable_or_move_rules(True, [], False, True)"],
		["Show Zero Hit Rules",				"rulebase.show_rules_zero(True)"],
		["temp fetch objects",				"rulebase.fetch_all_objects()"],
                ["Back to Main Menu",	 			"menu_set('main')"]]

results = []
waitforme = False

layers = []
hosts = []
networks = []

loggedin = False
modified = False
sessionid = "/var/log/cpme-session.id"

now = datetime.now() # current date and time

timestamp = now.strftime("%Y%m%d%H%M%S")

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


def fetch_all_access_layer():
	global layers
	if len(layers) < 1:
		out, err = func.execute_command('mgmt_cli -r true show access-layers --format json')
		data = json.load(out)
		for p in data['access-layers']:
			if p['type'] == "access-layer":
				layers.append([p['uid'], p['name']])

def fetch_all_objects():
	global hosts
	global networks
	cmds = ['hosts', 'networks']
	for c in cmds:
		if c == 'hosts' and len(hosts) > 0:
			break
		if c == 'networks' and len(networks) > 0:
			break
		last = 0
		moreData = True
		while moreData:
			out, err = func.execute_command("mgmt_cli -r true show "+c+" limit 50 offset "+str(last)+" --format json")
			data = json.load(out)
			if data['to'] >= data['total']:
				moreData = False
			else:
				last = data['to']
			for o in data['objects']:
				if c == "hosts":
					hosts.append(o)
				if c == "networks":
					networks.append(o)
	print(hosts)
	print(networks)


def select_access_layer():
	global layers
	fetch_all_access_layer()
	print("")
	print("Please select your access layer:")
	i = 0
	for layer in layers:
		print("- [" + str(i+1) + "] " + layer[0] + " - " + layer[1])
		i = i + 1
	print("- [0] Back to Menu")
	selected_layer = input("Enter your choice [0-"+str(len(layers))+"]: ")
	if selected_layer == "0":
		menu_set('rulebase')
	else:
		sel = int(selected_layer)-1
		selLayer = layers[sel]
		print("")
		return selLayer

def show_rules_zero_all(printRes = False):
	global layers
	fetch_all_access_layer()
	for layer in layers:
		show_rules_zero(False, layer)
	if printRes:
		print_results()


def api_login():
	global loggedin
	global modified
	while not loggedin:
		print("")
		print("Please enter credentials for Login to SmartCenter...")
		username = input("Enter Username: ")
		password = getpass("Enter Password: ")
		print("")
		failure = False
		out, err = func.execute_command('mgmt_cli login user ' + username + ' password ' + password + ' > ' + sessionid, True)
		ses, err = func.execute_command('cat ' + sessionid)
		for line in ses:
			if "err_login_failed" in line:
				failure = True
			if failure:
				print(line.strip('\n'))
		if not failure:
			loggedin = True
			modified = False
		print("")

def api_logout():
	global loggedin
	global modified
	if loggedin:
		if modified:
			api_publish()
		out, err = func.execute_command('mgmt_cli logout -s ' + sessionid)
		loggedin = False


def api_checklogin():
	global loggedin
	if not loggedin:
		api_login()


def api_publish(doLogout = False):
	global loggedin
	global modified
	if not loggedin:
		print("Not logged in, can not publish!")
	else:
		if modified:
			s = input("Would you like to (p)ublish or (d)iscard changed settings? [P/d]: ")
			if s == "" or s.lower() == "p":
				print("-> Publishing changes....")
				out, err = func.execute_command('mgmt_cli -s ' + sessionid + ' publish', True)
			else:
				print("-> Discarding changes....")
				out, err = func.execute_command('mgmt_cli -s ' + sessionid + ' discard', True)
		else:
			print("Nothing changed, no need to publish!")
	if doLogout:
		api_logout()


def create_access_layer(alname = "", publish = False, logout = False):
	global modified
	api_checklogin()
	if alname == "":
		print("")
		print("Please provide new name for access-layer, to accept")
		print("the default in brackets, just hit return.")
		print("")
		default = timestamp+"-cpme"
		alname = input("New Access Layer Name ["+default+"]: ")
		if alname == "":
			alname = default
	out, err = func.execute_command("mgmt_cli -s " + sessionid + " add access-layer name " + alname, True)
	modified = True
	if publish:
		api_publish()
	if logout:
		api_logout()
	return alname


def modify_access_rule(alname, ruid, mod):
	global modified
	api_checklogin()
	out, err = func.execute_command("mgmt_cli -s " + sessionid + " set access-rule uid " + ruid + " layer '" + alname + "' " + mod + " --format json", True)
	modified = True

def create_access_rule(alname, baserule, rule_name, rule_action, rule_dst, rule_src, rule_installon, rule_svc, rule_track):
	global modified
	api_checklogin()
	out, err = func.execute_command("mgmt_cli -s " + sessionid + " add access-rule layer '"+alname+"' position.above '"+baserule+"' name '"+rule_name+"' action '"+rule_action+"' destination '"+rule_dst+"' source '"+rule_src+"' service '"+rule_svc+"' install-on '"+rule_installon+"' track '"+rule_track+"'")
	modified = True

def delete_access_rule(alname, ruid):
	global modified
	api_checklogin()
	out, err = func.execute_command("mgmt_cli -s " + sessionid + " delete access-rule uid " + ruid + " layer " + alname, True)
	modified = True

def copy_access_rule(rule, alname, oldal = "", pos = "bottom"):
	global modified
	api_checklogin()
	rtxt = ""
	fields = ["name", "action", "destination-negate", "enabled", "service-negate", "source-negate", "comments"]
	lists  = ["source", "destination", "service", "install-on", "time", "vpn"]
	stamp = oldal + "@rule-" + str(rule["rule-number"])
	for f in fields:
		if f in rule:
			if f == "name":
				rtxt = rtxt + f + ' "' + rule[f] + '" '
			elif f == "comments":
				if rule[f] != "":
					rtxt = rtxt + f + ' "' + rule[f] + '\\n' + stamp + '" '
				else:
					rtxt = rtxt + f + ' "' + stamp + '" '
			else:
				rtxt = rtxt + f + " " + str(rule[f]) + " "
	for l in lists:
		if l in rule:
			i = 1
			for lfield in rule[l]:
				# track doesnt work now, returned uid - but rule needs plain text
				if l == "track":
					rtxt = rtxt + l + "." + lfield + " " + str(rule[l][lfield]) + " "
				else:
					rtxt = rtxt + l + "." + str(i) + " " + str(lfield) + " "
					i = i + 1
	out, err = func.execute_command("mgmt_cli -s " + sessionid + " add access-rule layer " + alname + " position " + pos + " " + rtxt, True)
	modified = True

def disable_or_move_rules(confirm = True, accesslayer = [], disableZero = False, moveDisabled = False):
	if len(accesslayer)<1:
		accesslayer = select_access_layer()
	print("")
	if disableZero:
		print("Operation: Disable Zero Hit Rules...")
	if moveDisabled:
		print("Operation: Move Disabled Rules...")
	print("")
	newlayer = ""
	fetchedAll = False
	rulesFound = False
	offset = "0"
	while not fetchedAll:
		out, err = func.execute_command('mgmt_cli -r true show access-rulebase uid '+accesslayer[0]+' details-level "full" use-object-dictionary true show-hits true offset '+offset+' --format json')
		data = json.load(out)
		for p in data['rulebase']:
			for rule in p['rulebase']:
				processRule = False
				if disableZero and rule['hits']['level'] == "zero":
					processRule = True
					if newlayer == "":
						api_checklogin()
						newlayer = "not-needed"
				if moveDisabled and rule['enabled'] == False:
					processRule = True
					if newlayer == "":
						newlayer = create_access_layer()
				if processRule:
					print("rule uid          : " + rule['uid'])
					print("rule enabled      : " + str(rule['enabled']))
					rname = ""
					if 'name' in rule:
						rname = rule['name']
					print("rule name         : " + rname)
					print("rule last modifiy : " + rule['meta-info']['last-modify-time']['iso-8601'])
					print("rule last modifier: " + rule['meta-info']['last-modifier'])
					print("rule comments     : " + rule['comments'])
					src_txt = ""
					for src in rule['source']:
						if src_txt != "":
							src_txt = src_txt + ","
						for dict in data['objects-dictionary']:
							if dict['uid'] == src:
								src_txt = src_txt + dict['name']
					print("rule source       : " + src_txt)
					dst_txt = ""
					for dst in rule['destination']:
						if dst_txt != "":
							dst_txt = dst_txt + ","
						for dict in data['objects-dictionary']:
							if dict['uid'] == dst:
								dst_txt = dst_txt + dict['name']
					print("rule destination  : " + dst_txt)
					srv_txt = ""
					for srv in rule['service']:
						if srv_txt != "":
							srv_txt = srv_txt + ","
						for dict in data['objects-dictionary']:
							if dict['uid'] == srv:
								srv_txt = srv_txt + dict['name']
					print("rule service      : " + srv_txt)
					print("")
					s = input("Should this rule modified? [Y/n/c]: ")
					if s.lower() == "c":
						break
					if s.lower() == "y" or s.lower() == "":
						print("modifing rule " + rule['uid'])
						if moveDisabled:
							copy_access_rule(rule, newlayer, accesslayer[1])
							delete_access_rule(accesslayer[0], rule["uid"])
						if disableZero:
							if rule['comments'] != "":
								rnewname = rule['comments'] + "\n" + timestamp + "@cpme"
							else:
								rnewname = timestamp + "@cpme"
							modify_access_rule(accesslayer[0], rule['uid'], 'comments "'+rnewname+'" enabled false')
					print("")
					print("")
		if data['to'] >= data['total']:
			fetchedAll = True
		else:
			offset = str(data['to'])
	api_logout()


def show_rules_zero(printRes = False, accessLayer = []):
	global results
	global waitforme
	if len(accessLayer)<1:
		accessLayer = select_access_layer()
	title = "Show Zero Hit Rules"
	t = threading.Thread(target=loader)
	t.start()
	fetchedAll = False
	offset = "0"
	while not fetchedAll:
		out, err = func.execute_command('mgmt_cli -r true show access-rulebase uid '+accessLayer[0]+' details-level "standard" use-object-dictionary true show-hits true offset '+offset+' --format json')
		data = json.load(out)
		if data['total'] < 1:
			break
		for p in data['rulebase']:
			if "rulebase" in p:
				for n in p['rulebase']:
					if n['hits']['level'] == "zero" and n['enabled'] == True:
						if 'name' in n:
							rname = n['name']
						else:
							rname = 'un-named'
						results.append(["Zero Hits on Layer: " + accessLayer[1] + ", Rule ["+str(n['rule-number'])+"]: "+rname, n['hits']['level'], "INFO", "Rulebase"])
			if "hits" in p and p['hits']['level'] == "zero" and p['enabled'] == True:
				if 'name' in p:
					rname = p['name']
				else:
					rname = 'un-named'
				results.append(["Zero Hits on Layer: " + accessLayer[1] + ", Rule ["+str(p['rule-number'])+"]: "+rname, p['hits']['level'], "INFO", "Rulebase"])
		if data['to'] >= data['total']:
			fetchedAll = True
		else:
			offset = str(data['to'])
	waitforme = False
	t.join()
	if printRes:
		print_results()


def print_results():
	global results
	logme.results(results)
	results = []
