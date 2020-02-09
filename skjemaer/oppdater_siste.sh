#!/bin/bash

chmod a+r . -R
chmod a+r alle -R
echo "NB! Alle filer i dene mappen har nå lesetilgang for alle!"

echo '<meta charset="utf-8">' >index.html
echo '<h1>Skjemaer</h1>' >>index.html
echo '<p>Se <a href="alle">cyb.no/okonomi/skjemaer/alle</a> for alle skjemaer.</p>' >>index.html

rm *.png

for x in alle/*; do
    if [ ! -d "$x" ] || [ -f "$x/.ignore_pdf" ]; then continue; fi

    echo '<h2>'$(basename "$x")'</h2>' >>index.html

    for a in "$x"/*; do
        if [ ! -d "$a" ] || [ -f "$a/.ignore_pdf" ]; then continue; fi
    
        # Finn neste PDF og symlink den
        siste=$(ls -1tr "$a"/*.pdf 2>/dev/null | tail -n 1)
        if [[ "$siste" == "" ]]; then
            echo "Fant ingen filer i $a"
        else
            navnpdf="$a-siste.pdf"
            navnpng=$(basename "$a")".png"

            if [ -h "$navnpdf" ]; then rm "$navnpdf"; fi
            sisteln=$(echo "$siste" | cut -d '/' -f 3-)

            ln -vs "$sisteln" "$navnpdf"

            convert -resize x400 "$siste"[0] "$navnpng"
            chmod go+r "$navnpng"
            echo '<a href="'$navnpdf'"><img src="'$navnpng'" style="border: 2px solid #BBB" /></a>' >>index.html
        fi

    done
done
