#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE
import os
import sys
import sqlite3
import time
import logme
import ipaddress

def get_path(env):
        try:
                return os.environ[env]
        except:
                return "/path-not-found/"

# note:
# new file location in r80.40, lets do checkup after loading
# functions.
#
# cpview_database = "/var/log/CPView_history/CPViewDB.dat"
#

cpregistry_file = get_path("CPDIR") + "/registry/HKLM_registry.data"
cpregistry = {}

def get_cpregistry(prod, key, returnBool = False):
	global cpregistry
	global cpregistry_file
	inSection = False
	value = "0"
	if prod+"_"+key in cpregistry:
		return cpregistry[prod + "_" + key]
	cmd = Popen("cat " + cpregistry_file, shell=True, stdout=PIPE, universal_newlines=True)
	i = 0
	for line in cmd.stdout:
		i = i + 1
		if ": (" + prod in line:
			inSection = True
		if inSection and ":" + key in line:
			data = line.strip('\n').replace(" ","").replace('\t','')
			value = data.replace(":" + key, "").replace("(", "").replace(")", "")
			break
	if "[4]" in value:
		value = value[4]
	if value != "":
		cpregistry[prod + "_" + key] = value
	if returnBool:
		if value == "0":
			return False
		else:
			return True
	else:
		return value


def execute_command(cmd, waitForMe = False):
	execme = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
	out = execme.stdout
	err = execme.stderr
	if waitForMe:
		execme.wait()
	return out, err


def execute_sqlite_query(sql):
	global cpview_database
	run = True
	while run:
		try:
			logme.loader()
			db = sqlite3.connect(cpview_database)
			dbcur = db.cursor()
			dbcur.execute(sql)
			run = False
			break
		except:
			logme.loader()
			time.sleep(0.5)
	return dbcur


def hex2ip(s):
	s = s.strip(' ')
	indices = range(0, 8, 2)
	data = [str(int(s[x:x+2], 16)) for x in indices]
	ipaddr = '.'.join(data)
	return ipaddr

def calc_subnet(firstip, lastip):
	a = ipaddress.IPv4Address(firstip)
	b = ipaddress.IPv4Address(lastip)
	subnets = [ipaddr for ipaddr in ipaddress.summarize_address_range(a, b)]
	for s in subnets:
		return s
	return subnets


def tail_and_head(file, tail = -1, head = -1):
	p = []
	p.append('tail')
	p.append('-n')
	p.append(str(tail))
	p.append(file)
	proc = Popen(p, stdout=PIPE, universal_newlines=True)
	lines = proc.stdout.readlines()
	if head > -1:
		return lines[:head]
	else:
		return lines


def str_pad(val, size, fill = " ", padLeft = False):
	tmp = str(val)
	if padLeft:
		while len(tmp) < size:
			tmp = fill + tmp
	else:
		while len(tmp) < size:
			tmp = tmp + fill
	return tmp


def confirm(cmd):
	print("> Executing command: " + cmd)
	a = input("> Should i really execute command? [y/N] ")
	if a.lower() == "y":
		os.system(cmd)
		return True
	else:
		print("Aborting!")
	return False


def self_update():
	cmd = "curl_cli https://raw.githubusercontent.com/0x7c2/cpme/main/cpme-install.sh -k -# | bash"
	print("")
	print("> Trying self-update routine...")
	print("> Executing command: " + cmd)
	print("")
	print("")
	os.system(cmd)


def make_check_all():
	results = []
	gaia.check_all(False)
	results = results + gaia.get_results(True)
	health.check_all(False)
	results = results + health.get_results(True)
	performance.check_all(False)
	results = results + performance.get_results(True)
	files.check_all(False, "all")
	results = results + files.get_results(True)
	if isManagement():
		rulebase.show_rules_zero_all(False)
		results = results + rulebase.get_results(True)
		mgmt.check_all(False)
		results = results + mgmt.get_results(True)
	return results

def make_report_html():
	html = logme.html_out(make_check_all())
	f = open("/web/htdocs2/cpme.html", "w")
	f.write(html)
	f.close()
	os.system("chmod 0755 /web/htdocs2/cpme.html")
	print("Done!" + 60*" ")
	print("")
	print("To view the report, follow below steps:")
	print("1. Please browse to GAiA Portal and login with your account.")
	print("2. Take a look at the URL in your webbrowser, you should see <something>/cgi-bin/home.tcl")
	print("3. Just replace <cgi-bin/home.tcl> with <cpme.html>")
	print("")

def make_report_cli():
	logme.results(make_check_all())

cache_isFirewall = "none"
def isFirewall():
	global cache_isFirewall
	if cache_isFirewall == "none":
		cache_isFirewall = get_cpregistry("FW1", "FireWall", True)
	return cache_isFirewall

cache_isManagement = "none"
def isManagement():
	global cache_isManagement
	if cache_isManagement == "none":
		cache_isManagement = get_cpregistry("FW1", "Management", True)
	return cache_isManagement

cache_isCluster = "none"
def isCluster():
	global cache_isCluster
	if cache_isCluster == "none":
		cache_isCluster = get_cpregistry("FW1", "HighAvailability", True)
	return cache_isCluster

cache_fwVersion = "none"
def fwVersion():
	global cache_fwVersion
	if cache_fwVersion == "none":
		out, err = execute_command("fw ver | grep -oE '(R[0-9\.]+)'")
		cache_fwVersion = out.read().strip('\n').strip(' ')
	return cache_fwVersion

cache_ipmiInfo = "none"
def ipmiInfo():
	global cache_ipmiInfo
	if cache_ipmiInfo == "none":
		o = []
		out, err = execute_command("ipmitool sensor list")
		for line in out:
			if "Could not open device" in line:
				break
			o.append(line.split('|'))
		cache_ipmiInfo = o
	return cache_ipmiInfo
	
cache_isFWUserMode = "none"
def isFWUserMode():
	global cache_isFWUserMode
	if cache_isFWUserMode == "none":
		if isFirewall:
			out, err = execute_command('lsmod | grep -c "fwmod"')
			ret = bool(int(out.read().strip('\n').strip(' ')))
		else:
			ret = False
		cache_isFWUserMode = ret
	return cache_isFWUserMode


if fwVersion() == "R80.20" or fwVersion() == "R80.30":
	cpview_database = "/var/log/CPView_history/CPViewDB.dat"
if fwVersion() == "R80.40":
	cpview_database = "/var/log/opt/CPshrd-" + fwVersion() + "/cpview_services/cpview_services.dat"


import gaia, health, rulebase, performance, mgmt, files
