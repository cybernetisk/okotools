# Automatisering av utleggs og kortskjema importering i Tripletex

## Oversikt

Dette prosjektet automatiserer prosessen med å hente innsendelser fra Nettskjema, kombinere relaterte filer til en enkel PDF, og laste opp de resulterende filene til Tripletex I tillegg håndterer det autentisering og tokenadministrasjon for APIene, samt filhåndtering og konverteringsoperasjoner.

## Oppsett

### Forutsetninger

- Python 3.7 eller høyere
- `pip` for å installere Python-pakker
- Nettskjema API-legitimasjon (Klient-ID og hemmelighet)
  - Fås fra [https://authorization.nettskjema.no/client](https://authorization.nettskjema.no/client)
- Tripletex API-legitimasjon (consumerstoken og employeetoken)

### Installasjon

1. Klon repositoriet:

    ```sh
    git clone https://github.com/cybernetisk/okotools.git
    cd utleggs-og-kortskjema-automatisering
    ```

2. Opprett et virtuelt miljø:

    ```sh
    python -m venv .venv
    source venv/bin/activate  # På Windows bruk `venv\Scripts\activate`
    ```

3. Installer avhengigheter:

    ```sh
    pip install -r requirements.txt
    ```

    Det er mulig at det er noen mangler i requirements.txt filen. i så fall gjerne legg til de requirementsene som mangler :)

4. Opprett en `.env`-fil i mappen `utleggs-og-kortskjema-automatisering` og fyll den med nødvendige miljøvariabler:

    ```ini
    # Hentet fra https://authorization.nettskjema.no/client - Gir
    API_CLIENT_ID=din_nettskjema_klient_id
    API_SECRET=din_nettskjema_hemmelighet

    KORTSKJEMA_ID=din_kortskjema_id
    UTLEGGSKJEMA_ID=din_utleggskjema_id

    TRIPLETEX_CONSUMER_TOKEN=din_tripletex_forbrukstoken
    TRIPLETEX_EMPLOYEE_TOKEN=din_tripletex_ansatttoken
    ```

    KORTSKJEMA_ID og UTLEGGSKJEMA_ID er nå respektive 396301 og 393516

## Bruk

1. Kjør hovedskriptet:

    ```sh
    python main.py
    ```

2. Skriptet vil:
    - Fjerne allerede kombinerte PDFer fra mappen `kombinerte_skjemaer`.
    - Hente innsendelser fra Nettskjema.
    - Laste ned tilhørende filer og vedlegg.
    - Kombinere filer til en enkel PDF per innsendelse.
    - Laste opp PDF-en til Tripletex.
    - Slette den behandlede innsendelsen fra Nettskjema.

    Det er mulig at jeg introduserte noen feil

## Filstruktur og Forklaring

### `main.py`

Dette er hovedskriptet som orkestrerer hele arbeidsflyten. Det utfører følgende oppgaver:

- Laster miljøvariabler.
- Initialiserer kataloger og API-klienter.
- Definerer hjelpefunksjoner som `clear_output_directory`.
- Henter, behandler, kombinerer og laster opp innsendelser.
- Sletter innsendelser fra Nettskjema etter vellykket behandling.

### `nettskjema_utils.py`

Inneholder hjelpefunksjoner for å interagere med Nettskjema API, som:

- `get_submissions(form_id)`: Henter innsendelser for et gitt skjema.
- `fetch_files_for_submission(submission)`: Laster ned PDF-er og andre vedlegg for en innsendelse og konverterer dem til PDF-er hvis nødvendig.

### `nettskjema_api.py`

Inneholder lavnivåfunksjoner for å interagere direkte med Nettskjema API, og håndterer oppgaver som:

- Tokenadministrasjon (`obtain_token`, `save_token`, `load_token`, `check_and_refresh_token`).
- API-spørringer (`api_request`).
- Spesifikke endepunktinteraksjoner (`get_form_info`, `get_form_submissions`, `get_submission_pdf`, `get_submission_attachment`, etc.).

### `tripletex_utils.py`

Definerer `Tripletex`-klassen, som håndterer:

- Oppretting av session og autentisering.
- Filopplasting til Tripletex gjennom APIet.
  
### `pdf_utils.py`

Inneholder funksjoner for håndtering av PDF-er og bildebehandling:

- `convert_image_to_pdf(image_bytes, rotate_if_wide=True, image_format=None)`: Konverterer et bilde til en PDF.
- `extract_images_from_word(word_bytes)`: Ekstraherer bilder fra et Word-dokument.
- `convert_images_to_pdfs(images)`: Konverterer flere bilder til PDF-er.
- `combine_pdfs(pdf_streams output_path)`: Kombinerer flere PDF-strømmer til en enkelt PDF.

### `utils.py`

Inneholder hjelpefunksjoner for diverse oppgaver:

- `sanitize_filename(filename)`: Rensker et filnavn ved å erstatte ugyldige tegn med understreker.
