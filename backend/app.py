from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, mark_read, add_user_feed, set_cache_interval, get_cache_interval

app = Flask(__name__)

@app.route("/")
def index():
    threats = fetch_all_feeds()
    return render_template("index.html", threats=threats, cache_interval=get_cache_interval())

@app.route("/api/threats")
def api_threats():
    threats = fetch_all_feeds()
    return jsonify(threats)

@app.route("/api/mark_read", methods=["POST"])
def api_mark_read():
    tid = request.json.get("id")
    if tid:
        mark_read(tid)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.json
    url = data.get("url")
    source = data.get("source")
    ttype = data.get("type")
    if url and source and ttype:
        add_user_feed(url, source, ttype)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/api/cache_interval", methods=["POST"])
def api_cache_interval():
    minutes = request.json.get("minutes")
    if minutes:
        set_cache_interval(int(minutes))
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    app.run(debug=True)
