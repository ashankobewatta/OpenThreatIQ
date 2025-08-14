from flask import Flask, jsonify, request, render_template
from utils import fetch_all_feeds, mark_read, add_user_feed, set_cache_interval

app = Flask(__name__)

# Homepage
@app.route("/")
def index():
    return render_template("index.html")

# API: get threats
@app.route("/api/threats")
def api_threats():
    threats = fetch_all_feeds()
    return jsonify(threats)

# API: mark read
@app.route("/api/mark_read/<threat_id>", methods=["POST", "GET"])
def api_mark_read(threat_id):
    mark_read(threat_id)
    return jsonify({"status": "ok"})

# API: add user feed
@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.json
    add_user_feed(data["url"], data["name"])
    return jsonify({"status": "ok"})

# API: set cache interval
@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache():
    data = request.json
    set_cache_interval(data["minutes"])
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
