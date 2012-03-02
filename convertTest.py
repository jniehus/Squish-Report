#!/usr/bin/env python

import os
import sys
import subprocess
import squishxml2html_v2

class JenkinsJob:
    def __init__(self):
        self.slaveOS                = os.name
        self.name                   = "TestJob" 
        self.workspace              = "/Workspace"   
        self.buildID                = "1234567"    
        self.buildNumber            = "123"
        self.buildsFolder           = "/PTSoftware/Projects/ImageLab/Builds"
        self.squishCommand          = "['squishrunner', 'suite']"
        self.qtVersion              = "QtDlls 4.7.1"
        self.squishrunnerReturnCode = 0
        self.changeList             = "CL14567"
        self.version                = "4.1"
        self.runType                = "Regression"
        
    
    def __str__(self):
        jobValues = "---------- Job Configuration ----------\n"
        jobValues += "Jenkins Job " + self.name + ": \n";
        for attr, value in sorted(self.__dict__.iteritems()):
            # skip the "none"s
            if str(value) != "none":
                jobValues += " " + attr + ":  " + str(value) + "\n"
        
        jobValues += "---------------------------------------\n"
        return jobValues

def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    jj = JenkinsJob();
    
    # old squish way of doing things:
    #subprocess.call(['python', 'squishxml2html_v2.py', '--dir', 'output', '--iso', 'results.xml'])
    
    # new way, main returns summary to post in jenkins console for parsing. Makes it nice and easy to mark it PASS/UNSTABLE/FAIL
    # First Arg (0)  = name of xml to transform
    # Second Arg (1) = name of directory to put output
    # subsequent args (2+) = whatever you want to do in squishxml2html_v2
    # NOTE: args are in array format 
    summary = squishxml2html_v2.main(['results.xml', 'output', jj])
    print summary

if __name__ == "__main__":
    sys.exit(main())