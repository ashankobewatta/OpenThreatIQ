import requests
import sqlite3
import feedparser
import json
import gzip
import io
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "data", "threats.db")
CACHE_EXPIRY_MINUTES = 30

FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "type": "Malware", "format": "rss"},
    {"url": "https://feeds.feedburner.com/GoogleChromeReleases", "source": "Google Chrome", "type": "Patch", "format": "rss"},
    {"url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "source": "NVD", "type": "CVE", "format": "json"}
]

def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
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

def fetch_all_feeds():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT value FROM config WHERE key='last_update'")
    row = c.fetchone()
    now = datetime.utcnow()
    if row:
        last_update = datetime.fromisoformat(row[0])
        if now - last_update < timedelta(minutes=get_cache_interval()):
            conn.close()
            return get_all_threats()

    for feed in FEEDS:
        try:
            if feed["format"] == "rss":
                items = fetch_rss_feed(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["title"], item["description"], item["link"], feed["source"], feed["type"], item["published_date"])
            elif feed["format"] == "json":
                items = fetch_nvd_json(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["id"], item["description"], "", feed["source"], feed["type"], item["publishedDate"])
        except Exception as e:
            print(f"Error fetching {feed['source']}: {e}")

    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("last_update", now.isoformat()))
    conn.commit()
    conn.close()
    return get_all_threats()

def upsert_threat(cursor, tid, title, description, link, source, ttype, pubdate):
    cursor.execute('''INSERT OR REPLACE INTO threats(id, title, description, link, source, type, published_date)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (tid, title, description, link, source, ttype, pubdate))

def fetch_rss_feed(url):
    headers = {"User-Agent": "OpenThreatIQ/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items = []

    for entry in feed.entries:
        content = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
        content = BeautifulSoup(content, "html.parser").get_text()

        # Fetch full article for trusted sources
        if "bleepingcomputer.com" in entry.link:
            try:
                page_resp = requests.get(entry.link, headers=headers, timeout=10)
                page_resp.raise_for_status()
                soup = BeautifulSoup(page_resp.text, "html.parser")
                full_article = soup.find("div", class_="article-content")
                if full_article:
                    content = full_article.get_text(separator="\n").strip()
            except Exception as e:
                print(f"Failed to fetch full article from {entry.link}: {e}")

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

def add_user_feed(url, source="Custom", ttype="Unknown"):
    FEEDS.append({"url": url, "source": source, "type": ttype, "format": "rss"})
    fetch_all_feeds()

def get_cache_interval():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='cache_interval'")
    row = c.fetchone()
    conn.close()
    return int(row[0]) if row else CACHE_EXPIRY_MINUTES

def set_cache_interval(minutes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("cache_interval", str(minutes)))
    conn.commit()
    conn.close()
