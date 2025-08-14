from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, mark_read, set_cache_interval, add_custom_feed, get_user_feeds

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cves")
def api_cves():
    cves = fetch_all_feeds()
    return jsonify(cves)

@app.route("/api/mark_read/<cve_id>", methods=["POST"])
def api_mark_read(cve_id):
    mark_read(cve_id)
    return jsonify({"status": "ok"})

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
    feed_type = data.get("type", "Other")
    source_name = data.get("source", "User Feed")
    if not url:
        return jsonify({"status": "error", "message": "Feed URL required"}), 400

    add_custom_feed(url, feed_type, source_name)
    return jsonify({"status": "ok"})

@app.route("/api/user_feeds")
def api_user_feeds():
    feeds = get_user_feeds()
    return jsonify(feeds)

if __name__ == "__main__":
    fetch_all_feeds()  # initial cache
    app.run(debug=True)
