# Importering av kasseoppgjør

Dette repoet tilbyr en CLI for å importere kasseoppgjør for CYB.

Når kasseoppgjør genereres ved hjelp av Google Disk
[forklart i eget dokument](https://github.com/cybernetisk/z-backend)
vil dataen bli lagret i en fil som heter ```reports.json``` i en egen mappe.
denne filen brukes til å generere import til Tripletex.

Normalt bør derfor dette kjøre på samme maskin som z-backend gjør,
slik at filen holdes i sync mellom applikasjonene.

## Oppsett

Bygg Docker-containeren

`./build.sh`

Opprett filen `settings.py` med Tripletex-info

```python
contextId = 12345  # finn denne i URL-ene til sidene i Tripletex
```

Gjør `reports.json` tilgjenglig i denne mappa

```bash
ln -s /adresse/til/reports.json reports.json
```

## Start importeringsveilederen

`./shell.sh`

Scriptet leser nå `reports.json` filen. Importerte oppgjør markeres som
skjult så de ikke kommer opp igjen.

Følg veiledningen på skjermen for hvordan det brukes. Hvis importering direkte
til Tripletex feiler av annen grunn enn feil i dataen kan man også generere fil
som kan lastes opp manuelt.

Problemer? Spør på [Slack](https://cybernetisk.slack.com/archives/it)
