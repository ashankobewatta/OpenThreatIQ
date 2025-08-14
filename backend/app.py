# backend/app.py
from flask import Flask, jsonify, render_template
from utils import fetch_cves

app = Flask(app = Flask(__name__, template_folder="../frontend"))

@app.route("/")
def index():
    cves = fetch_cves()  # Auto-updates if cache is old
    return render_template("index.html", cves=cves)

@app.route("/api/cves")
def api_cves():
    cves = fetch_cves()  # Returns cached or fresh CVEs
    return jsonify(cves)

if __name__ == "__main__":
    app.run(debug=True)
