import requests
import sqlite3
import feedparser
import json
import gzip
import io
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

DB_FILE = "data/threats.db"
DEFAULT_CACHE_MINUTES = 30

# Verified public feeds
FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "type": "Malware", "format": "rss"},
    {"url": "https://feeds.feedburner.com/GoogleChromeReleases", "source": "Google Chrome", "type": "Patch", "format": "rss"},
    {"url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "source": "NVD", "type": "CVE", "format": "json"}
]

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS threats (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    link TEXT,
                    source TEXT,
                    type TEXT,
                    published_date TEXT,
                    read_flag INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )''')
    conn.commit()
    conn.close()

# Get cache interval
def get_cache_interval():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='cache_interval'")
    row = c.fetchone()
    conn.close()
    return int(row[0]) if row else DEFAULT_CACHE_MINUTES

def set_cache_interval(minutes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("cache_interval", str(minutes)))
    conn.commit()
    conn.close()

# Fetch all feeds
def fetch_all_feeds():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Check last update
    c.execute("SELECT value FROM config WHERE key='last_update'")
    row = c.fetchone()
    now = datetime.utcnow()
    if row:
        last_update = datetime.fromisoformat(row[0])
        if now - last_update < timedelta(minutes=get_cache_interval()):
            print(f"[{datetime.now().isoformat()}] Using cached threats from DB")
            conn.close()
            return get_all_threats()

    print(f"[{datetime.now().isoformat()}] Updating feeds...")

    # Include user-added feeds
    conn_user = sqlite3.connect(DB_FILE)
    c_user = conn_user.cursor()
    c_user.execute("SELECT key, value FROM config WHERE key LIKE 'user_feed_%'")
    user_feeds = [{"url": v, "source": k.split("user_feed_")[1], "type": "Custom", "format": "rss"} for k, v in c_user.fetchall()]
    conn_user.close()

    feeds_to_fetch = FEEDS + user_feeds

    for feed in feeds_to_fetch:
        try:
            if feed["format"] == "rss":
                items = fetch_rss_feed(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["title"], item["description"], item["link"], feed.get("source", "Unknown"), feed.get("type", "Unknown"), item["published_date"])
            elif feed["format"] == "json":
                items = fetch_nvd_json(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["id"], item["description"], "", feed.get("source", "Unknown"), feed.get("type", "Unknown"), item.get("publishedDate", ""))
        except Exception as e:
            print(f"Error fetching {feed.get('source', 'Unknown')}: {e}")

    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("last_update", now.isoformat()))
    conn.commit()
    conn.close()
    return get_all_threats()

# Insert or update threats
def upsert_threat(cursor, tid, title, description, link, source, ttype, pubdate):
    cursor.execute('''
        INSERT OR REPLACE INTO threats(id, title, description, link, source, type, published_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tid, title, description, link, source, ttype, pubdate))

def fetch_rss_feed(url):
    headers = {"User-Agent": "OpenThreatIQ/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items = []
    for entry in feed.entries:
        content = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
        content = BeautifulSoup(content, "html.parser").get_text()
        items.append({
            "id": entry.get("id") or entry.get("link"),
            "title": entry.get("title"),
            "description": content,
            "link": entry.get("link"),
            "published_date": entry.get("published") or entry.get("updated") or ""
        })
    return items

def fetch_nvd_json(url):
    headers = {"User-Agent": "OpenThreatIQ/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
        data = json.load(f)
    items = []
    for item in data.get("CVE_Items", []):
        cve_id = item["cve"]["CVE_data_meta"]["ID"]
        desc = item["cve"]["description"]["description_data"][0]["value"]
        pubdate = item.get("publishedDate", "")
        items.append({"id": cve_id, "description": desc, "publishedDate": pubdate})
    return items

def get_all_threats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM threats ORDER BY published_date DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def mark_read(threat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE threats SET read_flag=1 WHERE id=?", (threat_id,))
    conn.commit()
    conn.close()

def add_user_feed(url, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    key = f"user_feed_{name}"
    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", (key, url))
    conn.commit()
    conn.close()
