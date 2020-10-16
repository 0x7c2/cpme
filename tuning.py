#
# Copyright 2020 by 0x7c2, Simon Brecht.
# All rights reserved.
# This file is part of the Report/Analytic Tool - CPme,
# and is released under the "Apache License 2.0". Please see the LICENSE
# file that should have been included as part of this package.
#

from subprocess import Popen, PIPE
import logme
import os

menu_text = "Tuning Options"
menu_item = [	["Configure Multi Queueing",		"tuning.multiq()"],
		["Configure Prio Queueing",             "tuning.prioq()"],
                ["Back to Main Menu",	 		"menu_set('main')"]]


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


def multiq():
	os.system("cpmq set")

def prioq():
	os.system("fw ctl multik prioq")
