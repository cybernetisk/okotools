#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import re
import json
import time
import io

from .tripletex import TripletexImporter
from .mamut import Transform
from .utils import get_num

LEDGER_SERIES = 80000
DEVIATION_ACCOUNT = '1909'
DATA_FILE_OUT = 'bilag.csv'

VAT_CODES = {
    0: 1,
    15: 371,
    25: 10
}


class Transaction:
    def __init__(self, data, text, amount):
        # data: K-3014-25
        #       25-K-3014
        #       K-3014-40804

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

        self.text = text
        self.amount_positive = get_num(amount)
        self.netto_positive = round(self.amount_positive / (1 + self.vat / 100.0), 2)

        self.modifier = -1 if self.type == 'K' else 1
        self.amount = self.amount_positive * self.modifier


class GenerateCSV:
    CSV_INDEX_BNR = 1
    CSV_INDEX_BDATE = 2
    CSV_INDEX_BPERIOD = 4
    CSV_INDEX_BYEAR = 5
    CSV_INDEX_ACCOUNT = 6
    CSV_INDEX_VAT = 7
    CSV_INDEX_NETTO = 8
    CSV_INDEX_DESC1 = 20
    CSV_INDEX_DESC2 = 21
    CSV_INDEX_PROJECT = 23
    CSV_INDEX_CALC_VAT = 26
    CSV_INDEX_BRUTTO = 27

    csv_default_line = [
        'GBAT10',
        '',  # 1 = bilagsnr
        '',  # 2 = bilagsdato (yyyymmdd)
        '6',  # bilagstype (6 = kasse, 9 = diverse)
        '',  # 4 = periode
        '',  # 5 = regnskapsår
        '',  # 6 = konto
        '',  # 7 = mva (1 = ingen, 30 = 25 % utgående, 371 = 15 % utgående)
        '',  # 8 = saldo (netto, altså uten evt. mva)
        '0',  # kundenr
        '0',  # leverandørnr
        '',  # kontaktnavn
        '',  # adresse
        '',  # postnr
        '',  # poststed
        '',  # fakturanr
        '',  # kid
        '0',  # forfallsdato
        '',  # (not in use)
        '',  # bankkonto
        '',  # 20 = beskrivelse hovedbok
        '',  # 21 = beskrivelse reskontro
        '0',  # rentefakturering
        '0',  # 23 = prosjekt
        '1',  # avdeling
        '0',  # betalingsbetingelse
        'T',  # 26 = brutto? (T = bruk neste beløp i kombinasjon med MVA, F = ikke beregn MVA)
        '',  # 27 = bruttosum
        ''  # ekstra felt for å sikre semikolon på slutten
    ]

    def __init__(self, cyb, output_handle):
        self.nextId = cyb.nextId
        self.cyb = cyb
        self.csv = csv.writer(output_handle, delimiter=';', quoting=csv.QUOTE_NONE)

    # def get_buffer(self):
    #    if self.useFile:
    #        raise Exception("Can not get buffer for file writing")
    #    return self.csv_f

    def add_z(self, z):
        znr = z.get_z_nr()

        for item in z.get_lines():
            # TODO: validate account
            # TODO: validate VAT

            vat_code = VAT_CODES[item.vat]

            line = list(self.csv_default_line)
            line[self.CSV_INDEX_BNR] = self.nextId - LEDGER_SERIES
            line[self.CSV_INDEX_BDATE] = z.date
            line[self.CSV_INDEX_BPERIOD] = z.period
            line[self.CSV_INDEX_BYEAR] = self.cyb.year
            line[self.CSV_INDEX_ACCOUNT] = item.account
            line[self.CSV_INDEX_VAT] = vat_code
            line[self.CSV_INDEX_NETTO] = item.netto_positive * item.modifier
            line[self.CSV_INDEX_DESC1] = "%s %s" % (znr, item.text)
            line[self.CSV_INDEX_DESC2] = line[self.CSV_INDEX_DESC1]
            line[self.CSV_INDEX_PROJECT] = item.project
            line[self.CSV_INDEX_CALC_VAT] = 'T'
            line[self.CSV_INDEX_BRUTTO] = item.amount

            self.csv.writerow(line)

        self.nextId += 1


class Z:
    """
    En Z identifiserer en versjon av et oppgjør. Ett oppgjør kan potensielt ha flere versjoner av rapporter
    dersom det f.eks. opprettes korrigert rapport.
    """

    def __init__(self, data):
        self.zindex = None
        self.group = None
        self.data = data
        self.selected = False

        self.sales = self.get_sales_or_debet(data['sales'])
        self.debet = self.get_sales_or_debet(data['debet'])
        self.is_mamut = self.is_mamut()

        self.date = self.get_date()
        self.period = int(self.date[4:6])

        self.index = -1
        self.subindex = -1
        self.json_index = None

    def get_sales_or_debet(self, data):
        ret = []
        for item in data:
            transaction = Transaction(item[0], item[1], item[2])
            if self.is_mamut:
                Transform.apply(transaction)
            ret.append(transaction)
        return ret

    def is_mamut(self):
        # assume old format (Mamut) if no projects are known
        for item in self.sales + self.debet:
            if item.project != 0:
                return False
        return True

    def get_date(self):
        """Konverter 'Tirsdag dd.mm.yyyy' til 'yyyymmdd'"""
        date = self.data['date'][-10:].split('.')
        date.reverse()
        return ''.join(date)

    def get_build_time(self):
        """Konverter builddate til yyyymmdd HHmm"""
        date = self.data['builddate'][:10].split('.')
        date.reverse()
        return ''.join(date) + ' ' + self.data['builddate'][11:13] + self.data['builddate'][14:16]

    def get_total_sales(self):
        z_sum = 0
        for item in self.sales:
            z_sum += item.amount
        return z_sum

    def get_z_nr(self):
        """Generer tekstversjon av Z-nr"""
        return ('Z%s' % self.data['z']) if str(self.data['z']).isdigit() else self.data['z']

    def validate_z(self):
        """Sjekker om kredit og debet går opp i hverandre"""
        z_sum = 0
        for item in self.sales + self.debet:
            z_sum += item.amount

        return z_sum == 0

    def get_lines(self):
        return self.sales + self.debet

    def get_deviation(self):
        for line in self.get_lines():
            if line.account == DEVIATION_ACCOUNT:
                return line.amount_positive
        return 0


class ZGroup:
    """
    En ZGroup representerer en samling av rapporter for samme Z-rapport, som regel identifisert utifra
    sheetId eller tilsvarende.
    """

    def __init__(self, sid):
        self.groupindex = None
        self.sid = sid
        self.zlist = []
        self.date = None

    def add(self, z):
        self.zlist.append(z)
        self.zlist.sort(key=lambda x: x.get_build_time(), reverse=True)
        self.date = z.get_date()
        z.group = self

    def is_selected(self):
        for z in self.zlist:
            if z.selected:
                return True
        return False


class CYBTripletexImport:
    def __init__(self, json_file):
        self.json_file = json_file
        self.nextId = 1
        self.year = 2015
        self.json = None  # initialized by loadJSON
        self.data = None  # initialized by loadJSON
        self.zgroups = None  # initialized by loadJSON
        self.selected = []  # initialized by loadJSON
        self.tripletex = TripletexImporter()

    def load_json(self, show_all=False):
        f = open(self.json_file, 'r')
        self.json = json.loads(f.read(), 'utf-8')['list']
        f.close()

        # lets parse it
        self.data = {}
        self.zgroups = {}
        self.selected = []
        item_i = -1
        for item in self.json:
            item_i += 1

            if not show_all and 'import_hide' in item and item['import_hide']:
                continue

            z = Z(item)
            z.json_index = item_i

            sid = item['sheetid']
            if sid not in self.zgroups:
                self.zgroups[sid] = ZGroup(sid)

            zgroup = self.zgroups[sid]
            zgroup.add(z)

        # sort it by date (and convert to list)
        self.zgroups = sorted(self.zgroups.values(), key=lambda x: x.date + x.zlist[0].get_z_nr())

        # store indexes
        groupi = 0
        for zgroup in self.zgroups:
            zgroup.groupindex = groupi
            zi = 0
            for z in zgroup.zlist:
                z.zindex = zi
                zi += 1
            groupi += 1

    def generate_csv(self, output_handle):
        writer = GenerateCSV(self, output_handle=output_handle)
        for z in self.selected:
            writer.add_z(z)

    def export_selected(self, import_csv=False):
        """Eksporter Z-rapporter som ligger i self.selected"""
        if len(self.selected) == 0:
            return None

        exported = []

        if import_csv:
            output_handle = io.StringIO()
            self.generate_csv(output_handle)
            self.tripletex.import_gbat10(output_handle.getvalue())
        else:
            output_handle = open(DATA_FILE_OUT, 'w', encoding="iso-8859-1")
            self.generate_csv(output_handle)
            output_handle.close()

        self.nextId += len(self.selected)

        for z in self.selected:
            z.selected = False
            exported.append(z)
        self.selected = []

        return exported

    def get_z(self, index, subindex):
        return self.zgroups[index].zlist[subindex or 0]

    def add_z(self, z):
        self.selected.append(z)
        z.selected = True

    def pop_z(self):
        z = self.selected.pop()
        z.selected = False
        return z

    def set_hidden(self, zlist):
        """Skjul Z-rapporter fra lista"""
        with open(self.json_file, 'r') as f:
            data = json.loads(f.read(), 'utf-8')

        for z in zlist:
            z.data['import_hide'] = time.time()
            data['list'][z.json_index]['import_hide'] = z.data['import_hide']

        with open(self.json_file, 'w') as f:
            json.dump(data, f)
