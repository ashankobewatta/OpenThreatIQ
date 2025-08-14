from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, get_all_cves, add_custom_feed

app = Flask(__name__)

# Default cache expiry (minutes)
DEFAULT_CACHE_MINUTES = 30

@app.route("/")
def index():
    cves = get_all_cves()
    return render_template("index.html", cves=cves)

@app.route("/api/cves")
def api_cves():
    cves = get_all_cves()
    return jsonify(cves)

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.json
    name = data.get("name")
    url = data.get("url")
    ftype = data.get("type", "Update")
    if not name or not url:
        return jsonify({"message": "Missing name or url"}), 400
    add_custom_feed(name, url, ftype)
    return jsonify({"message": "Feed added"}), 201

@app.route("/api/update_cache")
def api_update_cache():
    minutes = request.args.get("minutes", default=DEFAULT_CACHE_MINUTES, type=int)
    fetch_all_feeds(cache_expiry_minutes=minutes)
    return jsonify({"message": f"Cache refreshed with {minutes} minutes expiry"}), 200

if __name__ == "__main__":
    fetch_all_feeds(cache_expiry_minutes=DEFAULT_CACHE_MINUTES)  # initial cache on startup
    app.run(debug=True)
