from flask import Flask, Response
app = Flask(__name__)

import sys

sys.path.append('/usr/src/tripletex')
import fetch_budget_data
import fetch_tripletex_data

@app.route("/api/fetch-budget")
def fetch_budget():
    return Response(fetch_budget_data.run(), mimetype='text/plain')

@app.route("/api/fetch-accounting")
def fetch_accounting():
    return Response(fetch_tripletex_data.run(), mimetype='text/plain')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
