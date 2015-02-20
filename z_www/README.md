# Z-rapporter i CYB
Denne mappen inneholder scripts som brukes for håndtering av kasseoppgjør i Escape (for CYB).

Systemet er laget av kasserer Henrik Steen.

## Generering av PDF
1. Alle z-rapporter fra kassa slås inn i et regneark i Google Docs.
2. Scripts i Google Docs eksporterer dette til JSON som sendes til ```retrieve.py```.
3. Scriptet ```retrieve.py``` genererer en LaTeX-fil med inndataen, som så genererer PDF-filen som kan printes ut.

## Generering av bilagslinjer til Mamut
1. Ved mottak i ```retrieve.py``` lagres dataen også i ```reports.json```.
2. Scriptet ```mamut.py``` lister opp alle rapportene i ```reports.json``` og lar brukeren velge hvilke det skal genereres bilagslinjer for.
3. Filen ```bilag.csv``` blir så generert og kan importeres direkte i Mamut.

