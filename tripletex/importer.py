#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from cmd import Cmd
from tripletex.z import CYBTripletexImport, DATA_FILE_OUT
from tripletex.tripletex import LedgerNumberFailed

DATA_FILE_IN = '../z_www/reports.json'


# support for ANSI color codes
try:
    import colorama

    colorama.init()
except:
    pass


class BColors:
    RESET = '\033[0m'

    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[37m'

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PromptHelper:
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
                    prefix = "%2d:%s %s %-6s" % (i, subindex, zgroup.date, z.get_z_nr())
                else:
                    prefix = "   %-18s" % subindex

                if z.selected:
                    prefix = BColors.GREEN + prefix
                elif si == 0:
                    prefix = BColors.GRAY + prefix
                else:
                    prefix = BColors.BLUE + prefix
                suffix = BColors.RESET

                print("%s %s%7g%6g %s%s" % (
                    prefix, z.data['builddate'], z.get_total_sales(), z.get_deviation(), z.data['type'], suffix))

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
            print("%d  %s (%s)" % (i, z.get_z_nr(), z.data['date']))
            i += 1

    def show_help(self):
        print("")
        print("                Kommandoer:    (<x> kan også skrives som <x:y>)")
        print("--------------------------------------------------------------------------------")
        print("  add <x>   Klargjør rapport (kan sløyfe 'add' i kommandoen)")
        print("  pop       Fjern siste rapport")
        print("  import    Importer valgte bilag til Tripletex")
        print("  save      Generer manuell importeringsfil")
        print("  num <n>   Overstyr bilagsnr for første nye bilag")
        print("  show <x>  Vis konteringer for en rapport")
        print("  hide <x>  Skjul rapport permanent fra lista (kan vises igjen med 'reload all')")
        print("  reload    Nullstiller lister og laster data på nytt")
        print("  quit      Avslutt (evt. trykk Ctrl+D)")
        print("")
        print("Trykk enter for å se status/liste/hjelp")
        print("Neste bilagsnr: %d" % (self.cyb.nextId + len(self.cyb.selected)))
        print("")

    @staticmethod
    def show_z_lines(z, knr=None):
        znr = z.get_z_nr()
        k = ("%s%d%s " % (BColors.BLUE, knr, BColors.RESET)) if knr is not None else ""
        for line in z.get_lines():
            print("%s%s: %+5s %s   %+2s%%  %6d   %s" % (
                k, znr, line.project, line.account, line.vat, line.amount, line.text))


class MyPrompt(Cmd):
    def __init__(self, cyb):
        Cmd.__init__(self)
        self.cyb = cyb
        self.helper = PromptHelper(cyb, self)

    def do_add(self, args):
        """Legg til en Z-rapport i genereringslista"""
        try:
            index, subindex = self.get_input_index(args)
            z = self.cyb.get_z(index, subindex)

            if z.group.is_selected():
                print("FEIL: Z-rapport allerede markert")
                return

            if not z.validate_z():
                self.helper.show_z_lines(z)
                print("FEIL: Z-rapport summerer ikke til 0 (kredit+debet)")
                return

            knr = self.cyb.nextId + len(self.cyb.selected)
            self.cyb.add_z(z)

            print("     %s %s (%s)" % (z.get_z_nr(), z.data['date'], z.data['type']))
            self.helper.show_z_lines(z, knr)

            print("")
            print("Kontroller at papirskjemaet ble generert %s" % (
                BColors.YELLOW + str(z.data['builddate']) + BColors.RESET))
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
        removed = self.cyb.pop_z()
        print("Fjernet %s (%s) fra lista" % (removed.get_z_nr(), removed.data['date']))

    def do_save(self, args):
        """Generer konteringslinjer for de valgte Z-rapportene"""
        print("")
        print("                        Genererer importliste for")
        print("--------------------------------------------------------------------------------")
        self.helper.list_selected(header=False)
        exported = self.cyb.export_selected()
        if exported is None:
            print("Ingen bilag er valgt!")
            return

        print("")
        print("Fullført - %s kan nå importeres" % DATA_FILE_OUT)
        print("")

        val = None
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
            self.cyb.set_hidden(hide)
            self.do_reload("")

        else:
            print("")
            print("Neste bilagsnr: %d" % self.cyb.nextId)

    def do_import(self, args):
        """Importer konteringslinjer for de valgte Z-rapportene til Tripletex"""
        print("")
        print("                        Importerer følgende bilag")
        print("--------------------------------------------------------------------------------")
        self.helper.list_selected(header=False)

        exported = self.cyb.export_selected(import_csv=True)
        if exported is None:
            print("Ingen bilag er valgt!")
            return

        print("")
        print("Fullført - alle bilag ble import til Tripletex")
        print("")

        val = None
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
            self.cyb.set_hidden(hide)
            self.do_reload("")

        else:
            print("")
            print("Neste bilagsnr: %d" % self.cyb.nextId)

    def do_show(self, args):
        """Vis konteringslinjer for en Z-rapport"""
        try:
            index, subindex = self.get_input_index(args)
            z = self.cyb.get_z(index, subindex)
            self.helper.show_z_lines(z)
        except ValueError:
            return

    def do_num(self, args):
        """Vis eller sett første bilagsnummer"""
        if args == '':
            print("Første bilagsnummer: %d" % self.cyb.nextId)
            return

        try:
            self.cyb.nextId = int(args)
            print("Første bilagsnummer satt til %d" % self.cyb.nextId)
        except ValueError:
            print("Ugyldig verdi")

    def do_quit(self, args):
        """Avslutter programmet"""
        print("Avslutter")
        raise SystemExit

    def do_hide(self, args):
        """Skjul en (evt. spesifikk) Z-rapport fra lista"""
        try:
            index, subindex = self.get_input_index(args)
            z = self.cyb.get_z(index, subindex)

            if subindex is None:
                self.cyb.set_hidden(z.group.zlist)
            else:
                self.cyb.set_hidden([z])

            print("Skjuler %s (%s) neste gang programmet lastes inn" % (z.get_z_nr(), z.data['date']))
            print("Skriv evt 'reload' for å gjøre dette nå")
        except ValueError:
            return

    def do_reload(self, args):
        """Laster all data på nytt"""
        self.cyb.load_json(show_all=args == 'all')

        self.do_help("")
        print("Data ble lastet inn på nytt")

    def do_eof(self, args):
        """Ctrl+D avslutter programmet"""
        self.do_quit(args)

    def default(self, args):
        """Som standard prøver vi å identifisere en Z, evt. viser vi hjelp"""
        try:
            self.get_input_index(args, showmsg=False)
            self.do_add(args)
        except ValueError:
            self.do_help("")

    def do_help(self, args):
        """Vis liste over rapporter og hjelp"""
        self.helper.list_available()
        self.helper.list_selected()
        self.helper.show_help()

    def get_num(self):
        """Finn første bilagsnummer som skal brukes"""
        try:
            val = self.cyb.tripletex.get_next_ledger_number(2015)  # TODO: dynamic year
            self.cyb.nextId = val
            print("Nummer for neste oppgjør: %d" % val)
        except LedgerNumberFailed:
            print("Klarte ikke å hente bilagsnr fra Tripletex")

            while True:
                sys.stdout.write("Nummer for neste ledige bilagsnummer for oppgjør i Tripletex: ")
                num = input()

                try:
                    self.cyb.nextId = int(num)
                    break
                except ValueError:
                    print("Ugyldig verdi, prøv igjen")

    @staticmethod
    def get_input_index(args, showmsg=True):
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
    cyb = CYBTripletexImport(DATA_FILE_IN)
    cyb.load_json()

    prompt = MyPrompt(cyb)

    print("--------------------------------------------------------------------------------")
    print("         Generering av importeringsfil til Tripletex for Z-rapporter")
    print("         System laget av kasserer Henrik Steen våren og høsten 2015")
    print("                 se http://github.com/cybrairai/okotools")
    print("--------------------------------------------------------------------------------")
    print("")

    prompt.get_num()

    prompt.prompt = '> '
    prompt.do_help("")
    prompt.cmdloop()
