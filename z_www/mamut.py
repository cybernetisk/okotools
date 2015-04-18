#!/bin/env python
# -*- coding: utf-8 -*-
import csv
import re
import sys
from cmd import Cmd
import json
import time

class bcolors:
    RESET = '\033[0m'

    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[37m'

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

DEVIATION_ACCOUNT = '8995'

def getNum(val):
    try:
        return int(val)
    except ValueError:
        return 0

class GenerateCSV():
    def __init__(self, cyb):
        self.nextId = cyb.nextId
        self.cyb = cyb
        self.csv_f = open(DATA_FILE_OUT, 'w', encoding="iso-8859-1")
        self.csv = csv.writer(self.csv_f, delimiter=';', quoting=csv.QUOTE_NONE)

    def finish(self):
        self.csv_f.close()

    def addZ(self, z):
        znr = z.genZNr()

        for item in z.getLines():
            # TODO: validate account
            # TODO: validate VAT

            vat_code = VAT_CODES[item['vat']]

            line = list(csv_default_line)
            line[CSV_INDEX_BNR] = self.nextId
            line[CSV_INDEX_BDATE] = z.date
            line[CSV_INDEX_BPERIOD] = z.period
            line[CSV_INDEX_BYEAR] = self.cyb.year
            line[CSV_INDEX_ACCOUNT] = item['account']
            line[CSV_INDEX_VAT] = vat_code
            line[CSV_INDEX_NETTO] = item['netto']
            line[CSV_INDEX_DESC1] = "%s %s" % (znr, item['text'])
            line[CSV_INDEX_DESC2] = line[CSV_INDEX_DESC1]
            line[CSV_INDEX_CALC_VAT] = 'T'
            line[CSV_INDEX_BRUTTO] = item['amount']

            self.csv.writerow(line)

        self.nextId += 1


class Z():
    def __init__(self, data):
        self.zindex = None
        self.group = None
        self.data = data
        self.selected = False

        self.date = self.getDate()
        self.period = int(self.date[4:6])

        self.index = -1
        self.subindex = -1
        self.json_index = None

    def getDate(self):
        """Konverter 'Tirsdag dd.mm.yyyy' til 'yyyymmdd'"""
        date = self.data['date'][-10:].split('.')
        date.reverse()
        return ''.join(date)

    def getBuildTime(self):
        """Konverter builddate til yyyymmdd HHmm"""
        date = self.data['builddate'][:10].split('.')
        date.reverse()
        return ''.join(date) + ' ' + self.data['builddate'][11:13] + self.data['builddate'][14:16]

    def getTotalSales(self):
        sum = 0
        for item in self.data['sales']:
            sum += (-1 if item[0][0] == 'K' else 1) * getNum(item[2])
        return sum

    def genZNr(self):
        """Generer tekstversjon av Z-nr"""
        return ('Z%s' % self.data['z']) if str(self.data['z']).isdigit() else self.data['z']

    def validateZ(self):
        """Sjekker om kredit og debet går opp i hverandre"""
        sum = 0
        for item in self.data['sales'] + self.data['debet']:
            sum += (-1 if item[0][0] == 'K' else 1) * getNum(item[2])

        return sum == 0

    def getLines(self):
        lines = []

        for item in self.data['sales'] + self.data['debet']:
            modifier = -1 if item[0][0] == 'K' else 1
            x = {
                'text': item[1],
                'modifier': modifier,
                'account': item[0][2:6],
                'vat': 0 if len(item[0]) < 9 else getNum(item[0][7:9]),
                'amount': modifier * getNum(item[2])
            }

            x['netto'] = round(x['amount'] / (1 + x['vat']/100.0), 2)
            lines.append(x)

        return lines

    def getDeviation(self):
        for line in self.getLines():
            if line['account'] == DEVIATION_ACCOUNT:
                return line['amount']
        return 0

class ZGroup():
    def __init__(self, sid):
        self.groupindex = None
        self.sid = sid
        self.zlist = []
        self.date = None

    def add(self, z):
        self.zlist.append(z)
        self.zlist.sort(key=lambda x: x.getBuildTime(), reverse=True)
        self.date = z.getDate()
        z.group = self

    def isSelected(self):
        for z in self.zlist:
            if z.selected:
                return True
        return False


class CYBMamutImport():
    def __init__(self):
        self.nextId = 1
        self.year = 2015
        self.json = None # initialized by loadJSON
        self.zgroups = None # initialized by loadJSON
        self.selected = None # initialized by loadJSON

    def loadJSON(self, all=False):
        f = open(DATA_FILE_IN, 'r')
        self.json = json.loads(f.read(), 'utf-8')['list']
        f.close()

        # lets parse it
        self.data = {}
        self.zgroups = {}
        self.selected = []
        item_i = -1
        for item in self.json:
            item_i += 1

            if not all and 'import_hide' in item and item['import_hide']:
                continue

            z = Z(item)
            z.json_index = item_i

            sid = item['sheetid']
            if sid not in self.zgroups:
                self.zgroups[sid] = ZGroup(sid)

            zgroup = self.zgroups[sid]
            zgroup.add(z)

        # sort it by date (and convert to list)
        self.zgroups = sorted(self.zgroups.values(), key=lambda x: x.date + x.zlist[0].genZNr())

        # store indexes
        groupi = 0
        for zgroup in self.zgroups:
            zgroup.groupindex = groupi
            zi = 0
            for z in zgroup.zlist:
                z.zindex = zi
                zi += 1
            groupi += 1

    def export(self):
        """Eksporter Z-rapporter som ligger i self.selected"""
        if len(self.selected) == 0:
            return None

        exported = []

        writer = GenerateCSV(self)
        for z in self.selected:
            writer.addZ(z)
        writer.finish()

        self.nextId = writer.nextId
        for z in self.selected:
            z.selected = False
            exported.append(z)
        self.selected = []

        return exported

    def get(self, index, subindex):
        return self.zgroups[index].zlist[subindex or 0]

    def add(self, z):
        self.selected.append(z)
        z.selected = True

    def pop(self):
        z = self.selected.pop()
        z.selected = False
        return z

    def hide(self, zlist):
        """Skjul Z-rapporter fra lista"""
        with open(DATA_FILE_IN, 'r') as f:
            data = json.loads(f.read(), 'utf-8')

        for z in zlist:
            z.data['import_hide'] = time.time()
            data['list'][z.json_index]['import_hide'] = z.data['import_hide']

        with open(DATA_FILE_IN, 'w') as f:
            json.dump(data, f)


class PromptHelper():
    def __init__(self, cyb, prompt):
        self.cyb = cyb
        self.prompt = prompt

    def list_available(self):
        """Lists available reports to process"""
        print("")
        print("                             Liste over Z-rapporter")
        print("--------------------------------------------------------------------------------")

        if len(self.cyb.zgroups) == 0:
            print("No items in list")

        i = 0
        for zgroup in self.cyb.zgroups:
            ismultiple = len(zgroup.zlist) > 1
            si = 0
            for z in zgroup.zlist:
                subindex = "%d:" % si if ismultiple else "  "

                if si == 0:
                    prefix = "%2d:%s %s %-6s" % (i, subindex, zgroup.date, z.genZNr())
                else:
                    prefix = "   %-18s" % subindex

                if z.selected:
                    prefix = bcolors.GREEN + prefix
                elif si == 0:
                    prefix = bcolors.BLUE + prefix
                else:
                    prefix = bcolors.GRAY + prefix
                suffix = bcolors.RESET

                print("%s %s%7g%6g %s%s" % (prefix, z.data['builddate'], z.getTotalSales(), z.getDeviation(), z.data['type'], suffix))

                si += 1

            i += 1

    def list_selected(self, header=True):
        if len(self.cyb.selected) == 0:
            return

        if header:
            print("")
            print("             Klargjorte Z-rapporter (skriv 'pop' for å fjerne siste)")
            print("--------------------------------------------------------------------------------")
        i = self.cyb.nextId
        for z in self.cyb.selected:
            print("K%d  %s (%s)" % (i, z.genZNr(), z.data['date']))
            i += 1

    def show_help(self):
        print("")
        print("                Kommandoer:    (<x> kan også skrives som <x:y>)")
        print("--------------------------------------------------------------------------------")
        print("  add <x>   Klargjør rapport (kan sløyfe 'add' i kommandoen)")
        print("  pop       Fjern siste rapport")
        print("  save      Generer importeringsfil")
        print("  num <n>   Sett ny K-nr som første nr")
        print("  show <x>  Vis konteringer for en rapport")
        print("  hide <x>  Fjern rapport permanent fra lista")
        print("  reload    Nullstiller lister og laster data på nytt ('reload all' laster alt)")
        print("  quit      Avslutt (evt. trykk Ctrl+D)")
        print("")
        print("Trykk enter for å se status/liste/hjelp")
        print("Neste K-nr: %d" % (self.cyb.nextId + len(self.cyb.selected)))
        print("")

    def show_z_lines(self, z, knr = None):
        znr = z.genZNr()
        k = ("%sK%d%s " % (bcolors.BLUE, knr, bcolors.RESET)) if knr is not None else ""
        for line in z.getLines():
            print("%s%s: %s   %+2s%%  %6d   %s" % (k, znr, line['account'], line['vat'], line['amount'], line['text']))

class MyPrompt(Cmd):
    def __init__(self, cyb):
        Cmd.__init__(self)
        self.cyb = cyb
        self.helper = PromptHelper(cyb, self)

    def do_add(self, args):
        """Legg til en Z-rapport i genereringslista"""
        try:
            index, subindex = self.getInputIndex(args)
            z = self.cyb.get(index, subindex)

            if z.group.isSelected():
                print("FEIL: Z-rapport allerede markert")
                return

            if not z.validateZ():
                self.helper.show_z_lines(z)
                print("FEIL: Z-rapport summerer ikke til 0 (kredit+debet)")
                return

            knr = self.cyb.nextId + len(self.cyb.selected)
            self.cyb.add(z)

            print("     %s %s (%s)" % (z.genZNr(), z.data['date'], z.data['type']))
            self.helper.show_z_lines(z, knr)

            print("")
            print("Kontroller at papirskjemaet ble generert %s" % (bcolors.YELLOW + str(z.data['builddate']) + bcolors.RESET))
            print("Skriv 'pop' for å angre")

        except ValueError:
            return
        except IndexError:
            print("Indeks %s ble ikke funnet i listen" % args)

    def do_pop(self, args):
        """Fjern den siste Z-rapporten i lista"""
        if len(self.cyb.selected) == 0:
            print("Det er ingen rapporter i listen å fjerne!")
            return
        removed = self.cyb.pop()
        print("Fjernet %s (%s) fra lista" % (removed.genZNr(), removed.data['date']))

    def do_save(self, args):
        """Generer konteringslinjer for de valgte Z-rapportene"""
        print("")
        print("                        Genererer importliste for")
        print("--------------------------------------------------------------------------------")
        self.helper.list_selected(header=False)
        exported = self.cyb.export()
        if exported is None:
            print("Ingen bilag er valgt!")
            return

        print("")
        print("Fullført - %s kan nå importeres i Mamut" % DATA_FILE_OUT)
        print("")

        while True:
            sys.stdout.write("Skal vi fjerne Z-rapportene fra lista? (skriv 'hide' eller 'skip'): ")
            val = input()

            if val == 'hide' or val == 'skip':
                break

            print("Ugyldig verdi, prøv igjen")

        if val == 'hide':
            hide = []
            for z in exported:
                hide = hide + z.group.zlist
            self.cyb.hide(hide)
            self.do_reload("")

        else:
            print("")
            print("Neste K-nr: %d" % self.cyb.nextId)

    def do_show(self, args):
        """Vis konteringslinjer for en Z-rapport"""
        try:
            index, subindex = self.getInputIndex(args)
            z = self.cyb.get(index, subindex)
            self.helper.show_z_lines(z)
        except ValueError:
            return

    def do_num(self, args):
        """Vis eller sett første K-nummer"""
        if args == '':
            print("Første K-nummer: K%d" % self.cyb.nextId)
            return

        try:
            self.cyb.nextId = int(args)
            print("Første K-nummer satt til K%d" % self.cyb.nextId)
        except ValueError:
            print("Ugyldig verdi")

    def do_quit(self, args):
        """Avslutter programmet"""
        print("Avslutter")
        raise SystemExit

    def do_hide(self, args):
        """Skjul en (evt. spesifikk) Z-rapport fra lista"""
        try:
            index, subindex = self.getInputIndex(args)
            z = self.cyb.get(index, subindex)

            if subindex is None:
                self.cyb.hide(z.group.zlist)
            else:
                self.cyb.hide([z])

            print("Skjuler %s (%s) neste gang programmet lastes inn" % (z.genZNr(), z.data['date']))
            print("Skriv evt 'reload' for å gjøre dette nå")
        except ValueError:
            return

    def do_reload(self, args):
        """Laster all data på nytt"""
        self.cyb.loadJSON(all=args=='all')

        self.do_help("")
        print("Data ble lastet inn på nytt")

    def do_EOF(self, args):
        """Ctrl+D avslutter programmet"""
        self.do_quit(args)

    def default(self, args):
        """Som standard prøver vi å identifisere en Z, evt. viser vi hjelp"""
        try:
            self.getInputIndex(args, showmsg=False)
            self.do_add(args)
        except ValueError:
            self.do_help("")

    def do_help(self, args):
        """Vis liste over rapporter og hjelp"""
        self.helper.list_available()
        self.helper.list_selected()
        self.helper.show_help()

    def getNum(self):
        """Spør etter første K-nummer som skal brukes"""
        while True:
            sys.stdout.write("Nummer for neste ledige K-nummer i Mamut: ")
            num = input()

            try:
                self.cyb.nextId = int(num)
                break
            except ValueError:
                print("Ugyldig verdi, prøv igjen")

    def getInputIndex(self, args, showmsg=True):
        """Parse index:subindex"""
        r = re.compile('^(\d+)(?::(\d+))?$')
        m = r.match(args)
        if m is None:
            if showmsg:
                print("Ugyldig verdi, syntaks:")
                print("  <index>              Velg nyeste rapport av en Z")
                print("  <index>:<subindex>   Velg spesifikk rapport")
            raise ValueError

        return int(m.group(1)), int(m.group(2)) if m.group(2) is not None else None

    def emptyline(self):
        """En tom linje gir hjelp"""
        self.do_help("")

if __name__ == '__main__':
    cyb = CYBMamutImport()
    cyb.loadJSON()

    prompt = MyPrompt(cyb)

    print("--------------------------------------------------------------------------------")
    print("          Generering av importeringsfil til Mamtu for Z-rapporter")
    print("             System laget av kasserer Henrik Steen våren 2015")
    print("                 se http://github.com/cybrairai/okotools")
    print("--------------------------------------------------------------------------------")
    print("")

    prompt.getNum()

    prompt.prompt = '> '
    prompt.do_help("")
    prompt.cmdloop()
