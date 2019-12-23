from cybajour.util import DataSet, Col

# ------------------------------------------------------------------------------
# Statiske data.
# ------------------------------------------------------------------------------

kontoplan = DataSet("Cashregn.mdb", "Kontoplan", [
    # Kontonr i regnskapet, f.eks. 1900 for kontanter
    Col("KontoID", "konto_nr"),
    Col("Tekst", "tekst"),
    Col("Momssats", "mva_kode"),  # None, 1, 15, 33, ...
])

moms_satser = DataSet("Cashregn.mdb", "Msatser", [
    Col("Momssats", "mva_kode"),
    Col("FraDato", "fra_dato"),
    Col("Sats", "mva_sats"),
    Col("Changed", "tid_endret"),  # F.eks. 2018-05-09 15:27:41
])

betalingsmidler = DataSet("Cashdata.mdb", "Betalingsmidler", [
    Col("ID", "betalingsmiddel_id"),
    Col("Betalingsmiddel", "navn"),  # F.eks. KONTANT
    Col("KontoNr", "konto_nr"),  # 6810 for "SENDE REGNING" - hvorfor?
])

# Spesielle:
#   DebitorID:1000 <= Internpris
kunder = DataSet("Cashregn.mdb", "Debitor", [
    Col("DebitorID", "kunde_nr"),
    Col("Firma", "kundenavn"),  # F.eks. Internpris, Navet
    Col("Notat", "notat"),
    Col("Oprettet", "tid_opprettet"),  # F.eks. 2017-11-07 10:21:29
    Col("DatoChanged", "tid_endret"),
    Col("GNr", "gnr"),  # Vet ikke hva dette er, men enten None eller 9900, 9930
    Col("SalgPrisVarNr", "prisvariant"),  # Antar dette styrer internpris
])

# ------------------------------------------------------------------------------
# Vareinformasjon.
# ------------------------------------------------------------------------------

varegrupper = DataSet("Cashdata.mdb", "Gruppe", [
    Col("GRUPPE", "varegruppe_nr"),
    Col("TEKST", "tekst"),
    Col("Ksalg", "konto_nr"),  # Kontonr for salg
    Col("MomsFaktor125", "pris_med_mva_multiplikator"),
    Col("MomsKode", "mva_kode"),
])

varer = DataSet("Cashdata.mdb", "Vare", [
    Col("VAREID", "vare_id"),
    Col("Gruppe", "varegruppe_nr"),
    # Col("RabatID", ""),
    # Col("PrisID", ""),
    Col("TEKST", "tekst"),
    Col("KnapTekst", "tekst_knapp"),
    Col("SALG1", "pris"),
    Col("Salg2", "pris_intern"),  # Intenrpris
    Col("Notat", "notat"),
    Col("Oprettet", "tid_opprettet"),
    Col("Changed", "tid_endret"),
])

# ------------------------------------------------------------------------------
# Salg, fakturaer osv.
# ------------------------------------------------------------------------------

# Har noe med bordsalg å gjøre?
# noe_ukjent_salgslinjer = DataSet("Cashdata.mdb", "ButikDetail_Net")

"""
Kvitteringer.

Det er fire spesielle oppføringer her, som har ordre_nr og kvittering_nr
lik 2, 3, 6 og 7. Disse er de eneste oppføringene med type == REKV,
og kunde_navn er "Manuel varemodtagelse - Backoffice".
For disse er det ikke registrert noen betalinger, men det er salgslinjer.

For andre oppføringer:
    ordre_nr starter på 20000001
    kvittering_nr starter på 50000

Første registrerte kvittering har dato 2018-01-24.
"""
kvitteringer = DataSet("Cashdata.mdb", "Faklog", [
    Col("ORDRID", "ordre_nr"),
    Col("FAKTNR", "kvittering_nr"),
    Col("DATO", "dato"),
    Col("BDato", "betalt_dato"),  # 1989-12-30 for en del data
    Col("KUNDEID", "kunde_nr"),
    Col("IALT", "beloep_eks_mva"),
    Col("MOMS", "beloep_mva"),
    Col("TYPE", "type"),  # FAKT, KRED, REKV
    Col("IntRef", "bruker_navn"),
    Col("Tidspunkt", "tid_registrert"),
    Col("Firma", "kunde_navn"),
])

"""
Betalinger.

En betaling for en gitt kvittering.

ID-er og relasjoner:
    id starter på 1
    ordre_nr starter på 20000001
    kvittering_nr refererer til tabellen kvitteringer
    betalingsmiddel_id refererer til tabellen betalingsmidler
    kunde_nr refererer til tabellen kunder

Feltet konto_nr er enten None, 1900 eller 5810. Det er kun utfylt
der betalingsmiddel_tekst er lik RETUR eller Småindkøb. Tilsvarende
har betalingsmiddel_tekst disse verdien kun når konto_nr er utfylt.
Verdien 5810 ble benyttet frem til 2018-01-29, og 1900 fra og med 2018-01-29.

Feltet er_kredit er True der betalingsmiddel_tekst er "SENDE REGNING"
og False i alle andre tilfeller.

Feltet type er enten None, FAKT eller KRED. Det er kun None ved spesialradene
neden nedenfor.

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
betalinger = DataSet("Cashdata.mdb", "LogBetalingBon", [
    Col("ID", "id"),
    Col("OrdreNr", "ordre_nr"),
    # Dette feltet er en string av ukjent grunn.
    Col("Bilagsnr", "kvittering_nr"),
    Col("BetalingID", "betalingsmiddel_id"),
    Col("Betalingsmiddel", "betalingsmiddel_tekst"),  # F.eks. BETALINGSKORT
    Col("KontoNr", "konto_nr"),
    Col("Betalt", "beloep_betalt"),
    Col("Kredit", "er_kredit"),
    Col("Dato", "dato"),
    Col("BetDato", "bet_dato"),
    Col("Tidspunkt", "tid_registrert"),
    Col("Bordnr", "bord_nr"),
    Col("Saelger", "selger_navn"),
    Col("KundeNr", "kunde_nr"),  # 1000 for internpris
    Col("LogType", "type"),
])

"""
Salgslinjer.

Alle vareinnslag på kassa føres her.
Også der hvor man har valgt kunde vil fremkomme som en spesiell rad.

ID-er og relasjoner:
    id starter på 1
    ordre_nr - se merknad på tabellen kvitteringer
    kvittering_nr refererer til tabellen kvitteringer
    varegruppe_nr refererer til tabellen varegrupper
    vare_id refererer til tabellen varer
    kunde_nr refererer til tabellen kunder

Feltet beloep_inkl_mva_pr og beloep_eks_mva_pr angir priser for ett stk
av varen, og må ganges opp med antall for å få korrekt sum.
Feltet beloep_mva_sum er derimot den totale mengden MVA.

Feltet beloep_rabatt_inkl_mva er uvisst om gjelder pr antall eller sum,
fordi vi p.t. kun har 1 i antall på oppføringene.

Felt som foreløpig er uklare hva gir oss:
    bord_nr
    kode
"""
salgslinjer = DataSet("Cashdata.mdb", "Statistik", [
    Col("ID", "id"),
    Col("OrdrRek", "ordre_nr"),
    Col("FAKTNR", "kvittering_nr"),
    Col("VAREID", "vare_id"),
    Col("TEKST", "tekst"),
    Col("GRUPPE", "varegruppe_nr"),
    Col("SOLGT", "antall"),
    Col("EnHed", "enhet_tekst"),
    Col("SalgMomsYN", "beloep_inkl_mva_pr"),
    Col("SALG1", "beloep_eks_mva_pr"),
    Col("MomsBelb", "beloep_mva_sum"),
    Col("RabatBelb", "beloep_rabatt_inkl_mva"),
    Col("TYPE", "type"),  # FAKT, KRED, REKV
    Col("Dato", "dato"),
    Col("SalgsDato", "salgsdato"),
    Col("UdskTid", "tid_registrert"),
    Col("KundeNr", "kunde_nr"),
    Col("Saelger", "selger_navn"),
    Col("Bordnr", "bord_nr"),
    Col("Kode", "kode"),  # 00, 02
])

fakturaer_posteringer = DataSet("Cashregn.mdb", "OpostDebitor", [
    Col("Faktura", "faktura_nr"),
    Col("Bilag", "bilag_nr"),
    Col("DebitorID", "kunde_nr"),
    Col("TFirma", "kunde_navn"),  # Navn på kunde
    Col("Dato", "dato"),
    Col("BetDato", "bet_dato"),  # En dag etter "Dato" i en del tilfeller
    Col("KontoID", "konto_nr"),  # Alltid 2400
    Col("Vdebet", "beloep_debet"),
    Col("Vkredit", "beloep_kredit"),
    Col("Tekst", "tekst"),
])

# ------------------------------------------------------------------------------
# Annen type registrering.
# ------------------------------------------------------------------------------

# Ser ikke helt verdien av denne.
journal = DataSet("Cashregn.mdb", "Journal", [
    # "RegnID",  # Regnskapsår. F.eks. 201801
    Col("JournalID", "journal_id"),  # Unik, begynner på 1
    # ['Ajour - kasse', 'System administrator', 'Backoffice']
    Col("Navn", "navn"),
    Col("Dato", "tid_registrert"),  # F.eks. 2018-01-25 09:45:36
    # ['Kasseoptælling', 'Kreditsalg fra kassen', 'Faktura']
    Col("JournalType", "type"),
])

# ------------------------------------------------------------------------------
# Oppgjør / Z-rapport.
# ------------------------------------------------------------------------------

# Det er noen rader før 2018 med bilag_nr 99999.
# Noen rader _mangler_ (verdi 0) bilag_nr - hva betyr dette?
zrapport = DataSet("Cashdata.mdb", "OptaellingBon", [
    Col("Dato", "dato"),
    Col("BilagNr", "bilag_nr"),  # Z-nr, fra 5000
    Col("Omsaetning", "sum_omsetning"),
    Col("Kort", "sum_kort"),
    Col("Kontanter", "sum_kontanter"),
    Col("KasseDiff", "sum_kassediff"),
    # Col("Navn", ""),
    # Col("IndsatBank", ""),
    # Col("TotalKontanter", ""),
    Col("KreditSalg", "sum_kreditsalg"),  # Litt usikker hva dette betyr
    Col("Acontosalg", "sum_kontosalg"),  # Kontosalg - ikke del av omsetning
    Col("SysKontant", "sum_kontanter_sys"),
    Col("BankBoxPoseNr", "kontanter_posenr"),
])

zrapport_linje = DataSet("Cashregn.mdb", "Finanstransaktion", [
    # En form for bilagsnr i Ajour, begynner på 5000, men en rad har 201400001
    Col("Bilag", "bilag_nr"),  # 5000 osv
    # "RegnID",  # F.eks. 201801, 201901 - regnskapsårs
    Col("TransID", "trans_id"),  # ID på linje, men IKKE unik
    Col("JournalID", "journal_id"),  # Fra 1 og opp
    # Col("Periode", ""),  # Måned, 201801, 201802 osv
    # En form for fakturanr i Ajour, samme som bilagsnr noen ganger,
    # andre ganger f.eks. 58094, 112864
    Col("Faktura", "faktura_nr"),
    Col("Dato", "dato"),  # F.eks. 2018-01-24
    Col("KontoID", "konto_nr"),  # F.eks. 5815, 5820, 5810
    Col("Tekst", "tekst"),  # F.eks. "Kontanter fra kasse til bank"
    Col("Debet", "beloep_debet_eks_mva"),  # Beløp eks MVA. F.eks. 196.0
    Col("Kredit", "beloep_kredit_eks_mva"),  # Beløp eks MVA
    Col("Vdebet", "beloep_debet_inkl_mva"),  # Beløp inkl MVA
    Col("Vkredit", "beloep_kredit_inkl_mva"),  # Beløp inkl MVA
    Col("SysMoms", "beloep_mva_negativt"),  # Beregnet MVA med negativt fortegn
    Col("TidsPunkt", "tid_registrert"),  # F.eks. 2018-01-25 09:45:36
    Col("DebKrNr", "kunde_nr"),  # Kundenr. F.eks. 1337, 1000
    Col("TFirma", "kunde_navn"),  # Navn på kunde
])

# Alle bilag, men hvor kredit og debet er ført på samme linje for mange.
# Ser ikke helt hva vi ønsker å bruke dette til.
finans_bilag_log = DataSet("DataFlet.mdb", "Finans_BilagLog", [
    Col("LinieID", "id"),
    Col("Bilag", "bilag_nr"),
    Col("Faktura", "faktura_nr"),
    Col("Dato", "dato"),
    Col("BrugerID", "bruker_id"),
    Col("Vtotal", "total"),
    Col("Dkonto", "debet_kontonr"),
    Col("Kkonto", "kredit_kontonr"),
    Col("Tekst", "tekst"),
])
