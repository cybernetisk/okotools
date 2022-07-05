import html
import os
import sys

from dotenv import load_dotenv

import fetch_budget_data
import fetch_tripletex_data
from flask import Flask, Response, request, send_from_directory
from flask_cors import CORS

load_dotenv()

def require_env(name: str) -> str:
    value = os.environ.get(name, None)
    if value is None:
        raise RuntimeError(f"Missing {name} - please set in .env file")
    return value

context_id = int(require_env("TRIPLETEX_CONTEXT_ID"))
customer_token = require_env("TRIPLETEX_CUSTOMER_TOKEN")
employee_token = require_env("TRIPLETEX_EMPLOYEE_TOKEN")
budget_credentials_file = os.environ.get("OKOREPORTS_BUDGET_CREDENTIALS_FILE", None)
budget_spreadsheet_id = os.environ.get("OKOREPORTS_BUDGET_SPREADSHEET_ID", None)

reports_path = os.environ.get("REPORTS_DIR", os.getcwd() + "/reports/")

if not os.path.exists(reports_path):
    raise RuntimeError(f"Path {reports_path} does not exist")

app = Flask(__name__)

CORS(
    app,
    origins=('http://localhost:3000', 'http://localhost:8050'),
    supports_credentials=True
)

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
    result = fetch_budget_data.run(
        spreadsheet_id=budget_spreadsheet_id,
        credentials_file=budget_credentials_file,
        reports_path=reports_path,
    )
    return get_output('Oppdatering av budsjettdata', result)

@app.route("/api/fetch-accounting")
def fetch_accounting():
    drop_cache = False
    if 'drop_cache' in request.args:
        drop_cache = True
    result = fetch_tripletex_data.run(
        context_id=context_id,
        customer_token=customer_token,
        employee_token=employee_token,
        reports_path=reports_path,
        drop_cache=drop_cache,
    )
    return get_output('Oppdatering av regnskapsdata', result)

@app.route('/reports/<path:path>')
def reports(path):
    return send_from_directory(reports_path, path)

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    response.cache_control.public = False
    response.cache_control.max_age = 0
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
