from flask import Flask, render_template, jsonify, request
from utils import fetch_all_feeds, mark_read, get_all_threats, set_cache_interval, add_user_feed, get_cache_interval
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend")

# Ensure data folder exists
os.makedirs("data", exist_ok=True)

# Fetch feeds on startup
try:
    fetch_all_feeds()
except Exception as e:
    logging.error(f"Failed to fetch feeds on startup: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/threats")
def api_threats():
    try:
        threats = get_all_threats()
        return jsonify(threats)
    except Exception as e:
        logging.error(f"Error fetching threats: {e}")
        return jsonify({"status": "error", "message": "Could not fetch threats"}), 500

@app.route("/api/mark_read/<threat_id>", methods=["POST"])
def api_mark_read(threat_id):
    try:
        mark_read(threat_id)
        return jsonify({"status": "ok", "id": threat_id})
    except Exception as e:
        logging.error(f"Error marking threat {threat_id} as read: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache():
    try:
        data = request.get_json()
        minutes = int(data.get("minutes", 30))
        set_cache_interval(minutes)
        return jsonify({"status": "ok", "minutes": minutes})
    except Exception as e:
        logging.error(f"Error setting cache interval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    try:
        data = request.get_json()
        url = data.get("url")
        source = data.get("source", "Custom")
        ttype = data.get("type", "Unknown")
        if url:
            add_user_feed(url, source, ttype)
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "URL required"}), 400
    except Exception as e:
        logging.error(f"Error adding feed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
