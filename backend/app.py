from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, get_db_connection
from datetime import datetime

app = Flask(__name__)

# Fetch all feeds and update cache on startup
fetch_all_feeds()

# Homepage
@app.route("/")
def index():
    return render_template("index.html")

# API: Get CVEs
@app.route("/api/cves")
def api_cves():
    conn = get_db_connection()
    cves = conn.execute("SELECT * FROM cves ORDER BY published_date DESC").fetchall()
    conn.close()
    result = []
    for c in cves:
        result.append({
            "id": c["id"],
            "description": c["description"],
            "source": c["source"],
            "type": c["type"],
            "publishedDate": c["published_date"],
            "read_flag": c["read_flag"]
        })
    return jsonify(result)

# API: Mark read/unread
@app.route("/api/mark_read", methods=["POST"])
def mark_read():
    data = request.json
    cve_id = data.get("id")
    read_flag = int(data.get("read", 1))
    conn = get_db_connection()
    conn.execute("UPDATE cves SET read_flag=? WHERE id=?", (read_flag, cve_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "id": cve_id, "read": read_flag})

# API: Set cache refresh interval (optional)
@app.route("/api/set_interval", methods=["POST"])
def set_interval():
    data = request.json
    interval = int(data.get("interval", 30))  # in minutes
    fetch_all_feeds(interval=interval)
    return jsonify({"status": "success", "interval": interval})

if __name__ == "__main__":
    app.run(debug=True)
