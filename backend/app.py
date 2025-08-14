from flask import Flask, jsonify, render_template
from utils import fetch_cves
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Initial fetch
fetch_cves()

# Background scheduler to refresh cache every 24 hours
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_cves, 'interval', hours=24)
scheduler.start()

@app.route("/")
def index():
    cves = fetch_cves()
    return render_template("index.html", cves=cves)

@app.route("/api/cves")
def api_cves():
    cves = fetch_cves()
    return jsonify(cves)

if __name__ == "__main__":
    try:
        app.run(debug=True)
    finally:
        scheduler.shutdown()
