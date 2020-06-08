import pandas

standard_prosjekt = "20009"  # Varer

mappings_df = pandas.DataFrame([
    {"vare_id": "80001", "linje_tekst": "Magic", "konto_nr": "3000", "prosjekt_nr": "40013"},
    {"vare_id": "600035", "linje_tekst": "Danskebåttur", "konto_nr": "3290", "prosjekt_nr": "40022"},
    {"vare_id": "600036", "linje_tekst": "Danskebåttur", "konto_nr": "3290", "prosjekt_nr": "40022"},
    {"vare_id": "600200", "linje_tekst": "Danskebåttur", "konto_nr": "3290", "prosjekt_nr": "40022"},
    {"vare_id": "600201", "linje_tekst": "Danskebåttur", "konto_nr": "3290", "prosjekt_nr": "40022"},
    {"vare_id": "600202", "linje_tekst": "Danskebåttur", "konto_nr": "3290", "prosjekt_nr": "40022"},
    {"vare_id": "600025", "linje_tekst": "Medlemsskap", "konto_nr": "3220", "prosjekt_nr": "40041"},
    {"vare_id": "600026", "linje_tekst": "Livstidsmedlemsskap", "konto_nr": "3220", "prosjekt_nr": "40041"},
    # NB! CYB50 hardcover ligger med feil MVA i kassa.
    {"vare_id": "600121", "linje_tekst": "CYB50 hardcover", "konto_nr": "3100", "prosjekt_nr": "40163"},
    {"vare_id": "600148", "linje_tekst": "CYB-genser", "konto_nr": "3000", "prosjekt_nr": "20009"},
    {"vare_id": "600149", "linje_tekst": "CYB-genser", "konto_nr": "3000", "prosjekt_nr": "20009"},
    {"vare_id": "600058", "linje_tekst": "Hyttetur", "konto_nr": "3290", "prosjekt_nr": "20012"},
    {"vare_id": "600059", "linje_tekst": "Hyttetur", "konto_nr": "3290", "prosjekt_nr": "20012"},
    {"vare_id": "354001", "linje_tekst": "Whisky-seminar", "konto_nr": "3090", "prosjekt_nr": "20011"},
    {"vare_id": "354002", "linje_tekst": "Whisky-seminar", "konto_nr": "3090", "prosjekt_nr": "20011"},
    {"vare_id": "354003", "linje_tekst": "Whisky-seminar", "konto_nr": "3090", "prosjekt_nr": "20011"},
    {"vare_id": "600085", "linje_tekst": "Galla", "konto_nr": "3090", "prosjekt_nr": "20010"},
])
