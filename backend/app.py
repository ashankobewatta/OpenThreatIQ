from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, add_custom_feed, get_all_cves

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

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
    if name and url:
        add_custom_feed(name, url, ftype)
        return jsonify({"status": "success"}), 201
    return jsonify({"status": "error", "message": "Missing name or url"}), 400

if __name__ == "__main__":
    fetch_all_feeds()  # update cache on startup
    app.run(debug=True)
