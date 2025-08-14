from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, get_all_cves, mark_cve_read, set_cache_interval, start_background_refresh

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
def api_mark_read(cve_id):
    mark_cve_read(cve_id)
    return jsonify({"status": "ok"})

@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache_interval():
    minutes = request.json.get("minutes")
    try:
        minutes = int(minutes)
        set_cache_interval(minutes)
        return jsonify({"status": "ok", "minutes": minutes})
    except:
        return jsonify({"status": "error", "message": "Invalid value"}), 400

if __name__ == "__main__":
    fetch_all_feeds()           # Initial fetch
    start_background_refresh()  # Start auto-refresh in background
    app.run(host="0.0.0.0", port=5000, debug=True)
