from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, mark_read, get_cache_interval, set_cache_interval, add_user_feed, init_db, get_all_threats

app = Flask(__name__)
init_db()

# Update feeds on startup
fetch_all_feeds()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/threats")
def api_threats():
    return jsonify(get_all_threats())

@app.route("/api/mark_read/<threat_id>", methods=["GET"])
def api_mark_read(threat_id):
    mark_read(threat_id)
    return jsonify({"status": "ok"})

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.json
    url = data.get("url")
    source = data.get("source")
    ttype = data.get("type")
    if url and source and ttype:
        add_user_feed(url, source, ttype)
        fetch_all_feeds()
        return jsonify({"status": "added"})
    return jsonify({"status": "error", "message": "Missing parameters"}), 400

@app.route("/api/cache_interval", methods=["GET", "POST"])
def api_cache_interval():
    if request.method == "POST":
        minutes = int(request.json.get("minutes", 30))
        set_cache_interval(minutes)
        return jsonify({"status": "ok", "minutes": minutes})
    else:
        return jsonify({"minutes": get_cache_interval()})

if __name__ == "__main__":
    app.run(debug=True)
