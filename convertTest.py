#!/usr/bin/env python

import os
import sys
import subprocess
import squishxml2html_v2

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # old squish way of doing things:
    #subprocess.call(['python', 'squishxml2html_v2.py', '--dir', 'output', '--iso', 'results.xml'])
    
    # new way, main returns summary to post in jenkins console for parsing. Makes it nice and easy to mark it PASS/UNSTABLE/FAIL
    # First Arg (0)  = name of xml to transform
    # Second Arg (1) = name of directory to put output
    # subsequent args (2+) = whatever you want to do in squishxml2html_v2
    # NOTE: args are in array format 
    summary = squishxml2html_v2.main(['results.xml', 'output'])
    print summary

if __name__ == "__main__":
    sys.exit(main())