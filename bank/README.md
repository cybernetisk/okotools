# Bankbilag
CYB bruker Nordea som bank. I nettbanken henter vi ned kontoutskrifter, utbetalingskvitteringer og krediteringer (innbetalingskvitteringer). For å gjøre denne oppgaven enklere er deler av prosessen automatisert.

## Sortering av dokumenter fra banken
Se scriptet ```renamer.sh```.

Alle filer lastes ned til samme mappe, for så å kjøre dette scriptet. Scriptet identifiserer automatisk hva slags type dokument det er, gir dem nye navn og sorterer dem i riktige mapper.

## Nedlasting av utbetalingskvitteringer fra nettbanken
Her er et script for å laste ned alle PDF-er fra betalingene
utført i nettbanken. Scriptet kjøres i nettleseren.

OBS! Du må aktivere automatisk nedlasting av filer.

     I Google Chrome navngir den filer som 'kvittering (x).pdf',
     men ikke slik at x er større enn 100. Da spør den hvor
     du vil lagre filen! Last derfor ikke ned mer enn 100 filer!

1. Gå inn i nettbanken (https://nb.nordea.no) og hent liste over betalingene (da har du en oversikt med alle betalingene foran deg)
2. Merk av alle betalingene du ønsker å laste ned
3. Åpne utviklerkonsollen og kjør følgende script:

```javascript
   var interval = 2000, // tid mellom hver fil lastes ned
       elmsi = 0,
       elms = $("a[href^=paymentDetails]"),
       boxes = $("input[name=paymentsToConfirm]");
   var timer = setInterval(function(){
     while (elmsi < elms.length) {
       console.log("check "+elmsi);
       if (boxes[elmsi].checked) {
         elms[elmsi].click();
         elmsi++;
         console.log("found entry", elms[elmsi].href);
         return;
       }
       elmsi++;
     }
     clearInterval(timer);
     console.log("timer finished");
   }, interval);
```

Hvis man vil stoppe prosessen kan man skrive:

```javascript
clearInterval(timer);
```

4. Sjekk at antall filer du har fått lastet ned stemmer med antall bokser du har merket av. Det hender at ikke alle filene blir lastet ned.

