import requests
import feedparser
import sqlite3
import json
import gzip
import io
from datetime import datetime, timedelta
from pathlib import Path

DB_FILE = Path("data/cve_data.db")
CACHE_EXPIRY_MINUTES_DEFAULT = 30

# -----------------------------
# SQLite helper
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cves (
            id TEXT PRIMARY KEY,
            description TEXT,
            source TEXT,
            type TEXT,
            published_date TEXT,
            read_flag INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# -----------------------------
# Feed sources (verified)
# -----------------------------
FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "type": "Malware"},
    {"url": "https://feeds.feedburner.com/GoogleChromeReleases", "source": "Google Chrome", "type": "Patch"},
    {"url": "https://services.nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "source": "NVD", "type": "CVE", "json": True},
]

# User added feeds (can be dynamically updated in DB or config)
USER_FEEDS = []  # example: {"url": "...", "source": "...", "type": "..."}

# -----------------------------
# Fetch all feeds
# -----------------------------
def fetch_all_feeds(interval=CACHE_EXPIRY_MINUTES_DEFAULT):
    init_db()
    conn = get_db_connection()

    # Check last update
    try:
        mtime = DB_FILE.stat().st_mtime
        last_date = datetime.fromtimestamp(mtime)
        if datetime.now() - last_date < timedelta(minutes=interval):
            print(f"[{datetime.now().isoformat()}] Using cached CVEs in database")
            conn.close()
            return
    except FileNotFoundError:
        pass

    print(f"[{datetime.now().isoformat()}] Fetching feeds...")

    all_feeds = FEEDS + USER_FEEDS
    for feed in all_feeds:
        url = feed["url"]
        source = feed.get("source", "Unknown")
        ctype = feed.get("type", "Unknown")
        is_json = feed.get("json", False)
        print(f"Fetching feed: {source}")

        try:
            if is_json:  # NVD JSON
                resp = requests.get(url, headers={"User-Agent": "OpenThreatIQ/1.0"})
                resp.raise_for_status()
                with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                for item in data.get("CVE_Items", []):
                    cve_id = item["cve"]["CVE_data_meta"]["ID"]
                    desc = item["cve"]["description"]["description_data"][0]["value"]
                    pub_date = item["publishedDate"]
                    upsert_cve(conn, cve_id, desc, source, ctype, pub_date)
            else:  # RSS
                parsed = feedparser.parse(url)
                for entry in parsed.entries:
                    cve_id = entry.get("id") or entry.get("link")
                    desc = entry.get("content")[0].value if "content" in entry else entry.get("summary", "")
                    pub_date = entry.get("published", datetime.now().isoformat())
                    upsert_cve(conn, cve_id, desc, source, ctype, pub_date)
        except Exception as e:
            print(f"Error fetching {source}: {e}")

    conn.commit()
    conn.close()
    print(f"[{datetime.now().isoformat()}] Feeds updated.")

# -----------------------------
# Upsert CVE into DB
# -----------------------------
def upsert_cve(conn, cve_id, description, source, ctype, pub_date):
    conn.execute('''
        INSERT OR REPLACE INTO cves (id, description, source, type, published_date, read_flag)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT read_flag FROM cves WHERE id = ?), 0))
    ''', (cve_id, description, source, ctype, pub_date, cve_id))

