from flask import Flask, jsonify, render_template, request
from utils import fetch_all_feeds, get_all_threats, mark_read, set_cache_interval

app = Flask(__name__)

# Fetch feeds on startup
fetch_all_feeds()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/threats")
def api_threats():
    threats = get_all_threats()
    return jsonify(threats)

@app.route("/api/mark_read", methods=["POST"])
def api_mark_read():
    tid = request.json.get("id")
    if tid:
        mark_read(tid)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No ID provided"}), 400

@app.route("/api/set_cache_interval", methods=["POST"])
def api_set_cache_interval():
    minutes = request.json.get("minutes")
    if minutes:
        set_cache_interval(int(minutes))
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No minutes provided"}), 400

if __name__ == "__main__":
    app.run(debug=True)
