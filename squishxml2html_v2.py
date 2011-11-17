#!/usr/bin/env python
# -*- encoding=utf8 -*-
# Copyright (c) 2009-10 froglogic GmbH. All rights reserved.
# This file is part of an example program for Squish---it may be used,
# distributed, and modified, without limitation.

from __future__ import nested_scopes
from __future__ import generators
from __future__ import division

import codecs
import datetime
import optparse
import os
import re
import sys
import time
import xml.sax
import xml.sax.saxutils
if sys.platform.startswith("win"):
    import glob

if sys.version_info[0] != 2 or (
   sys.version_info[0] == 2 and sys.version_info[1] < 4):
    print """%s: error: this program requires \
Python 2.4, 2.5, 2.6, or 2.7;
it cannot run with python %d.%d.
Try running it with the Python interpreter that ships with squish, e.g.:
C:\> C:\\squish\\squish-4.0.1-windows\\python\python.exe %s
""" % (os.path.basename(sys.argv[0]),
       sys.version_info[0], sys.version_info[1],
       os.path.basename(sys.argv[0]))
    sys.exit(1)


NEUTRAL_COLOR = u"#DCDCDC"  # gainsboro
PASS_COLOR = u"#f0fff0"     # honeydew
FAIL_COLOR = u"#FFB6C1"     # lightpink
ERROR_COLOR = u"#FA8072"    # salmon
LOG_COLOR = u"#DAA520"      # goldenrod
WARNING_COLOR = u"#FFA500"  # orange
FATAL_COLOR = u"#F08080"    # lightcoral
CASE_COLOR = u"#90ee90"     # lightgreen


INDEX_HTML_START = u"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<title>Squish Report Results Summary</title></head>
<body><h3>Squish Report Results Summary</h3>
<p><b>Report generated %s</b></p>
<table border="0">
"""

INDEX_HTML_END = u"</table></div></body></html>\n"

INDEX_ITEM = u"""<tr valign="%(valign)s" bgcolor="%(color)s">\
<td>%(when)s</td><td align="right">%(passes)d/%(tests)d</td><td>\
<a href="%(url)s">%(name)s</a></td></tr>\n"""

SUMMARY_MARK = "SzUzMzMzAzRzY" * 2
SUMMARY_SIZE = 2000

REPORT_START = u"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n
<link rel="stylesheet" href="../squishReportTableStyle.css" type="text/css" charset="utf-8" />\n 
<title>%%(title)s</title></head>
<body>
<h2>%%(title)s</h2>
<h3>Summary</h3><table border="0">\n%s</table>
<h3>Results</h3><div class="scroll"><table class="testcases" border="0">\n""" % (
        SUMMARY_MARK + " " * SUMMARY_SIZE)

DETAILS_START = u"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n
<link rel="stylesheet" href="../squishReportTableStyle.css" type="text/css" charset="utf-8" />\n 
<title>%%(title)s Details</title></head>
<body>
<h2>%%(title)s</h2>
<h3>Details</h3><button type="button" id="previous">&larr;</button><button type="button" id="next">&rarr;</button><div class="scroll"><table class="details" border="0">\n""" %()

REPORT_END = u"""</table>\n
<script src="http://code.jquery.com/jquery-latest.min.js"></script>\n
<script src="../jquery.scrollTo-min.js"></script>\n
<script src="../squishReportTable.js"></script>\n
</body></html>\n"""

SUMMARY_ITEM = u"""<tr valign="%(valign)s" bgcolor="%(color)s">\
<td>%(name)s</td><td align="right">%(value)s</td><td>%(extra)s</td>\
</tr>\n"""

CASE_ITEM = u"""<tr class="testcase" valign="%%(valign)s" bgcolor="%%(color)s"><td>%%(number)s</td><td class="tcName">\
<b>%%(name)s</b></td><td colspan="4">%%(start)s</td><td>%%(thisEFF)s</td></tr>\n""" % ()

VERIFICATION_ITEM = u"""<tr class="verification" valign="%%(valign)s" bgcolor="%s">\
<td>%%(name)s</td><td colspan="4">%%(filename_and_line)s</td>\
</tr>\n""" % NEUTRAL_COLOR

RESULT_ITEM = u"""<tr class="result" valign="%%(valign)s" bgcolor="%s"><td></td>\
<td class="%%(resultClass)s" bgcolor="%%(color)s">%%(type)s</td><td bgcolor="%%(color)s">\
%%(when)s</td><td bgcolor="%%(color)s">%%(description)s</td>\
<td bgcolor="%%(color)s">%%(detailed_description)s</td></tr>\n""" % (
        NEUTRAL_COLOR)

escape = None
datetime_from_string = None

CONSOLE_SUMMARY = None

class ReportError(Exception): pass

class ConsoleSummary():
    def __init__(self, reporter):
        self.suite_passes = reporter.suite_passes
        self.suite_fails = reporter.suite_fails
        self.suite_fatals = reporter.suite_fatals
        self.suite_errors = reporter.suite_errors
        self.suite_expected_fails = reporter.suite_expected_fails
        self.suite_unexpected_passes = reporter.suite_unexpected_passes
        self.suite_tests = reporter.suite_tests
        self.suite_cases = reporter.suite_cases
        
    def __str__(self):
        output = "\n*******************************************************\n"
        output += "Summary:\n"
        output += "Number of Test Cases:        " + str(self.suite_cases) + "\n"
        output += "Number of Tests:             " + str(self.suite_tests) + "\n"
        output += "Number of Passes:            " + str(self.suite_passes) + "\n"
        output += "Number of Fails:             " + str(self.suite_fails) + "\n"
        output += "Number of Errors:            " + str(self.suite_errors) + "\n"
        output += "Number of Fatals:            " + str(self.suite_fatals) + "\n"
        output += "Number of Expected Fails:    " + str(self.suite_expected_fails) + "\n"
        output += "Number of Unexpected Passes: " + str(self.suite_unexpected_passes) + "\n"
        output += "*******************************************************\n"

        return output

# shoe-in class for the opts crap.  Need to run the main through another python script, options make this absurdely difficult
class Options():
    def __init__(self):
        self.dir = "."
        self.iso = True
        self.preserve = False
        self.verbose = False
 
class SquishReportHandler(xml.sax.handler.ContentHandler):

    def __init__(self, opts, fh):
        xml.sax.handler.ContentHandler.__init__(self)
        if opts.preserve:
            self.valign = "middle"
        else:
            self.valign = "top"
        self.preserve = opts.preserve
        self.fh = fh
        self.details_fh = None
        self.in_report = False
        self.in_suite = False
        self.in_case = False
        self.in_test = False
        self.in_result = False
        self.in_description = False
        self.in_detailed_description = False
        self.in_message = False
        self.suite_start = None
        self.suite_passes = 0
        self.suite_fails = 0
        self.suite_fatals = 0
        self.suite_errors = 0
        self.suite_expected_fails = 0
        self.suite_unexpected_passes = 0
        self.suite_tests = 0
        self.suite_cases = 0
        self.suite_url = None
        self.suite_name = None
        self.case_name = None
        self.current_case = None
        self.current_caseNumber = 0
        self.result_type = None
        self.result_time = None
        self.description = []
        self.detailed_description = []
        self.message_type = None
        self.message_time = None
        self.message = []
        self.opts = None
        self.testcase_pass = True
        self.testcase_color = u"#90ee90"
        self.attribute_time = None
        self.testcase_errors = 0
        self.testcase_fails = 0
        self.testcase_fatals = 0


    def startElement(self, name, attributes):
        if name == u"SquishReport":
            version = attributes.get(u"version").split(".")
            if not version or int(version[0]) < 2:
                raise ReportError("unrecognized Squish Report version; "
                        "try using squishrunner's xml2.1 report-generator")
            self.in_report = True
            return
        elif not self.in_report:
            raise ReportError("unrecognized XML file")
        if name == u"test":
            if not self.in_suite:
                self.suite_name = escape(attributes.get("name") or "Suite")
                self.fh.write(REPORT_START % dict(title=self.suite_name))
                self.in_suite = True
            else:
                if self.in_case:
                    raise ReportError("nested tests are not supported")
                self.case_name = attributes.get("name" or "Test")
                self.suite_cases += 1
                self.in_case = True
        elif name == u"prolog":
            if self.in_case:
                if self.case_name != self.current_case:                    
                    self.createDetailsPage(attributes)
                
            elif self.in_suite:
                self.suite_start = datetime_from_string(
                        attributes.get("time"))
                
        elif name == u"epilog":
            # We ignore epilog times
            pass
        elif name == u"verification":
            line = attributes.get("line") or ""
            if line:
                line = "#" + line
            filename = attributes.get("file") or ""
            if filename:
                filename = os.path.normpath(filename)
            filename_and_line = filename + line
            self.details_fh.write(VERIFICATION_ITEM % dict(valign=self.valign,
                    name=escape(attributes.get("name") or "TEST"),
                    filename_and_line=escape(filename_and_line)))
        elif name == u"result":
            self.result_type = attributes.get("type")
            self.result_time = datetime_from_string(attributes.get("time"))
            self.suite_tests += 1
            if self.result_type == u"PASS":
                self.suite_passes += 1
            elif self.result_type == u"FAIL":
                self.suite_fails += 1
                self.testcase_color = FAIL_COLOR
                self.testcase_fails += 1
            elif self.result_type == u"FATAL":
                self.suite_fatals += 1
                self.testcase_color = FAIL_COLOR
            elif self.result_type == u"ERROR":
                self.suite_errors += 1
                self.testcase_color = FAIL_COLOR
            elif self.result_type in (u"XPASS", u"UPASS"):
                self.suite_unexpected_passes += 1
            elif self.result_type == u"XFAIL":
                self.suite_expected_fails += 1
            self.in_result = True
        elif name == u"description":
            if not (self.in_result or self.in_message):
                raise ReportError("misplaced description")
            self.in_description = False
            self.in_detailed_description = False
            type = attributes.get("type")
            if not type or type != u"DETAILED":
                self.in_description = True
            else:
                self.in_detailed_description = True
        elif name == u"message":
            self.message_type = attributes.get("type")
            if self.message_type == u"FATAL":
                self.suite_fatals += 1
            elif self.message_type == u"ERROR":
                self.suite_errors += 1
            self.message_time = datetime_from_string(
                    attributes.get("time"))
            self.in_message = True


    def characters(self, text):
        if self.in_message and not (self.in_description or self.in_detailed_description):
            self.message.append(text)
        elif self.in_description:
            self.description.append(text)
        elif self.in_detailed_description:
            self.detailed_description.append(text)


    def endElement(self, name):
        if name == u"SquishReport":
            if self.details_fh != None:
                self.closeDetailsFH()

            self.fh.write(REPORT_END)
        elif name == u"test":
            if self.in_test:
                self.in_test = False
            elif self.in_case:
                self.in_case = False
        elif name == u"prolog":
            pass
        elif name == u"epilog":
            # We ignore epilog times
            pass
        elif name == u"verification":
            pass
        elif name == u"result":
            color = FAIL_COLOR
            if self.result_type in (u"PASS", u"XFAIL"):
                color = PASS_COLOR
            elif self.result_type == u"ERROR":
                color = ERROR_COLOR
                self.testcase_color = ERROR_COLOR
            elif self.result_type == u"LOG":
                color = LOG_COLOR
            detailed_description = escape_and_handle_image(
                    "".join(self.detailed_description), self.preserve)
            description = escape_and_handle_image(
                    "".join(self.description), self.preserve)
            
            thisResultClass = "normal"
            if self.result_type == u"ERROR" or self.result_type == u"FATAL" or self.result_type == u"FAIL":
                thisResultClass = "defect"
            
            self.details_fh.write(RESULT_ITEM % dict(color=color,
                    resultClass=thisResultClass, type=self.result_type, when=self.result_time,
                    description=description,
                    detailed_description=detailed_description,
                    valign=self.valign))
            
            self.result_type = None
            self.result_time = None
            self.description = []
            self.detailed_description = []
            self.in_result = False
        elif name == u"description":
            if self.in_detailed_description:
                self.in_detailed_description = False
            elif self.in_description:
                self.in_description = False
        elif name == u"message":                
            color = LOG_COLOR
            if self.message_type == u"WARNING":
                color = WARNING_COLOR
            if self.message_type == u"ERROR":
                color = ERROR_COLOR
                self.testcase_color = ERROR_COLOR
                self.testcase_errors += 1
            elif self.message_type == u"FATAL":
                color = FATAL_COLOR
                self.testcase_color = FATAL_COLOR
                self.testcase_fatals += 1
            msg = self.message
            detail_msg = ""
            if (len("".join(self.message).strip()) == 0 and
                len(self.description) > 0):
                msg = self.description
                detail_msg = self.detailed_description
                self.description = []
                self.detailed_description = []
            msg = escape_and_handle_image("".join(msg), self.preserve)
            detail_msg = escape_and_handle_image("".join(detail_msg),
                    self.preserve)
            
            thisResultClass = "normal"
            if self.message_type == u"ERROR" or self.message_type == u"FATAL":
                thisResultClass = "defect"            
            
            self.details_fh.write(RESULT_ITEM % dict(color=color,
                    resultClass=thisResultClass, type=self.message_type, when=self.message_time,
                    description=msg,
                    detailed_description=detail_msg,
                    valign=self.valign))
            
            self.message = []
            self.in_message = False
     
    def closeDetailsFH(self):
        self.details_fh.write(REPORT_END)
        self.details_fh.close()
        
        effCount = ""
        if self.testcase_fails > 0:
            effCount += "Fails: " + str(self.testcase_fails)
        if self.testcase_errors > 0:
            effCount += " Errors: " + str(self.testcase_errors)
        if self.testcase_fatals > 0:
            effCount += " Fatals: " + str(self.testcase_fatals)
        
        self.current_caseNumber += 1   
        self.fh.write(CASE_ITEM % dict(number=str(self.current_caseNumber), name=escape(self.current_case), valign=self.valign, start=datetime_from_string(self.attribute_time), color=self.testcase_color, thisEFF=effCount))
        
        self.testcase_color = u"#90ee90"
        self.testcase_fails = 0
        self.testcase_errors = 0
        self.testcase_fatals = 0
           
    def createDetailsPage(self, attributes):
        if self.details_fh != None:
            self.closeDetailsFH()
        
        self.current_case = self.case_name
        self.attribute_time = attributes.get("time")
        details_file = os.path.abspath(os.path.join(self.opts.dir, os.path.basename(self.case_name + "_details.html")))
        try:
            self.details_fh = codecs.open(details_file, "w", encoding="utf-8")
            self.details_fh.write(DETAILS_START % dict(title=self.suite_name + "/" + self.case_name))
        except (EnvironmentError, ValueError, ReportError, xml.sax.SAXParseException), err:
            print >>sys.stderr, err

def escape_and_handle_image(description, preserve):
    match = re.search(ur"""saved\s+as\s+['"](?P<image>[^'"]+)['"]""",
            description, re.IGNORECASE)
    if match is None:
        match = re.search(
                ur"""screenshot\s+in\s+['"](?P<image>[^'"]+)['"]""",
                description, re.IGNORECASE)
    if match:
        before = escape(description[:match.start()])
        image = match.group("image")
        after = escape(description[match.end():])
        description = '%s <a href="file://%s">%s</a> %s' % (
                before, image, image, after)
        if preserve:
            description = "<pre>%s</pre>" % description
    else:
        description = escape(description, True)
    return description


def process_suite(opts, filename, index_fh=None):    
    extension = os.path.splitext(filename)[1]
    html_file = os.path.abspath(os.path.join(opts.dir,
            os.path.basename(filename.replace(extension, ".html"))))
    if opts.preserve:
        valign = "middle"
    else:
        valign = "top"
    fh = None
    try:
        try:
            fh = codecs.open(html_file, "w", encoding="utf-8")
            reporter = SquishReportHandler(opts, fh)
            reporter.opts = opts
            parser = xml.sax.make_parser()
            parser.setContentHandler(reporter)
            parser.parse(filename)
            write_summary_entry(valign, reporter, html_file)
            if index_fh is not None:
                write_index_entry(valign, index_fh, reporter,
                                  os.path.basename(html_file))
            if opts.verbose:
                print "wrote '%s'" % html_file
        except (EnvironmentError, ValueError, ReportError,
                xml.sax.SAXParseException), err:
            print >>sys.stderr, err
    finally:
        if fh is not None:
            fh.close()


def write_summary_entry(valign, reporter, html_file):
    global CONSOLE_SUMMARY
    CONSOLE_SUMMARY = ConsoleSummary(reporter)
    
    summary = []
    color = NEUTRAL_COLOR
    summary.append(SUMMARY_ITEM % dict(color=color, name="Test Cases",
            value=reporter.suite_cases, extra="", valign=valign))
    summary.append(SUMMARY_ITEM % dict(color=color, name="Tests",
            value=reporter.suite_tests, extra="", valign=valign))
    extra = ""
    if reporter.suite_expected_fails != 0:
        extra = " plus %d expected fails" % reporter.suite_expected_fails
    summary.append(SUMMARY_ITEM % dict(color=color, name="Passes",
            value=reporter.suite_passes, extra=extra, valign=valign))
    extra = ""
    if reporter.suite_unexpected_passes != 0:
        extra = " plus %d unexpected passes" % (
                reporter.suite_unexpected_passes)
    color = FAIL_COLOR
    if reporter.suite_fails == 0:
        color = NEUTRAL_COLOR
    summary.append(SUMMARY_ITEM % dict(color=color, name="Fails",
            value=reporter.suite_fails, extra=extra, valign=valign))
    color = ERROR_COLOR
    if reporter.suite_errors == 0:
        color = NEUTRAL_COLOR
    summary.append(SUMMARY_ITEM % dict(color=color, name="Errors",
            value=reporter.suite_errors, extra="", valign=valign))
    color = FATAL_COLOR
    if reporter.suite_fatals == 0:
        color = NEUTRAL_COLOR
    summary.append(SUMMARY_ITEM % dict(color=color, name="Fatals",
            value=reporter.suite_fatals, extra="", valign=valign))
    summary = u"".join(summary)
    summary = summary.encode("utf8")
    if len(summary) > SUMMARY_SIZE + len(SUMMARY_MARK):
        print >>sys.stderr, ("internal error: summary too big to write"
                "---try doubling SUMMARY_SIZE")
        return

    fh = None
    try:
        fh = open(html_file, "r+b")
        data = fh.read(8000 + SUMMARY_SIZE)
        i = data.find(SUMMARY_MARK)
        if i == -1:
            print >>sys.stderr, "internal error: failed to write summary"
        else:
            fh.seek(i)
            fh.write(summary)
    finally:
        if fh is not None:
            fh.close()

def write_index_entry(valign, index_fh, reporter, html_file):
    color = FAIL_COLOR
    if ((reporter.suite_tests ==
        reporter.suite_passes + reporter.suite_expected_fails) and
        not reporter.suite_errors and not reporter.suite_fatals):
        color = PASS_COLOR
    index_fh.write(INDEX_ITEM % dict(color=color, valign=valign,
            when=reporter.suite_start, passes=reporter.suite_passes,
            tests=reporter.suite_tests, url=html_file,
            name=reporter.suite_name))

def create_functions(opts):
    global escape
    if not opts.preserve:
        def function(s, is_multiline=False):
            return (xml.sax.saxutils.escape(s).strip().
                replace("\\n", "\n").replace("\n", "<br/>"))
    else:
        def function(s, is_multiline=False):
            if is_multiline:
                return "<pre>%s</pre>" % (
                        xml.sax.saxutils.escape(s).replace("\\n",
                                                           "\n").strip())
            else:
                return xml.sax.saxutils.escape(s).replace("\\n",
                                                          "\n").strip()
    escape = function

    global datetime_from_string
    if not opts.iso:
        # Sadly, Python doesn't properly support time zones out of the box
        def function(s):
            if s is None:
                return ""
            return time.asctime(time.strptime(s[:19],
                    "%Y-%m-%dT%H:%M:%S")).replace(" ", "&nbsp;")
    else:
        def function(s):
            if s is None:
                return ""
            return s
    datetime_from_string = function


def main(args=None):
    if args is None:
        args = sys.argv
            
    opts = Options()
    opts.dir = args[1]
    
    if sys.platform.startswith("win"):
        temp = []
        for arg in args:
            temp.extend(glob.glob(arg))
        args = temp
    
    create_functions(opts)

    if not os.path.exists(opts.dir):
        os.makedirs(opts.dir)
    
    index_file = os.path.abspath(os.path.join(opts.dir, "index.html"))
    fh = None
    
    try:
        fh = codecs.open(index_file, "w", encoding="utf-8")
        if opts.iso:
            when = datetime.date.today().isoformat()
        else:
            when = datetime.date.today().strftime("%x")
        fh.write(INDEX_HTML_START % when)
        process_suite(opts, args[0], fh)
        fh.write(INDEX_HTML_END)
        if opts.verbose:
            print "wrote '%s'" % index_file
    finally:
        if fh is not None:
            fh.close()
    
    return CONSOLE_SUMMARY

if __name__ == "__main__":
    sys.exit(main())