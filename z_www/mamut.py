#!/bin/env python
# -*- coding: utf-8 -*-
import csv
import cStringIO
import codecs
import re
import sys
import os
from pprint import pprint
from cmd import Cmd
import types

# kjipe Ifi som har gammel programvare...
lib_path = os.path.abspath('simplejson-2.1.0')
sys.path.append(lib_path)
import simplejson as json

csv_default_line = [
    'GBAT10',
    '', # 1 = bilagsnr
    '', # 2 = bilagsdato (yyyymmdd)
    '6', # bilagstype (6 = kasse, 9 = diverse)
    '', # 4 = periode
    '', # 5 = regnskapsår
    '', # 6 = konto
    '', # 7 = mva (1 = ingen, 30 = 25 % utgående, 371 = 15 % utgående)
    '', # 8 = saldo (netto, altså uten evt. mva)
    '0', # kundenr
    '0', # leverandørnr
    '', # kontaktnavn
    '', # adresse
    '', # postnr
    '', # poststed
    '', # fakturanr
    '', # kid
    '0', # forfallsdato
    '', # (not in use)
    '', # bankkonto
    '', # 20 = beskrivelse hovedbok
    '', # 21 = beskrivelse reskontro
    '0', # rentefakturering
    '0', # prosjekt
    '1', # avdeling
    '0', # betalingsbetingelse
    'T', # 26 = brutto? (T = bruk neste beløp i kombinasjon med MVA, F = ikke beregn MVA)
    '', # 27 = bruttosum
    '' # ekstra felt for å sikre semikolon på slutten
]

CSV_INDEX_BNR = 1
CSV_INDEX_BDATE = 2
CSV_INDEX_BPERIOD = 4
CSV_INDEX_BYEAR = 5
CSV_INDEX_ACCOUNT = 6
CSV_INDEX_VAT = 7
CSV_INDEX_NETTO = 8
CSV_INDEX_DESC1 = 20
CSV_INDEX_DESC2 = 21
CSV_INDEX_CALC_VAT = 26
CSV_INDEX_BRUTTO = 27

VAT_CODES = {
    0: 1,
    15: 371,
    25: 10
}

DATA_FILE_IN = 'reports.json'
DATA_FILE_OUT = 'bilag.csv'

class CSVWriter():
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    (code mostly from https://docs.python.org/2/library/csv.html)
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([(s.encode("utf-8") if isinstance(s, types.UnicodeType) else s) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class CYBMamutImport():
    def __init__(self):
        self.nextId = 1
        self.year = 2015

    def loadJSON(self):
        f = open(DATA_FILE_IN, 'r')
        self.json = json.loads(f.read(), 'utf-8')['list']
        f.close()

    def getCSVWriter(self):
        if not hasattr(self, 'csv'):
            self.csv_f = open(DATA_FILE_OUT, 'w')
            self.csv = CSVWriter(self.csv_f, delimiter=';', quoting=csv.QUOTE_NONE)
        return self.csv

    def closeOutputCSV(self):
        self.csv_f.close()

    def genZNr(self, z):
        """Generer tekstversjon av Z-nr"""
        return ('Z%s' % z['z']) if str(z['z']).isdigit() else z['z']

    def validateZ(self, z):
        """Sjekker om kredit og debet går opp i hverandre"""
        sum = 0
        for item in z['sales'] + z['debet']:
            sum += (-1 if item[0][0] == 'K' else 1) * item[2]

        return sum == 0

    def addZ(self, z):
        # konverter "Tirsdag dd.mm.yyyy" til "yyyymmdd"
        date = z['date'][-10:].split('.')
        date.reverse()
        date = ''.join(date)

        period = int(date[4:6])
        znr = self.genZNr(z)

        for item in z['sales'] + z['debet']:
            # TODO: validate account
            # TODO: validate VAT

            modifier = -1 if item[0][0] == 'K' else 1
            account = item[0][2:6]
            vat = 0 if len(item[0]) < 9 else int(item[0][7:9])
            vat_code = VAT_CODES[vat]

            amount = modifier * item[2]
            netto = amount / (1 + vat/100.0)
            netto = round(netto, 2)
            brutto = amount

            line = list(csv_default_line)
            line[CSV_INDEX_BNR] = self.nextId
            line[CSV_INDEX_BDATE] = date
            line[CSV_INDEX_BPERIOD] = period
            line[CSV_INDEX_BYEAR] = self.year
            line[CSV_INDEX_ACCOUNT] = account
            line[CSV_INDEX_VAT] = vat_code
            line[CSV_INDEX_NETTO] = netto
            line[CSV_INDEX_DESC1] = "%s %s" % (znr, item[1])
            line[CSV_INDEX_DESC2] = line[CSV_INDEX_DESC1]
            line[CSV_INDEX_CALC_VAT] = 'T'
            line[CSV_INDEX_BRUTTO] = brutto

            self.getCSVWriter().writerow(line)
            print "LINE: %s: %s (%s%%) %d (%s)" % (znr, account, vat, amount, item[1])

        self.nextId += 1

class MyPrompt(Cmd):
    def __init__(self, cyb):
        Cmd.__init__(self)
        self.cyb = cyb

    def do_list(self, args):
        if len(self.cyb.json) == 0:
            print "No items in list"

        i = 0
        for z in self.cyb.json:
            print "%d: %s (%s) (%s) generated %s" % (i, self.cyb.genZNr(z), z['date'], z['type'], z['builddate'])
            i += 1

    def do_add(self, args):
        if not args.isdigit():
            print "Invalid argument, syntax: add <index>"
            return

        try:
            z = self.cyb.json[int(args)]

            if self.cyb.validateZ(z) == False:
                print "ERROR: Z-report don't sum to 0 (kredit+debet)"
                return

            self.cyb.addZ(z);
            print "Added entry for %s (%s) (%s) generated %s" % (self.cyb.genZNr(z), z['date'], z['type'], z['builddate'])
        except IndexError:
            print "Index %s not found in list" % args

    def do_save(self, args):
        self.cyb.closeOutputCSV()

    def do_num(self, args):
        try:
            self.cyb.nextId = int(args)
        except ValueError:
            print "Invalid value"

    def do_quit(self, args):
        """Quits the program"""
        print "Quitting"
        raise SystemExit

if __name__ == '__main__':
    cyb = CYBMamutImport()
    cyb.loadJSON()

    prompt = MyPrompt(cyb)
    prompt.prompt = '> '
    prompt.cmdloop('Starting prompt...')
