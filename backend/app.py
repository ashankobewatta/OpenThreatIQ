# backend/app.py
from flask import Flask, jsonify, render_template
from utils import fetch_cves

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def index():
    cves = fetch_cves()  # Auto-update if cache is old
    return render_template("index.html", cves=cves)

@app.route("/api/cves")
def api_cves():
    cves = fetch_cves()
    return jsonify(cves)

if __name__ == "__main__":
    app.run(debug=True)
