# Z-rapporter i CYB
Denne mappen inneholder scripts som brukes for håndtering av kasseoppgjør i Escape (for CYB).

Systemet er laget av Henrik Steen som var kasserer i 2014 og 2015.

## Generering av PDF
1. Alle z-rapporter fra kassa slås inn i et regneark i Google Docs.
2. Scripts i Google Docs eksporterer dette til JSON som sendes til ```retrieve.py```.
3. Scriptet ```retrieve.py``` genererer en LaTeX-fil med inndataen, som så genererer PDF-filen som kan printes ut.

## Importering til regnskapssystem
Se [egen beskrivelse](../tripletex/README.md) om dette.

## Feilsøking
Hvis man får meldingen 'Premature end of script headers: retrieve.cgi' på nettsia så er det enten feil i scriptet,
eller så er det mest sannsynlig feil tilganger. Sørg for at +x er korrekt satt!
