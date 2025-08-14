from flask import Flask, jsonify, render_template
from utils import fetch_all_feeds, CACHE_FILE
import os
from datetime import datetime, timedelta

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

@app.route("/")
def index():
    print(f"[{datetime.now().isoformat()}] Loading CVEs...")
    entries = fetch_all_feeds()
    print(f"[{datetime.now().isoformat()}] Loaded {len(entries)} entries")
    return render_template("index.html", cves=entries)

@app.route("/api/cves")
def api_cves():
    entries = fetch_all_feeds()
    return jsonify(entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
