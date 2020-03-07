#!/bin/bash
set -eu

rm -rf dist
mkdir dist

cat <<EOF >dist/index.html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Skjemaer</title>
  </head>
  <body>
    <h1>Skjemaer</h1>
    <p>Se <a href="https://github.com/cybernetisk/okotools/tree/master/skjemaer/files">GitHub</a> for alle skjemaer.</p>
    <p>Skjemaer oppdateres på GitHub - se <a href="http://github.com/cybernetisk/okotools/tree/master/skjemaer">github.com/cybernetisk/okotools</a>.</p>
EOF

for group_path in files/*; do
  if [ ! -d "$group_path" ] || [ -f "$group_path/.ignore_pdf" ]; then continue; fi

  group=$(basename "$group_path")

  cat <<EOF >>dist/index.html
    <h2>$group</h2>
EOF

  for skjema_path in "$group_path"/*; do
    if [ ! -d "$skjema_path" ] || [ -f "$skjema_path/.ignore_pdf" ]; then continue; fi

    skjema=$(basename "$skjema_path")

    # Finn siste PDF og symlink den.
    siste_path=$(ls -1tr "$skjema_path"/*.pdf 2>/dev/null | sort -n | tail -n 1)
    if [[ "$siste_path" == "" ]]; then
      echo "Fant ingen filer i $skjema_path"
    else
      mkdir -p "dist/$group"
      cp -p "$siste_path" "dist/$group/$skjema-siste.pdf"

      echo "Creating PNG for '$group/$skjema'"
      convert -resize x400 "$siste_path" "dist/$group/$skjema-siste.png"

      cat <<EOF >>dist/index.html
    <a href="$group/$skjema-siste.pdf"><img src="$group/$skjema-siste.png" style="border: 2px solid #BBB" alt="$skjema" /></a>
EOF
    fi
  done
done

cat <<EOF >>dist/index.html
  </body>
</html>
EOF
