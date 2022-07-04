# Tripletex-integrasjon for CYB

CYB benytter regnskapssystemet Tripletex fra og med høst 2015.
Denne mappen inneholder abstraksjoner på toppen av Tripletex API
for å passe de behovene vi har.

Se også https://confluence.cyb.no/display/okonomi/Tripletex+API for mer info rundt API-et.

## Teste lokalt

Sørg for at du har Python 3 installert.

Lag filen `.env` og sett følgende med riktige verdier:

```text
TRIPLETEX_CONTEXT_ID=xxx
TRIPLETEX_CUSTOMER_TOKEN=xxx
TRIPLETEX_EMPLOYEE_TOKEN=xxx
```

For å installere og kjøre tester:

```bash
cd okotools
python -m venv .venv
source .venv/bin/activate
cd tripletex
pip install -e ".[dev]"
pytest
```
