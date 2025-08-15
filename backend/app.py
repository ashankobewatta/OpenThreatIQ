import logging
import os
from flask import Flask, render_template, jsonify, request
from utils import (
    fetch_all_feeds,
    mark_read,
    get_all_threats,
    set_cache_interval,
    add_user_feed,
    get_cache_interval,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")

# Initial fetch (cached if recent)
try:
    fetch_all_feeds(force=False)
except Exception as e:
    logging.error(f"Failed to fetch feeds on startup: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/threats")
def api_threats():
    try:
        return jsonify(get_all_threats())
    except Exception as e:
        logging.error(f"Error fetching threats: {e}")
        return jsonify({"status": "error", "message": "Could not fetch threats"}), 500

@app.route("/api/mark_read/<path:threat_id>", methods=["POST"])
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
        data = request.get_json() or {}
        minutes = int(data.get("minutes", 30))
        set_cache_interval(minutes)
        # apply immediately by refetching (force)
        fetch_all_feeds(force=True)
        return jsonify({"status": "ok", "minutes": minutes, "message": "Refresh interval updated and feed reloaded."})
    except Exception as e:
        logging.error(f"Error setting cache interval: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Force-refresh feeds, bypassing cache."""
    try:
        threats = fetch_all_feeds(force=True)
        return jsonify({"status": "ok", "message": "Feeds refreshed.", "count": len(threats)})
    except Exception as e:
        logging.error(f"Error refreshing feeds: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    try:
        data = request.get_json() or {}
        url = data.get("url")
        source = data.get("source", "Custom")
        ttype = data.get("type", "Unknown")
        if not url:
            return jsonify({"status": "error", "message": "URL required"}), 400
        add_user_feed(url, source, ttype)
        return jsonify({"status": "ok", "message": "Feed added and fetched."})
    except Exception as e:
        logging.error(f"Error adding feed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
