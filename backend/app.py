from flask import Flask, render_template, jsonify, request
from utils import fetch_all_feeds, mark_read, get_all_threats, set_cache_interval, add_user_feed, get_cache_interval
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

# On startup, fetch all feeds (update DB cache)
fetch_all_feeds()

@app.route("/")
def index():
    # Serve main dashboard page
    return render_template("index.html")

@app.route("/api/threats")
def api_threats():
    # Return all threats from DB
    threats = get_all_threats()
    return jsonify(threats)

@app.route("/api/mark_read/<threat_id>", methods=["POST"])
def api_mark_read(threat_id):
    mark_read(threat_id)
    return jsonify({"status": "ok", "id": threat_id})

@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache():
    data = request.get_json()
    minutes = int(data.get("minutes", 30))
    set_cache_interval(minutes)
    return jsonify({"status": "ok", "minutes": minutes})

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.get_json()
    url = data.get("url")
    source = data.get("source", "Custom")
    ttype = data.get("type", "Unknown")
    if url:
        add_user_feed(url, source, ttype)
        fetch_all_feeds()  # immediately fetch new feed
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "URL required"}), 400

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
