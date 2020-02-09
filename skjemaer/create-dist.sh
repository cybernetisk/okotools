#!/bin/bash
set -eu

rm -rf dist
mkdir dist

echo '<meta charset="utf-8">' >dist/index.html
echo '<h1>Skjemaer</h1>' >>dist/index.html
echo '<p>Se <a href="alle/">cyb.no/okonomi/skjemaer/alle/</a> for alle skjemaer.</p>' >>dist/index.html
echo '<p>Skjemaer oppdateres på GitHub - se <a href="http://github.com/cybernetisk/okotools/tree/master/skjemaer">github.com/cybernetisk/okotools</a>.</p>' >>dist/index.html

cp -rp files dist/alle
cp -p www/.htaccess dist/alle/

for group_path in files/*; do
  if [ ! -d "$group_path" ] || [ -f "$group_path/.ignore_pdf" ]; then continue; fi

  group=$(basename "$group_path")

  echo "<h2>$group</h2>" >>dist/index.html

  for skjema_path in "$group_path"/*; do
    if [ ! -d "$skjema_path" ] || [ -f "$skjema_path/.ignore_pdf" ]; then continue; fi

    skjema=$(basename "$skjema_path")

    # Finn siste PDF og symlink den.
    siste_path=$(ls -1tr "$skjema_path"/*.pdf 2>/dev/null | sort -n | tail -n 1)
    if [[ "$siste_path" == "" ]]; then
      echo "Fant ingen filer i $a"
    else
      siste=$(basename "$siste_path")

      ln -s "$skjema/$siste" "dist/alle/$group/$skjema-siste.pdf"

      echo "Creating PNG for '$group/$skjema'"
      convert -resize x400 "$siste_path" "dist/$skjema.png"

      navnpdf="alle/$group/$skjema-siste.pdf"
      echo '<a href="'$navnpdf'"><img src="'$skjema'.png" style="border: 2px solid #BBB" /></a>' >>dist/index.html
    fi
  done
done
