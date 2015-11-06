# Tripletex-integrasjon for CYB
CYB benytter regnskapssystemet Tripletex fra og med høst 2015. Tripletex har et eget API
som vi dessverre ikke får tilgang til uten videre. Denne mappen inneholder imidlertid
scripts som bruker de vanlige sidene for å laste opp bilag og hente ut data. Dette er ikke
garantert å være like stabilt som hvis vi kunne benyttet API-et.

Ved bruk av scriptene her blir man spurt om brukernavn og passord til Tripletex, slik
at den kan logge på med en personlig bruker.

## Krav
Må ha følgende på systemet:
* Python3
* Python3-pakker: `pip3 install requests cookielib` (hvis nødvendig)
* BeautifulSoup4 for Python3

## Importering av kasseoppgjør
Når kasseoppgjør genereres ved hjelp av Google Disk [forklart i eget dokument](../z_www/)
vil dataen bli lagret i en fil som heter ```reports.json``` i en egen mappe. Denne filen
brukes til å generere import til Tripletex.

Det er derfor et krav å være på samme maskin som mottar oppgjørene og derav har tilgang
til ```../z_www/reports.json```-filen.

Denne filen leses av ```importer.py```-scriptet, samt at importerte oppgjør markeres som
skjult så de ikke kommer opp igjen.

For å starte importering av oppgjør kjører man enkelt bare følgende:

```bash
./importer.py
```

Følg veiledningen på skjermen for hvordan det brukes. Hvis importering direkte til Tripletex
feiler av annen grunn enn feil i dataen kan man også generere fil som kan lastes opp manuelt.

## Hente ut kontoplan, prosjektoversikt og rapporter
Vi bruker også disse scriptene for å hente ut kontoplan, prosjektoversikt, resultatregnskap for
driftsprosjektet og overordnet resultatregnskap for alle prosjekter.

Dette gjøres ved å kjøre:

```bash
./reports.py
```

Juster innstillinger i reports.py etter eget ønske.
