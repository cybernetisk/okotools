# Tripletex-integrasjon for CYB

CYB benytter regnskapssystemet Tripletex fra og med høst 2015.
Denne mappen inneholder abstraksjoner på toppen av Tripletex API
for å passe de behovene vi har.

Se også https://confluence.cyb.no/display/okonomi/Tripletex+API for mer info rundt API-et.

## Teste lokalt

Sørg for at du har Python 3 installert.

Filen `settings_local.py` må settes opp. Se `tripletex/settings.py` for mulige innstillinger.

For å installere og kjøre tester:

```bash
cd okotools
python -m venv .venv
source .venv/bin/activate
cd tripletex
pip install -e ".[dev]"
pytest
```
