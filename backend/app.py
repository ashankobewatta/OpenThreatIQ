from flask import Flask, jsonify, render_template
from utils import fetch_all_feeds

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def index():
    entries = fetch_all_feeds()
    return render_template("index.html", cves=entries)

@app.route("/api/cves")
def api_cves():
    entries = fetch_all_feeds()
    return jsonify(entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
