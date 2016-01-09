#!/bin/env python
# -*- coding: UTF-8 -*-
import cgi
import sys
import os
import re
import subprocess

import cgitb
cgitb.enable(display=0, logdir="/hom/cyb/www_docs/okonomi/z/logdir")

# kjipe Ifi som har gammel programvare...
lib_path = os.path.abspath('simplejson-2.1.0')
sys.path.append(lib_path)
import simplejson as json

VAT_CODES = {
    0: 0,
    3: 25,
    31: 15,
    5: 0,
    6: 0
}


def get_num(val):
    if val is None:
        return 0
    try:
        return int(val)
    except ValueError:
        return 0


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
        '_':  r'\_',  # r'\letterunderscore{}',
        '{':  r'\{',  # r'\letteropenbrace{}',
        '}':  r'\}',  # r'\letterclosebrace{}',
        '~':  r'\~',  # r'\lettertilde{}',
        '^':  r'\^',  # r'\letterhat{}',
        '\\': r'\\',  # r'\letterbackslash{}',
    }
    return "".join([CHARS.get(char, char) for char in unicode(data).strip()])


def get_trans(data, addsum=0):
    trans = []
    sum = 0
    for r in data:
        t = Transaction(r[0])

        mva = ""
        if t.vat != 0:
            if t.vat in VAT_CODES:
                mva = "%s (%d\\%%)" % (safestring(t.vat), VAT_CODES[t.vat])
            else:
                mva = safestring(t.vat) + '\\% (?)'

        trans.append("\\footnotesize{%s} & \\footnotesize{%s} & \\small{%s} & %s & %s & \\footnotesize{%s} \\\\" %
                     (t.project or "", mva, safestring(t.type), safestring(t.account), safestring(r[2]), safestring(r[1])))
        sum += getInt(r[2])
    if addsum:
        trans.append("&&&& \\textbf{%d} & \\textbf{Sum salg} \\\\[3mm]" % sum)
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
        ret.append("%s & %s & %s & %s & %s \\\\" %
                   (t[i], start, end, x, amount))
        sum += amount
        sum_start += start*t[i]
        sum_end += end*t[i]

    ret.append("\\textbf{Sum} & %d & %d & & %d \\\\" %
               (sum_start, sum_end, sum))

    return "\n\hline".join(ret)


def generatePDF(data, filename):
    f = open('archive/%s.tex' % filename, 'w')
    data = data.encode('utf-8')
    f.write(data)
    f.close()

    p = subprocess.Popen(["pdflatex", "%s.tex" % filename], stdout=subprocess.PIPE, cwd=os.path.abspath('archive'))
    out, err = p.communicate()

    print 'http://cyb.no/okonomi/z/archive/%s.pdf' % filename


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
    #   x = {'list': []}

    x['list'].append(data)

    x = json.dumps(x)  # .encode('utf-8')
    f.write(x)
    f.truncate()
    f.close()

printHeader()

data = getDataOrExit()
tex = getTemplate()

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
#                                                (beware: ^old format. new format: "25-K-3014-40404")
#     ...
#   ]
#   debet => same as sales
#   comment => user provided comment


class Transaction:
    def __init__(self, data):
        # format: [vatcode]-K/D-account-[project]
        # (old format: K/D-account-vat)

        # match again old format
        m = re.match(r'^([KD])-([\d_]+)(?:-(25|15|__))?$', data)
        if m is not None:
            self.type = m.group(1)
            self.account = m.group(2)
            self.vat = get_num(m.group(3)) or 0
            self.project = 0

        else:
            # new format
            m = re.match(r'^(?:(\d+)-)?([KD])-([\d_]+)(?:-([\d_]+))?$', data)
            if m is None:
                raise ValueError("Invalid data when parsing Trans: %s" % data)
            self.type = m.group(2)
            self.account = m.group(3)
            self.vat = get_num(m.group(1)) or 0
            self.project = get_num(m.group(4)) or 0


ztext = safestring(data['z'])
if ztext.isdigit():
    ztext = "Z " + ztext
tex = tex.replace("VAR-ZNR", ztext)

tex = tex.replace("VAR-RESPONSIBLE", safestring(data['responsible']))
tex = tex.replace("VAR-TYPE", safestring(data['type']))
tex = tex.replace("VAR-DATE", safestring(data['date']))
tex = tex.replace("VAR-BUILDDATE", safestring(data['builddate']))
tex = tex.replace("VAR-COMMENT", safestring(data['comment']).replace("\n", "\\\\\n"))

trans = "\n\cline{3-6}".join(get_trans(data['sales'], True)) \
      + "\n\cline{3-6}".join(get_trans(data['debet']))
tex = tex.replace("VAR-SALES-AND-DEBET", trans)

tex = tex.replace("VAR-CASH", get_cash_table(data['cash']))

prettydate = ''.join(data['date'][-10:].split('.')[::-1])
prettybuilddate = ''.join(data['builddate'][:10].split('.')[::-1]) + '_' + data['builddate'][11:13] + data['builddate'][14:16]
filename = '%s-%s-%s' % (prettydate, re.sub(r'[^a-zA-Z0-9]', '_', ztext), prettybuilddate)
generatePDF(tex, filename)

exportJSON(data)
