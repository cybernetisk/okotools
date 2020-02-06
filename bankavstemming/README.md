# Lage CSV for kontoutskrift til Tripletex

Gå gjennom kontoutskrift i PDF _ved bruk av Google Chrome_ og kopier
alle sidene til et tekstdokument med navn `transaksjoner.txt` som legges i
denne mappen lokalt.

Konverter denne til en riktig formatert CSV-fil:

```bash
python convert.py transaksjoner.txt <årstall> <inngående beløp> <utgående beløp>
```

Filen `out.csv` blir generert.

I Tripletex, gå til automatisk bankavstemming, last opp filen
og velg DNB (CSV) som format.

## Tekniske detaljer

For CSV filen som lastes opp til Tripletex (med DNB formatet):

- Må være i ISO-8859-1
- Må ha semikolon
- Utgående saldo må stemme

## Utvikling

Kjøring av tester:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest
pytest test.py
```
