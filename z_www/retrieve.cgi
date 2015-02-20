#!/bin/env python
# -*- coding: UTF-8 -*-
import cgi
import sys
import os
import pprint
import subprocess

import cgitb
cgitb.enable(display=0, logdir="/hom/cyb/www_docs/okonomi/z/logdir")

# kjipe Ifi som har gammel programvare...
lib_path = os.path.abspath('simplejson-2.1.0')
sys.path.append(lib_path)
import simplejson as json


def printHeader():
    print "Content-Type: text/plain"
    print

def getDataOrExit():
    form = cgi.FieldStorage()
    if 'data' not in form:
        print "Invalid data"
        sys.exit(0)
    return json.loads(form['data'].value, 'utf-8')

def getTemplate():
    f = open('template.tex', 'r')
    data = f.read()
    data = data.decode('utf-8')
    f.close()
    return data

def safestring(data):
    CHARS = {
        '&':  r'\&',
        '%':  r'\%', 
        '$':  r'\$', 
        '#':  r'\#', 
        '_':  r'\_', #r'\letterunderscore{}', 
        '{':  r'\{', #r'\letteropenbrace{}', 
        '}':  r'\}', #r'\letterclosebrace{}',
        '~':  r'\~', #r'\lettertilde{}', 
        '^':  r'\^', #r'\letterhat{}', 
        '\\': r'\\', #r'\letterbackslash{}',
    }
    return "".join([CHARS.get(char, char) for char in unicode(data)])

def get_trans(data, addsum=0):
    trans = []
    sum = 0
    for r in data:
        info = r[0].split("-")
        mva = ""
        if len(info) > 2:
            mva = safestring(info[2])+r' \%'
        konto = info[1]
        type = info[0]
        trans.append("\\footnotesize{%s} & \\small{%s} & %s & %s & \\small{%s} \\\\" % \
            (mva, safestring(type), safestring(konto), safestring(r[2]), safestring(r[1])))
        sum += getInt(r[2])
    if addsum:
        trans.append("&&& \\textbf{%d} & \\textbf{Sum salg} \\\\[3mm]" % sum)
    return trans

def getInt(v):
    try:
        return int(v)
    except ValueError:
        return 0

def get_cash_table(data):
    ret = []
    t = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
    sum = 0
    sum_start = 0
    sum_end = 0
    for i, start in enumerate(data['start']):
        start = getInt(start)
        end = getInt(data['end'][i])

        x = end-start
        amount = x*t[i]
        ret.append("%s & %s & %s & %s & %s \\\\" % \
            (t[i], start, end, x, amount))
        sum += amount
        sum_start += start*t[i]
        sum_end += end*t[i]
    
    ret.append("\\textbf{Sum} & %d & %d & & %d \\\\" % \
        (sum_start, sum_end, sum))

    return "\n\hline".join(ret)

def generatePDF(data):
    f = open('ny.tex', 'w')
    data = data.encode('utf-8')
    f.write(data)
    f.close()

    p = subprocess.Popen(["pdflatex", "ny.tex"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    print 'http://cyb.no/okonomi/z/ny.pdf';


def exportJSON(data):
	"""
	1. load the existing data
	2. merge this data in the existing list
	3. save new list
	"""
	
	f = open('reports.json', 'r+')
	x = json.loads(f.read(), 'utf-8')
	f.seek(0)
	
	#if not 'list' in x:
	#	x = {'list': []}
	
	x['list'].append(data)
	
	x = json.dumps(x) #.encode('utf-8')
	f.write(x)
	f.truncate()
	f.close()

printHeader()
data = getDataOrExit()
tex = getTemplate()


exportJSON(data)


# variable data is a associative array with the following keys:
#   z => "Znr" in the spreadsheet (can be text, but excludes "Z" char)
#   date => date of the z report
#   builddate => current date (when exported)
#   responsible => who's in charge of the Z
#   type => the type of event (user provided, e.g. "Kafé")
#   cash => [
#     start => array of cash when started, first element is 1, second 5, 10, 20, 50 ...
#     end   => array of cash when ended (same structure as above)
#   ]
#   sales => [
#     array(account details, account text, value) e.g. ("K-3014-25", "Salg, mineralvann", 106),
#     ...
#   ]
#   debet => same as sales
#   comment => user provided comment


ztext = safestring(data['z'])
if ztext.isdigit():
    ztext = "Z " + ztext
tex = tex.replace("VAR-ZNR", ztext)

tex = tex.replace("VAR-RESPONSIBLE", safestring(data['responsible']))
tex = tex.replace("VAR-TYPE", safestring(data['type']))
tex = tex.replace("VAR-DATE", safestring(data['date']))
tex = tex.replace("VAR-BUILDDATE", safestring(data['builddate']))
tex = tex.replace("VAR-COMMENT", safestring(data['comment']).replace("\n", "\\\\\n"))

trans = "\n\cline{2-5}".join(get_trans(data['sales'], True)) \
      + "\n\cline{2-5}".join(get_trans(data['debet']))
tex = tex.replace("VAR-SALES-AND-DEBET", trans)

tex = tex.replace("VAR-CASH", get_cash_table(data['cash']))

generatePDF(tex)