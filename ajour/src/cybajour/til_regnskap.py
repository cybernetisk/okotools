import pandas
from datetime import date
from pathlib import Path

from cybajour.datasets import (
    Betaling,
    Faktura,
    Kvittering,
    Salgslinje,
    Zrapport,
    ZrapportLinje,
    Vare,
    Varegruppe,
)
from cybajour.util import DatabaseCollection

# pandas.set_option('display.max_columns', 300)
pandas.set_option('display.max_rows', 3000)

standard_prosjekt = "20009"  # Varer

mappings_df = pandas.DataFrame([
    {"vare_id": "600025", "linje_tekst": "Medlemsskap", "konto_nr": "3220", "prosjekt": "40041"},
    {"vare_id": "600026", "linje_tekst": "Livstidsmedlemsskap", "konto_nr": "3220", "prosjekt": "40041"},
    {"vare_id": "600148", "linje_tekst": "CYB-genser", "konto_nr": "3000", "prosjekt": "20009"},
    {"vare_id": "600149", "linje_tekst": "CYB-genser", "konto_nr": "3000", "prosjekt": "20009"},
    {"vare_id": "600058", "linje_tekst": "Hyttetur høst 2019", "konto_nr": "3290", "prosjekt": "40176"},
    {"vare_id": "600059", "linje_tekst": "Hyttetur høst 2019", "konto_nr": "3290", "prosjekt": "40176"},
    {"vare_id": "354001", "linje_tekst": "Whisky-seminar", "konto_nr": "3090", "prosjekt": "20011"},
])

datadir = Path.cwd() / "data" / "20200219-112506Z"
dbcol = DatabaseCollection(path=datadir)

dato_start = str(date(2019, 11, 1))
dato_slutt = str(date(2019, 12, 31))

# Hent alle data så det caches.
kvittering_df_all = Kvittering(dbcol).df()
betaling_df_all = Betaling(dbcol).df()
salgslinje_df_all = Salgslinje(dbcol).df()
faktura_df_all = Faktura(dbcol).df()
zrapport_df_all = Zrapport(dbcol).df()
zrapport_linje_df_all = ZrapportLinje(dbcol).df()

kvittering_df = kvittering_df_all[(kvittering_df_all["dato"] >= dato_start) & (kvittering_df_all["dato"] <= dato_slutt)].copy()
betaling_df = betaling_df_all[(betaling_df_all["dato"] >= dato_start) & (betaling_df_all["dato"] <= dato_slutt)].copy()
salgslinje_df = salgslinje_df_all[(salgslinje_df_all["dato"] >= dato_start) & (salgslinje_df_all["dato"] <= dato_slutt)].copy()
faktura_df = faktura_df_all[(faktura_df_all["dato"] >= dato_start) & (faktura_df_all["dato"] <= dato_slutt)].copy()
zrapport_df = zrapport_df_all[(zrapport_df_all["dato"] >= dato_start) & (zrapport_df_all["dato"] <= dato_slutt)].copy()
zrapport_linje_df = zrapport_linje_df_all[(zrapport_linje_df_all["dato"] >= dato_start) & (zrapport_linje_df_all["dato"] <= dato_slutt)].copy()

data = kvittering_df
data["beloep_inkl_mva"] = data["beloep_eks_mva"] + data["beloep_mva"]
sum_omsetning = data["beloep_inkl_mva"].sum()
antall_produkter = salgslinje_df[salgslinje_df["beloep_inkl_mva"] != 0]["antall"].sum()

vare_df = Vare(dbcol).df()
varegruppe_df = Varegruppe(dbcol).df()

salgslinje_utvidet_df = (
    salgslinje_df[salgslinje_df["beloep_inkl_mva"] != 0]
    .join(varegruppe_df.set_index("varegruppe_nr"), on="varegruppe_nr", rsuffix="_vg")
    .join(mappings_df.set_index("vare_id"), on="vare_id", rsuffix="_m")
)

salgslinje_utvidet_df["ny_konto_nr"] = salgslinje_utvidet_df["konto_nr_m"].mask(pandas.isnull, salgslinje_utvidet_df["konto_nr"])
salgslinje_utvidet_df["ny_tekst"] = salgslinje_utvidet_df["linje_tekst"].mask(pandas.isnull, salgslinje_utvidet_df["varegruppe_nr"] + " " + salgslinje_utvidet_df["tekst_vg"])
salgslinje_utvidet_df["ny_prosjekt"] = salgslinje_utvidet_df["prosjekt"].mask(pandas.isnull, standard_prosjekt)


# Lag liste gruppert etter produkt.
alle_produkter = (
    salgslinje_utvidet_df
    .groupby(["varegruppe_nr", "tekst_vg", "vare_id", "tekst"])[["antall", "beloep_inkl_mva", "beloep_mva_sum"]]
    .agg("sum")
    # .sort_values(by="antall", ascending=False)
)
alle_produkter["snittbeloep_inkl_mva"] = alle_produkter["beloep_inkl_mva"] / alle_produkter["antall"]

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

beloep_inkl_mva = sum_per_varegruppe_per_dato.sum()["beloep_inkl_mva"]

# Lagre data.

data = ""
data += "Periode: {} - {}\n".format(dato_start, dato_slutt)

data += "\n"
data += "Oppsummering:\n"
data += "-------------\n"
data += "Sum omsetning inkl mva:  {:15}\n".format(sum_omsetning)
data += "Antall kvitteringer:     {:15}\n".format(kvittering_df.count()[0])
data += "Antall produkter solgt:  {:15}\n".format(antall_produkter)

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

data += "\n"
data += "Kontrollsum: {}\n".format(beloep_inkl_mva)

Path("report.txt").write_text(data, encoding="utf-8")
