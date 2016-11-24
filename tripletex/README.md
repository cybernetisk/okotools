# Tripletex-integrasjon for CYB
CYB benytter regnskapssystemet Tripletex fra og med høst 2015. Tripletex har et eget API,
men dette er så pass mangelfullt at det ikke egner seg til bruk av oss. Denne mappen inneholder imidlertid
scripts som bruker de vanlige sidene for å laste opp bilag og hente ut data. Dette er ikke
garantert å være like stabilt som hvis vi kunne benyttet et API.

Se også https://confluence.cyb.no/display/okonomi/Tripletex+API for mer info rundt API-et.

Ved bruk av scriptene her blir man spurt om brukernavn og passord til Tripletex, slik
at den kan logge på med en personlig bruker.

## Krav
Må ha følgende på systemet:
* Python3
* Python3-pakker: `pip3 install --user requests beautifulsoup4`
* (Kan også skrive `pip3 install --user -r requirements.txt` - sløyf `--user` hvis i virtualenv)

Filen `settings_local.py` må settes opp. Se `settings.py` for mulige innstillinger.

## Hente ut kontoplan, prosjektoversikt og rapporter
Vi bruker også disse scriptene for å hente ut kontoplan, prosjektoversikt, resultatregnskap for
driftsprosjektet og overordnet resultatregnskap for alle prosjekter.

Dette gjøres ved å kjøre:

```bash
./reports.py
```

Juster innstillinger i reports.py etter eget ønske.
