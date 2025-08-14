from flask import Flask, jsonify, render_template
from utils import fetch_all_feeds, get_all_cves

app = Flask(__name__)

@app.route("/")
def index():
    cves = get_all_cves()
    return render_template("index.html", cves=cves)

@app.route("/api/cves")
def api_cves():
    cves = get_all_cves()
    return jsonify(cves)

@app.route("/api/mark_read/<cve_id>", methods=["POST"])
def mark_read(cve_id):
    from utils import mark_cve_read
    mark_cve_read(cve_id)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Update cache on startup
    fetch_all_feeds()
    app.run(host="0.0.0.0", port=5000, debug=True)
