from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, mark_read, add_user_feed, set_cache_interval

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cves")
def api_cves():
    data = fetch_all_feeds()
    return jsonify(data)

@app.route("/api/mark_read/<string:tid>", methods=["POST"])
def api_mark_read(tid):
    mark_read(tid)
    return jsonify({"status": "ok"})

@app.route("/api/add_feed", methods=["POST"])
def api_add_feed():
    data = request.json
    add_user_feed(data.get("url"), data.get("source"), data.get("type"))
    return jsonify({"status": "ok"})

@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache_interval():
    data = request.json
    minutes = int(data.get("minutes", 30))
    set_cache_interval(minutes)
    return jsonify({"status": "ok", "minutes": minutes})

if __name__ == "__main__":
    app.run(debug=True)
