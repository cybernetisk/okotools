from __future__ import annotations

from cmd import Cmd
from datetime import datetime, date as ddate, timedelta
from pathlib import Path
from typing import Optional

import colorama
from pandas import DataFrame
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Preformatted, SimpleDocTemplate

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


def create_pdf(path: Path, data: str) -> None:
    styles = getSampleStyleSheet()
    styles["Code"].fontSize = 9
    styles["Code"].leftIndent = 0

    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        bottomMargin=5 * mm,
        topMargin=5 * mm,
        rightMargin=5 * mm,
        leftMargin=5 * mm,
    )

    P = Preformatted(data, styles['Code'])
    doc.build([P])


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

    def csv(self, path: Path) -> str:
        salgslinje_utvidet_df = Salgslinje.utvid(
            salgslinje_df=self._salgslinje_df(),
            varegruppe_df=self.dfcache.memoize(Varegruppe)
        )

        kunder = self.dfcache.memoize(Kunde)[["kunde_nr", "kundenavn"]]

        salgslinje_utvidet_df["kunde_nr"] = None
        salgslinje_utvidet_df.loc[salgslinje_utvidet_df["bord_nr"].str.startswith("V", na=False), "kunde_nr"] = salgslinje_utvidet_df["bord_nr"].apply(lambda v: v[1:])
        salgslinje_utvidet_df = (
            salgslinje_utvidet_df
            .join(kunder.set_index("kunde_nr"), on="kunde_nr", rsuffix="_k")
        )

        salgslinje_utvidet_df.to_csv(path)

    def _salgslinje_df(self) -> DataFrame:
        salgslinje_df = self.memoize(Salgslinje)

        # Sett aar_mnd utifra hvorvidt dette er kontosalg eller vanlig salg.
        # Dette gjør at vi tilbakeskriver kontosalg til korrekt måned, men
        # ikke annet salg som blir slått gjennom på kassa den aktuelle dagen.
        # Annet salg kan gjelde ting som har ligget i "åpne poster" og som
        # senere slås gjennom for å bli reversert. Dersom vi tilbakeskriver
        # det vil ikke reverseringen komme på samme dag som salget.
        salgslinje_df.loc[salgslinje_df["bord_nr"].str.startswith("V", na=False), "aar_mnd"] = (
            salgslinje_df["salgsdato"].dt.year.astype(str)
            + "-"
            + salgslinje_df["salgsdato"].dt.month.astype(str).str.zfill(2)
        )
        salgslinje_df.loc[~ salgslinje_df["bord_nr"].str.startswith("V", na=False), "aar_mnd"] = (
            salgslinje_df["dato"].dt.year.astype(str)
            + "-"
            + salgslinje_df["dato"].dt.month.astype(str).str.zfill(2)
        )

        return salgslinje_df

    def generate(self) -> str:
        kvittering_df = self.memoize(Kvittering)
        salgslinje_df = self._salgslinje_df()

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
            .rename(columns={
                "beloep_inkl_mva_pr_abs": "pris",
                "varegruppe_nr": "varegr",
                "prosjekt_nr": "prosjekt",
                "konto_nr": "konto",
                "mva_kode": "mva",
            })
            .groupby(["aar_mnd", "prosjekt", "konto", "mva", "varegr", "tekst_vg", "vare_id", "tekst", "pris"])[["antall", "beloep_inkl_mva", "beloep_mva"]]
            .agg("sum")
        )

        # Fiks problem med avrunding som gir tall som -8.881784e-16.
        alle_produkter["beloep_mva"] = alle_produkter["beloep_mva"].round(2)

        sum_per_varegruppe_per_dato = (
            salgslinje_utvidet_df
            .groupby(["aar_mnd", "dato", "salgsdato", "prosjekt_nr", "konto_nr", "mva_kode", "linje_tekst"])[["antall", "beloep_inkl_mva", "beloep_mva"]]
            .agg("sum")
        )
        sum_per_varegruppe_per_dato["snittbeloep_inkl_mva"] = (sum_per_varegruppe_per_dato["beloep_inkl_mva"] / sum_per_varegruppe_per_dato["antall"]).round(2)

        sum_per_varegruppe = (
            sum_per_varegruppe_per_dato
            .groupby(["prosjekt_nr", "konto_nr", "mva_kode", "linje_tekst"])
            .agg("sum")
        )
        sum_per_varegruppe["snittbeloep_inkl_mva"] = (sum_per_varegruppe["beloep_inkl_mva"] / sum_per_varegruppe["antall"]).round(2)

        sum_per_konto = (
            sum_per_varegruppe_per_dato
            .groupby(["aar_mnd", "prosjekt_nr", "konto_nr", "mva_kode"])
            .agg("sum")
        )

        sum_per_dag = (
            sum_per_varegruppe_per_dato
            .groupby(["dato"])
            .agg("sum")
        )
        sum_per_dag["snittbeloep_inkl_mva"] = (sum_per_dag["beloep_inkl_mva"] / sum_per_dag["antall"]).round(2)

        sum_per_dag_detalj = (
            sum_per_varegruppe_per_dato
            .groupby(["dato", "aar_mnd", "salgsdato"])
            .agg("sum")
        )
        sum_per_dag_detalj["snittbeloep_inkl_mva"] = (sum_per_dag_detalj["beloep_inkl_mva"] / sum_per_dag_detalj["antall"]).round(2)

        kunder = self.dfcache.memoize(Kunde)

        kontosalg = salgslinje_df[salgslinje_df["bord_nr"].str.startswith("V", na=False)].copy()
        kontosalg["kunde_nr"] = kontosalg["bord_nr"].apply(lambda v: v[1:])
        kontosalg = (
            kontosalg
            .join(kunder.set_index("kunde_nr"), on="kunde_nr", rsuffix="_k")
        )

        kontosalg_detalj = kontosalg.groupby(
            by=["bord_nr", "kundenavn", "dato", "aar_mnd", "salgsdato"]
        )[["antall", "beloep_inkl_mva", "beloep_mva"]].sum()

        kontosalg_oppsummert = kontosalg.groupby(
            by=["aar_mnd", "bord_nr", "kundenavn"]
        )[["antall", "beloep_inkl_mva", "beloep_mva"]].sum()

        kontosalg_totalt = kontosalg["beloep_inkl_mva"].sum()

        beloep_inkl_mva = sum_per_varegruppe_per_dato["beloep_inkl_mva"].sum()
        estimert_kontant_og_kort = beloep_inkl_mva - kontosalg_totalt

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
        data += "Kontant/kort:                  {:15}\n".format(estimert_kontant_og_kort)
        data += "Antall kvitteringer:           {:15}\n".format(kvittering_df.count()[0])
        data += "Antall produkter solgt:        {:15}\n".format(antall_produkter)

        data += "\n"
        data += "Salg per konto for regnskap:\n"
        data += "----------------------------\n"
        data += sum_per_konto.to_string() + "\n"

        if len(kontosalg_detalj.index) > 0:
            data += "\n"
            data += "Fakturert kontosalg (oppsummert):\n"
            data += "---------------------------------\n"
            data += kontosalg_oppsummert.to_string() + "\n"

            data += "\n"
            data += "Fakturert kontosalg (detalj):\n"
            data += "-----------------------------\n"
            data += kontosalg_detalj.to_string() + "\n"

        data += "\n"
        data += "Salg per varegruppe:\n"
        data += "--------------------\n"
        data += sum_per_varegruppe.to_string() + "\n"

        data += "\n"
        data += "Salg per dag:\n"
        data += "-------------\n"
        data += sum_per_dag.to_string() + "\n"

        data += "\n"
        data += "Salg per dag (detalj):\n"
        data += "----------------------\n"
        data += sum_per_dag_detalj.to_string() + "\n"

        data += "\n"
        data += "Produkter solgt:\n"
        data += "----------------\n"
        data += alle_produkter.to_string() + "\n"

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
        print("  salgslinjer_csv <dato> <dato> <rapportfil>")
        print("                Generere CSV-fil over alle salg for periode fra og med")
        print("                og til og med")
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
            reports = sorted(base.glob("*Z"))
            if len(reports) == 0:
                print("No reports found in '{}'".format(base))
                return
            args = next(reversed(reports)).name

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
            .groupby(["dato", "salgsdato", "prosjekt_nr", "konto_nr", "mva_kode", "linje_tekst"])[["antall", "beloep_inkl_mva", "beloep_mva"]]
            .agg("sum")
        )
        sum_per_varegruppe_per_dato["snittbeloep_inkl_mva"] = sum_per_varegruppe_per_dato["beloep_inkl_mva"] / sum_per_varegruppe_per_dato["antall"]

        print("Sum per varegruppe:")
        print(sum_per_varegruppe_per_dato.to_string())
        print()

        sum_per_konto = (
            sum_per_varegruppe_per_dato
            .groupby(["prosjekt_nr", "konto_nr"])
            .agg("sum")
        )
        sum_per_konto["snittbeloep_inkl_mva"] = sum_per_konto["beloep_inkl_mva"] / sum_per_konto["antall"]

        print("Linjer til regnskapet:")
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

        if outfile and outfile.endswith(".pdf"):
            print("Skriver til {}".format(outfile))
            create_pdf(Path(outfile), report)
        elif outfile:
            print("Skriver til {}".format(outfile))
            Path(outfile).write_text(report, encoding="utf-8")
        else:
            print(report, end="")

    def do_salgslinjer_csv(self, args):
        if not self.check_dbcol():
            return

        arglist = args.split()

        try:
            date1 = ddate.fromisoformat(arglist[0])
            date2 = ddate.fromisoformat(arglist[1])
        except Exception:
            print("Ugyldig datoer")
            return

        if len(arglist) <= 2:
            print("Mangler filnavn")
            return

        outfile = arglist[2]

        report = Rapport(self.dfcache, dato_start=date1, dato_slutt=date2)

        print("Skriver til {}".format(outfile))
        report.csv(Path(outfile))

    def do_kontosalg(self, args):
        kontosalg_df = self.dfcache.memoize(Kontosalg)
        df = kontosalg_df[kontosalg_df["beloep_inkl_mva"] != 0]
        df = df.groupby(by=["bord_nr", "salgsdato"])[["antall", "beloep_inkl_mva", "beloep_mva"]].sum()

        print("Fordelt per dag:")
        print(df.to_string())

        print()
        print("Oppsummert per konto:")
        df = df.groupby(by=["bord_nr"])[["antall", "beloep_inkl_mva", "beloep_mva"]].sum()
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
