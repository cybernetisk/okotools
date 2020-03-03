from __future__ import annotations

from cmd import Cmd
from datetime import datetime, date as ddate, timedelta
from pathlib import Path
from typing import Optional

import colorama
from pandas import DataFrame

from cybajour.datasets import (
    Betaling,
    Faktura,
    Journal,
    Kontosalg,
    Kunde,
    Kvittering,
    Salgslinje,
    Vare,
    Varegruppe,
    Zrapport,
    ZrapportLinje
)
from cybajour.util import DatabaseCollection


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


class DfCache:
    def __init__(self, dbcol: DatabaseCollection):
        self.dbcol = dbcol
        self._cache = {}

    def memoize(self, clz) -> DataFrame:
        name = clz.__name__
        if name not in self._cache:
            self._cache[name] = clz(self.dbcol).df()
        return self._cache[name]


class Rapport:
    def __init__(self, dfcache: DfCache, dato_start: ddate = None, dato_slutt: ddate = None):
        self.dfcache = dfcache
        self.dato_start = dato_start
        self.dato_slutt = dato_slutt
        self._cache = {}

    def memoize(self, clz) -> DataFrame:
        name = clz.__name__
        if name not in self._cache:
            df = self.dfcache.memoize(clz)

            if self.dato_start is not None and self.dato_slutt is not None:
                dato_start_str = str(self.dato_start)
                dato_slutt_str = str(self.dato_slutt)

                if name == Kvittering.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                elif name == Betaling.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                elif name == Salgslinje.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                elif name == Faktura.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                elif name == Journal.__name__:
                    df = df[(df["tid_registrert"].dt.date >= self.dato_start) & (df["tid_registrert"].dt.date <= self.dato_slutt + timedelta(days=1))].copy()
                elif name == Zrapport.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                elif name == ZrapportLinje.__name__:
                    df = df[(df["dato"] >= dato_start_str) & (df["dato"] <= dato_slutt_str)].copy()
                else:
                    raise ValueError("Ukjent: {}".format(name))

            self._cache[name] = df

        return self._cache[name]

    def generate(self) -> str:
        kvittering_df = self.memoize(Kvittering)
        salgslinje_df = self.memoize(Salgslinje)

        data = kvittering_df
        data["beloep_inkl_mva"] = data["beloep_eks_mva"] + data["beloep_mva"]
        sum_omsetning = data["beloep_inkl_mva"].sum()
        antall_produkter = salgslinje_df[salgslinje_df["beloep_inkl_mva"] != 0]["antall"].sum()

        varegruppe_df = self.dfcache.memoize(Varegruppe)
        salgslinje_utvidet_df = Salgslinje.utvid(
            salgslinje_df=salgslinje_df,
            varegruppe_df=varegruppe_df
        )

        # Lag liste gruppert etter produkt.
        alle_produkter = (
            salgslinje_utvidet_df
            .groupby(["varegruppe_nr", "tekst_vg", "vare_id", "tekst", "beloep_inkl_mva_pr_abs"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]]
            .agg("sum")
            # .sort_values(by="antall", ascending=False)
        )

        sum_per_varegruppe_per_dato = (
            salgslinje_utvidet_df
            .groupby(["dato", "ny_prosjekt", "ny_konto_nr", "mva_kode", "ny_tekst"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]]
            .agg("sum")
        )
        sum_per_varegruppe_per_dato["snittbeloep_inkl_mva"] = sum_per_varegruppe_per_dato["beloep_inkl_mva"] / sum_per_varegruppe_per_dato["antall"]

        sum_per_varegruppe = (
            sum_per_varegruppe_per_dato
            .groupby(["ny_prosjekt", "ny_konto_nr", "mva_kode", "ny_tekst"])
            .agg("sum")
        )
        sum_per_varegruppe["snittbeloep_inkl_mva"] = sum_per_varegruppe["beloep_inkl_mva"] / sum_per_varegruppe["antall"]

        sum_per_konto = (
            sum_per_varegruppe_per_dato
            .groupby(["ny_prosjekt", "ny_konto_nr"])
            .agg("sum")
        )
        sum_per_konto["snittbeloep_inkl_mva"] = sum_per_konto["beloep_inkl_mva"] / sum_per_konto["antall"]

        sum_per_dag = (
            sum_per_varegruppe_per_dato
            .groupby(["dato"])
            .agg("sum")
        )
        sum_per_dag["snittbeloep_inkl_mva"] = sum_per_dag["beloep_inkl_mva"] / sum_per_dag["antall"]

        kunder = self.dfcache.memoize(Kunde)

        kontosalg = salgslinje_df[salgslinje_df["bord_nr"].str.startswith("V", na=False)].copy()
        kontosalg["kunde_nr"] = kontosalg["bord_nr"].apply(lambda v: v[1:])
        kontosalg["aar"] = kontosalg["salgsdato"].dt.year
        kontosalg = (
            kontosalg
            .join(kunder.set_index("kunde_nr"), on="kunde_nr", rsuffix="_k")
        )

        kontosalg_detalj = kontosalg.groupby(
            by=["bord_nr", "kundenavn", "dato", "salgsdato"]
        )[["antall", "beloep_inkl_mva", "beloep_mva_sum"]].sum()

        kontosalg_oppsummert = kontosalg.groupby(
            by=["bord_nr", "kundenavn", "aar"]
        )[["antall", "beloep_inkl_mva", "beloep_mva_sum"]].sum()

        kontosalg_totalt = kontosalg["beloep_inkl_mva"].sum()

        beloep_inkl_mva = sum_per_varegruppe_per_dato.sum()["beloep_inkl_mva"]

        # Lagre data.

        data = ""
        data += "Periode: {} - {}\n".format(self.dato_start, self.dato_slutt)
        data += "Rapport-tidspunkt: {}\n".format(datetime.now())

        data += "\n"
        data += "Oppsummering:\n"
        data += "-------------\n"
        data += "Sum omsetning inkl mva:        {:15}\n".format(sum_omsetning)
        data += "Kontrollsum:                   {:15} (skal være lik summen over)\n".format(beloep_inkl_mva)
        data += "Fakturert kontosalg inkl mva:  {:15}\n".format(kontosalg_totalt)
        data += "Antall kvitteringer:           {:15}\n".format(kvittering_df.count()[0])
        data += "Antall produkter solgt:        {:15}\n".format(antall_produkter)

        data += "\n"
        data += "Alle produktlinjer:\n"
        data += "-------------------\n"
        data += alle_produkter.to_string() + "\n"

        data += "\n"
        data += "Salgslinjer:\n"
        data += "------------\n"
        data += sum_per_varegruppe.to_string() + "\n"

        data += "\n"
        data += "Sum per konto:\n"
        data += "--------------\n"
        data += sum_per_konto.to_string() + "\n"

        data += "\n"
        data += "Sum per dato:\n"
        data += "-------------\n"
        data += sum_per_dag.to_string() + "\n"

        if len(kontosalg_detalj.index) > 0:
            data += "\n"
            data += "Fakturert kontosalg (detalj):\n"
            data += "-----------------------\n"
            data += kontosalg_detalj.to_string() + "\n"

            data += "\n"
            data += "Fakturert kontosalg (oppsummert):\n"
            data += "---------------------------\n"
            data += kontosalg_oppsummert.to_string() + "\n"

        return data


class PromptHelper:
    def __init__(self, prompt: MyPrompt):
        self.prompt = prompt

    def show_help(self):
        print("")
        print("                Kommandoer:")
        print("--------------------------------------------------------------------------------")
        print("  db            Sett database til nyeste funnet")
        print("  db <name>     Sett database til angitt mappenavn")
        print("  z <dato>      Vis oppgjør for dato yyyy-mm-dd")
        print("  z <nr>        Vis oppgjør med angitt nr")
        print("  dato <dato>   Vis informasjon om dato")
        print("  zlist [<n>]   Vis oversikt over n siste Z, -1 for alle")
        print("  rapport <dato> <dato> [<rapportfil>]")
        print("                Generer rapport for periode fra og med og til og med")
        print("  kontosalg     Vis oppsummering for åpne kontosalg")
        print("  varegrupper   Vis alle varegrupper")
        print("  varer         Vis alle varer")
        print("  journal       Vis alle oppføringer fra journal")
        print("  kunder        Vis alle kunder")
        print("  quit          Avslutt (evt. trykk Ctrl+D)")
        print("")
        print("Trykk enter for å se hjelp")
        print("")


class MyPrompt(Cmd):
    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super().__init__(completekey, stdin, stdout)
        self.helper = PromptHelper(self)
        self.prompt = "> "
        self.dbcol: Optional[DatabaseCollection] = None
        self.dfcache: Optional[DfCache] = None

    def do_db(self, args):
        base = Path.cwd() / "data"

        if args == "":
            args = next(reversed(sorted(base.glob("*Z")))).name

        datadir = base / args
        if not datadir.exists():
            print("Not found: " + str(datadir))
            return
        elif not datadir.is_dir():
            print("Not a dir: " + str(datadir))
            return
        else:
            print("Data dir: " + str(datadir))

        self.dbcol = DatabaseCollection(path=datadir)
        self.dfcache = DfCache(self.dbcol)

    def do_z(self, args):
        if not self.check_dbcol():
            return

    def do_zlist(self, args):
        if not self.check_dbcol():
            return

        zrapport_df = self.dfcache.memoize(Zrapport)
        zrapport_df = zrapport_df.sort_values(by="dato")
        if args != "-1":
            n = 10
            if args != "":
                n = int(args)
            zrapport_df = zrapport_df[-n:]
        print(zrapport_df.to_string())

    def do_dato(self, args):
        try:
            dato_obj = ddate.fromisoformat(args)
        except Exception:
            print("Ugyldig dato")
            return

        report = Rapport(self.dfcache, dato_start=dato_obj, dato_slutt=dato_obj)

        kvittering_df = report.memoize(Kvittering)
        betaling_df = report.memoize(Betaling)
        salgslinje_df = report.memoize(Salgslinje)
        faktura_df = report.memoize(Faktura)
        journal_df = report.memoize(Journal)
        zrapport_df = report.memoize(Zrapport)
        zrapport_linje_df = report.memoize(ZrapportLinje)

        data = kvittering_df
        data["beloep_inkl_mva"] = data["beloep_eks_mva"] + data["beloep_mva"]
        sum_omsetning = data["beloep_inkl_mva"].sum()

        print("Sum omsetning inkl mva: {}".format(sum_omsetning))
        print("Antall kvitteringer: {}".format(kvittering_df.count()[0]))
        print("Antall produkter solgt: {}".format(salgslinje_df[salgslinje_df["beloep_inkl_mva"] != 0]["antall"].sum()))

        print("Journaler:")
        print(journal_df.to_string())
        print()

        print("Z-rapporter:")
        print(zrapport_df.to_string())
        print()

        print("Z-rapport linjer:")
        print(zrapport_linje_df.to_string())
        print()

        print("Fakturaer:")
        print(faktura_df.to_string())
        print()

        print("Kvitteringer:")
        print(kvittering_df.sort_values(by="tid_registrert").to_string())
        print()

        print("Betalinger:")
        print(betaling_df.sort_values(by="tid_registrert").to_string())
        print()

        print("Salgslinjer:")
        print(salgslinje_df.sort_values(by="tid_registrert").to_string())
        print()

        varegruppe_df = self.dfcache.memoize(Varegruppe)

        salgslinje_utvidet_df = Salgslinje.utvid(
            salgslinje_df=salgslinje_df,
            varegruppe_df=varegruppe_df
        )

        sum_per_varegruppe_per_dato = (
            salgslinje_utvidet_df
            .groupby(["dato", "ny_prosjekt", "ny_konto_nr", "mva_kode", "ny_tekst"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]]
            .agg("sum")
        )
        sum_per_varegruppe_per_dato["snittbeloep_inkl_mva"] = sum_per_varegruppe_per_dato["beloep_inkl_mva"] / sum_per_varegruppe_per_dato["antall"]

        print("Sum per varegruppe:")
        print(sum_per_varegruppe_per_dato.to_string())
        print()

        sum_per_konto = (
            sum_per_varegruppe_per_dato
            .groupby(["ny_prosjekt", "ny_konto_nr"])
            .agg("sum")
        )
        sum_per_konto["snittbeloep_inkl_mva"] = sum_per_konto["beloep_inkl_mva"] / sum_per_konto["antall"]

        print("Sum per konto:")
        print(sum_per_konto.to_string())

    def do_rapport(self, args):
        if not self.check_dbcol():
            return

        arglist = args.split()

        try:
            date1 = ddate.fromisoformat(arglist[0])
            date2 = ddate.fromisoformat(arglist[1])
        except Exception:
            print("Ugyldig datoer")
            return

        outfile = arglist[2] if len(arglist) > 2 else None

        report = Rapport(self.dfcache, dato_start=date1, dato_slutt=date2).generate()

        if outfile:
            print("Skriver til {}".format(outfile))
            Path(outfile).write_text(report, encoding="utf-8")
        else:
            print(report, end="")

    def do_kontosalg(self, args):
        kontosalg_df = self.dfcache.memoize(Kontosalg)
        df = kontosalg_df[kontosalg_df["beloep_inkl_mva"] != 0]
        df = df.groupby(by=["bord_nr", "salgsdato"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]].sum()

        print("Fordelt per dag:")
        print(df.to_string())

        print()
        print("Oppsummert per konto:")
        df = df.groupby(by=["bord_nr"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]].sum()
        print(df.to_string())

    def do_varegrupper(self, args):
        varegrupper_df = self.dfcache.memoize(Varegruppe)
        varegrupper_df = varegrupper_df.sort_values(by=Varegruppe.nr)
        print(varegrupper_df.to_string())

    def do_varer(self, args):
        varer_df = self.dfcache.memoize(Vare)
        varer_df = varer_df.sort_values(by=Vare.id)
        print(varer_df.to_string())

    def do_journal(self, args):
        journal_df = self.dfcache.memoize(Journal)
        journal_df = journal_df.sort_values(by="tid_registrert")
        print(journal_df.to_string())

    def do_kunder(self, args):
        kunder_df = self.dfcache.memoize(Kunde)
        kunder_df = kunder_df.sort_values(by=Kunde.nr)
        print(kunder_df[[Kunde.nr, "kundenavn", "prisvariant"]].to_string())

    def do_quit(self, args):
        """Avslutter programmet"""
        print("Avslutter")
        raise SystemExit

    def do_EOF(self, args):
        """Ctrl+D avslutter programmet"""
        self.do_quit(args)

    def default(self, args):
        self.do_help("")

    def do_help(self, args):
        self.helper.show_help()

    def emptyline(self):
        """En tom linje gir hjelp"""
        self.do_help("")

    def check_dbcol(self) -> bool:
        if self.dbcol is None:
            print("Set database by using db command first")
            return False
        return True


def main():
    colorama.init()

    # pandas.set_option('display.max_columns', 300)
    # pandas.set_option('display.max_rows', 3000)

    prompt = MyPrompt()
    prompt.do_help("")
    prompt.do_db("")
    prompt.cmdloop()
