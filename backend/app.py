from flask import Flask, jsonify, send_from_directory
import requests
import json
from utils import fetch_cves

app = Flask(__name__, static_folder="../frontend")

@app.route("/api/cves")
def get_cves():
    cves = fetch_cves()
    return jsonify(cves)

@app.route("/")
def serve_frontend():
    return send_from_directory("../frontend", "index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
