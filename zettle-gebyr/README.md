# Her bor noen enkle script for å føre gebyr fra zettle

CYB benytter regnskapssystemet Tripletex og betalingsterminaler fra Zettle. Ettersom
Zettle trekker et gebyr på x% fra utbetalingene de gjør, er det nødvendig å føre disse
gebyrene daglig for å klare å lukke poster i Tripletex.

2024-09-11: Dette er veldig enkel og lite robust kode. Du vil ikke få beskjed hvis noe ikke fungerer.

2024-10-02: Nå er koden mere robust, samt refactoret til å bruke en .env fil istedenfor hardkodede verdier i egne config filer

## Env fil

Env-filen må inneholde disse feltene:

``` bash
# Tripletex nøkler/tokens fås fra wikien (eller noen i økonomigruppen som sitter med infoen)
TRIPLETEX_CONSUMER_TOKEN=<tripletex-consumer-token>
TRIPLETEX_EMPLOYEE_TOKEN=<tripletex-employee-token>
TRIPLETEX_BASE_URL=https://tripletex.no/v2

# Zettle nøkkel kan lages på https://my.zettle.com/apps/api-keys hvis du har tilgang
ZETTLE_ID=<zettle-id>
ZETTLE_SECRET=<zettle-secret>
```

## Kjøring

Krever [uv](https://docs.astral.sh/uv/). Hver kjøring fører bilag i Tripletex, så velg én av:

- Måneden en dato ligger i: `uv run main.py 2026-10-15`
- Egendefinert periode: `uv run main.py 2026-10-01 2026-10-15`
- Inneværende måned, kun på siste dag i måneden: `uv run main.py auto`
