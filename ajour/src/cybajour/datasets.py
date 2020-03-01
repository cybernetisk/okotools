import pandas
import numpy as np

from cybajour.util import Col, Database, DatabaseCollection, DataSet
from cybajour.config import mappings_df, standard_prosjekt

# Usikker om vi har tabeller som holder på info om dette.
BILAG_NR = "bilag_nr"
ORDRE_NR = "ordre_nr"  # starter på 20000001

TID_REGISTRERT = "tid_registrert"
TID_OPPRETTET = "tid_opprettet"
TID_ENDRET = "tid_endret"


class Konto(DataSet):
    """
    Konto i kontoplanen.

    Feltet konto_nr er kontonummeret vi benyttet i regnskapet.

    mva_kode refererer til MvaSats
    """

    nr = "konto_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "Kontoplan", [
            # Kontonr i regnskapet, f.eks. 1900 for kontanter
            Col("KontoID", Konto.nr),
            Col("Tekst", "tekst"),
            Col("Momssats", MvaSats.id),  # None, 1, 15, 33, ...
        ])


class MvaSats(DataSet):
    """
    Oversikt over MVA-satser i bruk.
    """

    id = "mva_kode"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "Msatser", [
            Col("Momssats", MvaSats.id),
            Col("FraDato", "fra_dato"),
            Col("Sats", "mva_sats"),
            Col("Changed", TID_ENDRET),
        ])


class Betalingsmiddel(DataSet):
    """
    Betalingsmiddel. F.eks. KONTANT.
    """

    id = "betalingsmiddel_id"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "Betalingsmidler", [
            Col("ID", Betalingsmiddel.id),
            # F.eks. KONTANT
            Col("Betalingsmiddel", "navn"),
            # 6810 for "SENDE REGNING" - hvorfor?
            Col("KontoNr", Konto.nr),
        ])


class Kunde(DataSet):
    """
    Kunde.

    Kunden 1000 benyttes for å få internpris på kassa.
    """

    nr = "kunde_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "Debitor", [
            Col("DebitorID", Kunde.nr),
            # F.eks. Internpris, Navet
            Col("Firma", "kundenavn"),
            Col("Notat", "notat"),
            # F.eks. 2017-11-07 10:21:29
            Col("Oprettet", TID_OPPRETTET),
            Col("DatoChanged", TID_ENDRET),
            # Vet ikke hva dette er, men enten None eller 9900, 9930
            Col("GNr", "gnr"),
            # Antar dette styrer internpris
            Col("SalgPrisVarNr", "prisvariant"),
        ])


class Varegruppe(DataSet):
    nr = "varegruppe_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "Gruppe", [
            Col("GRUPPE", Varegruppe.nr),
            Col("TEKST", "tekst"),
            Col("Ksalg", Konto.nr),
            Col("MomsFaktor125", "pris_med_mva_multiplikator"),
            Col("MomsKode", MvaSats.id),
        ])


class Vare(DataSet):
    id = "vare_id"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "Vare", [
            Col("VAREID", Vare.id),
            Col("Gruppe", Varegruppe.nr),
            Col("TEKST", "tekst"),
            Col("KnapTekst", "tekst_knapp"),
            Col("SALG1", "pris"),
            Col("Salg2", "pris_intern"),
            Col("Notat", "notat"),
            Col("Oprettet", TID_OPPRETTET),
            Col("Changed", TID_ENDRET),
        ])


class Kvittering(DataSet):
    """
    Kvittering.

    Det er fire spesielle oppføringer her, som har ordre_nr og kvittering_nr
    lik 2, 3, 6 og 7. Disse er de eneste oppføringene med type == REKV,
    og kunde_navn er "Manuel varemodtagelse - Backoffice".
    For disse er det ikke registrert noen betalinger, men det er salgslinjer.

    For andre oppføringer:
        ordre_nr starter på 20000001
        kvittering_nr starter på 50000

    Første registrerte kvittering har dato 2018-01-24.
    """

    nr = "kvittering_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "Faklog", [
            Col("ORDRID", ORDRE_NR),
            Col("FAKTNR", Kvittering.nr),
            Col("DATO", "dato"),
            Col("BDato", "betalt_dato"),
            Col("KUNDEID", Kunde.nr),
            Col("IALT", "beloep_eks_mva"),
            Col("MOMS", "beloep_mva"),
            Col("TYPE", "type"),  # FAKT, KRED, REKV
            Col("IntRef", "bruker_navn"),
            Col("Tidspunkt", TID_REGISTRERT),
            Col("Firma", "kunde_navn"),
        ])

    def df(self):
        result = super().df()

        # Fiks betalt_dato der dette mangler og tolkes som 1899-12-30.
        d = np.datetime64('1899-12-30')
        result.loc[result["betalt_dato"] == d, "betalt_dato"] = None

        # Legg til kolonne for beløp inkl mva.
        result.insert(6, "beloep_inkl_mva", (
            result["beloep_eks_mva"] + result["beloep_mva"]
        ))

        return result


class Betaling(DataSet):
    """
    Betalinger.

    En betaling for en gitt kvittering.

    betaling_id starter på 1

    Feltet konto_nr er enten None, 1900 eller 5810. Det er kun utfylt
    der betalingsmiddel_tekst er lik RETUR eller Småindkøb. Tilsvarende
    har betalingsmiddel_tekst disse verdien kun når konto_nr er utfylt.
    Verdien 5810 ble benyttet frem til 2018-01-29, og 1900 fra og med
    2018-01-29.

    Feltet er_kredit er True der betalingsmiddel_tekst er "SENDE REGNING"
    og False i alle andre tilfeller.

    Feltet type er enten None, FAKT eller KRED. Det er kun None ved
    spesialradene neden nedenfor.

    Det er en del spesialrader her:
        1 Kontanter flyttet til kort
        2 Kontanter flyttet til kort
        1 Kort flyttet til kontanter
        2 Kort flyttet til kontanter
        1 Gavekort flyttet til kontanter
        3 Gavekort flyttet til kontanter
    Det er litt uvisst hva disse radene betyr, men det kan se ut som det
    har noe med oppgjør å gjøre.
    """

    id = "betaling_id"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "LogBetalingBon", [
            Col("ID", Betaling.id),
            Col("OrdreNr", ORDRE_NR),
            Col("Bilagsnr", Kvittering.nr),
            Col("BetalingID", Betalingsmiddel.id),
            # F.eks. BETALINGSKORT
            Col("Betalingsmiddel", "betalingsmiddel_tekst"),
            Col("KontoNr", Konto.nr),
            Col("Betalt", "beloep_betalt"),
            Col("Kredit", "er_kredit"),
            Col("Dato", "dato"),
            Col("BetDato", "bet_dato"),
            Col("Tidspunkt", TID_REGISTRERT),
            Col("Bordnr", "bord_nr"),
            Col("Saelger", "selger_navn"),
            Col("KundeNr", Kunde.nr),
            Col("LogType", "type"),
        ])

    def df(self):
        result = super().df()

        # Fiks type på kvittering_nr.
        result[Kvittering.nr] = result[Kvittering.nr].astype(int)

        return result


class Salgslinje(DataSet):
    """
    Salgslinje.

    Alle vareinnslag på kassa føres her.
    Også der hvor man har valgt kunde vil fremkomme som en spesiell rad.

    salgslinje_id starter på 1

    Feltet beloep_inkl_mva_pr og beloep_eks_mva_pr angir priser for ett stk
    av varen, og må ganges opp med antall for å få korrekt sum.
    Feltet beloep_mva_sum er derimot den totale mengden MVA.

    Feltet beloep_rabatt_inkl_mva er uvisst om gjelder pr antall eller sum,
    fordi vi p.t. kun har 1 i antall på oppføringene.

    Felt som foreløpig er uklare hva gir oss:
        bord_nr
        kode
    """

    id = "salgslinje_id"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "Statistik", [
            Col("ID", Salgslinje.id),
            Col("OrdrRek", ORDRE_NR),
            Col("FAKTNR", Kvittering.nr),
            Col("VAREID", Vare.id),
            Col("TEKST", "tekst"),
            Col("GRUPPE", Varegruppe.nr),
            Col("SOLGT", "antall_abs"),
            Col("EnHed", "enhet_tekst"),
            Col("SalgMomsYN", "beloep_inkl_mva_pr"),
            Col("SALG1", "beloep_eks_mva_pr"),
            Col("MomsBelb", "beloep_mva_sum"),
            Col("RabatBelb", "beloep_rabatt_inkl_mva"),
            Col("TYPE", "type"),  # FAKT, KRED, REKV
            Col("Dato", "dato"),
            Col("SalgsDato", "salgsdato"),
            Col("UdskTid", TID_REGISTRERT),
            Col("KundeNr", Kunde.nr),
            Col("Saelger", "selger_navn"),
            Col("Bordnr", "bord_nr"),
            Col("Kode", "kode"),  # 00, 02
        ])

    def df(self):
        result = super().df()

        # Sett antall til å være negativt ved kreditering, slik
        # at kolonnen kan summeres for å få korrekt antall.
        result["antall"] = (
            result["antall_abs"] *
            result["beloep_inkl_mva_pr"].apply(lambda x: (-1 if x < 0 else 1))
        )

        # Fjern whitespace så ikke "x " og "x" havner på forskjellige linjer.
        result["tekst"] = result["tekst"].apply(lambda x: x.strip())

        # Priser for alle antall.
        result["beloep_inkl_mva"] = result["beloep_inkl_mva_pr"] * result["antall_abs"]
        result["beloep_eks_mva"] = result["beloep_eks_mva_pr"] * result["antall_abs"]

        return result

    @staticmethod
    def utvid(salgslinje_df, varegruppe_df):
        salgslinje_utvidet_df = (
            salgslinje_df[salgslinje_df["beloep_inkl_mva"] != 0]
            .join(varegruppe_df.set_index("varegruppe_nr"), on="varegruppe_nr", rsuffix="_vg")
            .join(mappings_df.set_index("vare_id"), on="vare_id", rsuffix="_m")
        )

        salgslinje_utvidet_df["ny_konto_nr"] = salgslinje_utvidet_df["konto_nr_m"].mask(pandas.isnull, salgslinje_utvidet_df["konto_nr"])
        salgslinje_utvidet_df["ny_tekst"] = salgslinje_utvidet_df["linje_tekst"].mask(pandas.isnull, salgslinje_utvidet_df["varegruppe_nr"] + " " + salgslinje_utvidet_df["tekst_vg"])
        salgslinje_utvidet_df["ny_prosjekt"] = salgslinje_utvidet_df["prosjekt"].mask(pandas.isnull, standard_prosjekt)

        return salgslinje_utvidet_df


class Faktura(DataSet):
    """
    Faktura/regning.

    Første faktura_nr er 50812. Det er ikke løpende nr, men hoppende
    nummer. F.eks. 114276 er også i bruk.

    Det finnes en faktura_nr lik 201400001. Det ser ut som denne er
    registrert på en annen måte.

    Feltet bet_dato er i en del tilfeller datoen etter feltet dato.

    Feltet konto_nr er alltid 2400. Dette skulle trolig egnetlig
    vært 1500, da 2400 er konto vi fører vår gjeld på, ikke fordringer
    som dette.
    """

    # faktura_nr er det samme som kvittering_nr?
    nr = "faktura_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "OpostDebitor", [
            Col("Faktura", Faktura.nr),
            Col("Bilag", BILAG_NR),
            Col("DebitorID", Kunde.nr),
            Col("TFirma", "kunde_navn"),
            Col("Dato", "dato"),
            Col("BetDato", "bet_dato"),
            Col("KontoID", Konto.nr),
            Col("Vdebet", "beloep_debet"),
            Col("Vkredit", "beloep_kredit"),
            Col("Tekst", "tekst"),
        ])


class Journal(DataSet):
    """
    Journal for enkelte handlinger.

    Denne viser når det er utført (type):
        Kasseoptælling
        Kreditsalg fra kassen
        Faktura

    Verdier i navn:
        Ajour - kasse
        System administrator
        Backoffice

    Feltet journal_id er et løpenummer som begynner på 1.

    Ser ikke helt verdien av denne.
    """

    nr = "journal_nr"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "Journal", [
            Col("JournalID", Journal.nr),
            Col("Navn", "navn"),
            Col("Dato", TID_REGISTRERT),
            Col("JournalType", "type"),
        ])


class Zrapport(DataSet):
    """
    Z-rapport.

    En del rader (47) mangler bilag_nr. Betyr dette at det aldri
    er tatt skikkelig oppgjør for disse datoene?

    bilag_nr benyttes til en viss grad som Z-nr, selv om det er andre
    føringer som benytter samme nummerserie.

    Merk at for rapporter bakover i tid så mangler det også
    ZrapportLinje for disse oppføringene. På den siste åpne raden
    er det imidlertid data i ZrapportLinje med utfylt bilag_nr,
    men denne tabellen har rad med 0 og med alle felter lik 0.
    Dataen som er i ZrapportLinje inneholder kun fakturatest utført.
    """

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHDATA, "OptaellingBon", [
            Col("Dato", "dato"),
            Col("BilagNr", BILAG_NR),
            Col("Omsaetning", "sum_omsetning"),
            Col("Kort", "sum_kort"),
            Col("Kontanter", "sum_kontanter"),
            Col("KasseDiff", "sum_kassediff"),
            # Salg sendt som regning, del av omsetning, men egentlig tilhører
            # det annen bilag_nr.
            Col("KreditSalg", "sum_kreditsalg"),
            # Kontosalg - ikke del av omsetning
            Col("Acontosalg", "sum_kontosalg"),
            Col("SysKontant", "sum_kontanter_sys"),
            Col("BankBoxPoseNr", "kontanter_posenr"),
        ])

    def df(self):
        result = super().df()

        # Fjern rader fra før 2018. Uvisst hvorfor disse radene er her,
        # men alle radene har bilag_nr lik 99999.
        result = result[result["dato"].dt.year >= 2018]

        # Endre 0 til å bli None.
        result[BILAG_NR].replace({0: None}, inplace=True)

        return result


class ZrapportLinje(DataSet):
    """
    Linje i Z-rapport.

    Se forklaring i Zrapport.
    """

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.CASHREGN, "Finanstransaktion", [
            Col("Bilag", BILAG_NR),
            # ID på linje, men IKKE unik
            Col("TransID", "trans_id"),
            Col("JournalID", Journal.nr),
            Col("Faktura", Faktura.nr),
            Col("Dato", "dato"),
            Col("KontoID", Konto.nr),
            # F.eks. "Kontanter fra kasse til bank"
            Col("Tekst", "tekst"),
            Col("Debet", "beloep_debet_eks_mva"),
            Col("Kredit", "beloep_kredit_eks_mva"),
            Col("Vdebet", "beloep_debet_inkl_mva"),
            Col("Vkredit", "beloep_kredit_inkl_mva"),
            Col("SysMoms", "beloep_mva_negativt"),
            Col("TidsPunkt", TID_REGISTRERT),
            Col("DebKrNr", Kunde.nr),
            Col("TFirma", "kunde_navn"),
        ])

    def df(self):
        result = super().df()

        # Blank ut faktura_nr der dette også benyttes som bilag_nr.
        result.loc[result[Faktura.nr] == result[BILAG_NR], Faktura.nr] = -1
        result[Faktura.nr].replace({-1: None}, inplace=True)

        return result


class FinansBilagLog(DataSet):
    """
    Alle bilag, men hvor kredit og debet er ført på samme linje for mange.
    Ser ikke helt hva vi ønsker å bruke dette til.
    """

    id = "finansbilaglog_id"

    def __init__(self, dbcol: DatabaseCollection):
        super().__init__(dbcol, Database.DATAFLET, "Finans_BilagLog", [
            Col("LinieID", FinansBilagLog.id),
            Col("Bilag", BILAG_NR),
            Col("Faktura", Faktura.nr),
            Col("Dato", "dato"),
            Col("BrugerID", "bruker_id"),
            Col("Vtotal", "total"),
            Col("Dkonto", "debet_kontonr"),
            Col("Kkonto", "kredit_kontonr"),
            Col("Tekst", "tekst"),
        ])

    def df(self):
        result = super().df()

        # Fiks type på bilag_nr.
        result[BILAG_NR] = result[BILAG_NR].astype(int)

        # Fiks type på faktura_nr.
        result[Faktura.nr] = result[Faktura.nr].astype(int)

        # Blank ut faktura_nr der dette også benyttes som bilag_nr.
        result.loc[result[Faktura.nr] == result[BILAG_NR], Faktura.nr] = -1
        result[Faktura.nr].replace({-1: None}, inplace=True)

        return result
