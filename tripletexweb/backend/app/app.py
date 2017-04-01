from flask import Flask, Response, request, send_from_directory
from flask_cors import CORS
app = Flask(__name__)

CORS(
  app,
  origins=('http://localhost:3000', 'http://localhost:8050'),
  supports_credentials=True
)

import html
import sys
import os.path

sys.path.append('/usr/src/tripletex')
import fetch_budget_data
import fetch_tripletex_data

if not os.path.isfile('/usr/src/tripletex/settings_local.py'):
  print('Missing settings file!')
  print('You should volume mount a file to /usr/src/tripletex/settings_local.py')
  print('See https://github.com/cybrairai/okotools/blob/master/tripletex/settings.py as a template')
  sys.exit(1)

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
    drop_cache = False
    if 'drop_cache' in request.args:
        drop_cache = True
    return get_output('Oppdatering av regnskapsdata', fetch_tripletex_data.run(drop_cache))

@app.route('/reports/<path:path>')
def reports(path):
    return send_from_directory('/var/okoreports/reports', path)

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.public = False
    response.cache_control.max_age = None
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
