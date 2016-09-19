from flask import Flask, Response
app = Flask(__name__)

import html
import sys

sys.path.append('/usr/src/tripletex')
import fetch_budget_data
import fetch_tripletex_data

def get_output(title, data):
    ret = """<!DOCTYPE html>
<html>
  <head>
    <title>""" + html.escape(title) + """</title>
  </head>
  <body>
    <h1>""" + html.escape(title) + """</h1>
    <p><a href="../">Tilbake</a></p>
    <p><pre>""" + html.escape(data) + """</pre></p>
  </body>
</html>"""

    return Response(ret, mimetype='text/html')

@app.route("/api/fetch-budget")
def fetch_budget():
    return get_output('Oppdatering av budsjettdata', fetch_budget_data.run())

@app.route("/api/fetch-accounting")
def fetch_accounting():
    return get_output('Oppdatering av regnskapsdata', fetch_tripletex_data.run())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
