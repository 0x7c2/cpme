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

menu_text = "File Modifications"
menu_item = [	["Check all known files",		"files.check_all(True)"]]

if func.isFirewall():
	menu_item.append(["Check known files on gateway",	"files.check_all(True, 'gw')"])

if func.isManagement():
	menu_item.append(["Check known files on management",	"files.check_all(True, 'mgmt')"])

menu_item.append(["Back to Main Menu",	 		"menu_set('main')"])

PPKDIR = func.get_path("PPKDIR")
FWDIR = func.get_path("FWDIR")

results = []

# fwkern.conf
files_fwd = [	[FWDIR + "/boot/modules/fwkern.conf", "1"] ]

# fwaffinity.conf
files_fwd.append([FWDIR + "/conf/fwaffinity.conf", "a1603a26029ebf4aba9262fa828c4685"])

# simkern.conf
files_fwd.append([PPKDIR + "/boot/modules/simkern.conf", "5e93554515a637726c4832adee9095ce"])

# simkern.conf
files_fwd.append([PPKDIR + "/conf/simkern.conf", "1"])

# trac_client_1.ttm
files_fwd.append([FWDIR + "/conf/trac_client_1.ttm", "9d898b072aa5e0d3646ce81829c45453"])

# ipassignment.conf
files_fwd.append([FWDIR + "/conf/ipassignment.conf", "4564f2ffd76c72c5503d4a74420f0ef7"])

# discntd.if
files_fwd.append([FWDIR + "/conf/discntd.if", "1"])

# user.def
files_fwm = [	[FWDIR + "/lib/user.def", "e4c4b057826ed24937a92cf16541b8ee"] ]

# table.def
if func.fwVersion() == "R80.20" or func.fwVersion() == "R80.30":
	files_fwm.append([FWDIR + "/lib/table.def", "1b3268539fb3c5711891edc49bce57ee"])
if func.fwVersion() == "R80.40":
	files_fwm.append([FWDIR + "/lib/table.def", "ac179cc481dd7b6d18dcb21abe47ddef"])

# crypt.def
files_fwm.append([FWDIR + "/lib/crypt.def", "45acf726e29970add148df6816f313ba"])

# implied_rules.def
if func.fwVersion() == "R80.20" or func.fwVersion() == "R80.30":
	files_fwm.append([FWDIR + "/lib/implied_rules.def", "43e98a9595e479f1a7d879f9ba9e38ff"])
if func.fwVersion() == "R80.40":
	files_fwm.append([FWDIR + "/lib/implied_rules.def", "d1cf4d23e544060c26ff8f77bcd3864a"])

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

def check_all(printRes = False, ftype = "all"):
	global results
	title = "File"
	files_arr = []
	if ftype == "gw":
		files_arr = files_fwd
	if ftype == "mgmt":
		files_arr = files_fwm
	if ftype == "all":
		if func.isFirewall():
			files_arr = files_arr + files_fwd
		if func.isManagement():
			files_arr = files_arr + files_fwm
	i = 0
	while i < len(files_arr):
		state = "PASS"
		detail = ""
		try:
			with open(files_arr[i][0], "rb") as f:
				bytes = f.read()
				fhash = hashlib.md5(bytes).hexdigest()
			if fhash != files_arr[i][1]:
				state = "WARN"
				detail = "Wrong Hash!"
		except:
			if files_arr[i][1] != "1":
				state = "FAIL"
				detail = "not found!"
		results.append([title + " (" + files_arr[i][0] + ")", detail, state, "Filesystem"])
		i = i + 1
	if printRes:
		logme.results(results)
		results = []

