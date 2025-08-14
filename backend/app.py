from flask import Flask, jsonify, render_template
from utils import fetch_all_feeds, CACHE_FILE
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Cache update interval: 10 minutes
CACHE_UPDATE_INTERVAL = 10 * 60  # 10 minutes in seconds

def background_cache_updater():
    while True:
        try:
            print(f"[{datetime.now().isoformat()}] Running background cache update...")
            new_data = fetch_all_feeds()
            # Replace old cache with new data
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                import json
                json.dump(new_data, f, indent=2)
            print(f"[{datetime.now().isoformat()}] Cache updated successfully.")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error updating cache: {e}")
        time.sleep(CACHE_UPDATE_INTERVAL)

# Start background updater as daemon
threading.Thread(target=background_cache_updater, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cves")
def api_cves():
    import json
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cves = json.load(f)
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error loading cache: {e}")
        cves = []
    return jsonify(cves)

if __name__ == "__main__":
    print(f"[{datetime.now().isoformat()}] Starting OpenThreatIQ server...")
    # Fetch once at startup to populate cache immediately
    try:
        initial_data = fetch_all_feeds()
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            import json
            json.dump(initial_data, f, indent=2)
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Initial cache fetch failed: {e}")
    app.run(debug=True)
