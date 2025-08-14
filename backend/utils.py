import requests
import json
import os
import gzip
import io
import sqlite3
from datetime import datetime, timedelta, timezone

DB_FILE = "data/threatiq.db"
DEFAULT_CACHE_EXPIRY_MINUTES = 30  # default cache expiry

# Verified free public feeds
FEED_URLS = [
    {"name": "NVD", "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "type": "CVE"},
    {"name": "Beeping Computer", "url": "https://www.beepingcomputer.com/feed/", "type": "Update"},
    {"name": "Google Security Blog", "url": "https://security.googleblog.com/feeds/posts/default", "type": "Update"},
    {"name": "Microsoft Security", "url": "https://msrc.microsoft.com/update-guide/rss", "type": "Update"}
]

# ------------------ DB Setup ------------------
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cve_entries (
            id TEXT PRIMARY KEY,
            description TEXT,
            published_date TEXT,
            type TEXT,
            source TEXT,
            read_flag INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS custom_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            type TEXT
        )
    """)
    conn.commit()
    conn.close()

# ------------------ Fetch all feeds ------------------
def fetch_all_feeds(cache_expiry_minutes=DEFAULT_CACHE_EXPIRY_MINUTES):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Check cache freshness
    cur.execute("SELECT MAX(published_date) FROM cve_entries")
    last_date_row = cur.fetchone()
    if last_date_row and last_date_row[0]:
        last_date = datetime.fromisoformat(last_date_row[0].replace("Z", "+00:00"))
        now_utc = datetime.now(timezone.utc)
        expiry_delta = timedelta(minutes=cache_expiry_minutes)
        if now_utc - last_date < expiry_delta:
            print(f"[{now_utc.isoformat()}] Using cached CVEs from DB")
            conn.close()
            return get_all_cves()

    all_entries = []

    for feed in FEED_URLS:
        print(f"Fetching feed: {feed['name']}")
        try:
            resp = requests.get(feed["url"], headers={"User-Agent": "OpenThreatIQ/1.0"}, timeout=15)
            resp.raise_for_status()
            if feed["url"].endswith(".gz"):
                with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                items = data.get("CVE_Items", [])
                for item in items:
                    entry = {
                        "id": item["cve"]["CVE_data_meta"]["ID"],
                        "description": item["cve"]["description"]["description_data"][0]["value"],
                        "published_date": item["publishedDate"],
                        "type": feed["type"],
                        "source": feed["name"]
                    }
                    save_cve_entry(entry)
                    all_entries.append(entry)
            else:
                import xml.etree.ElementTree as ET
                xml = ET.fromstring(resp.text)
                for item in xml.findall(".//item"):
                    entry = {
                        "id": item.find("title").text if item.find("title") is not None else "N/A",
                        "description": item.find("description").text if item.find("description") is not None else "",
                        "published_date": item.find("pubDate").text if item.find("pubDate") is not None else "",
                        "type": feed["type"],
                        "source": feed["name"]
                    }
                    save_cve_entry(entry)
                    all_entries.append(entry)
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")

    # Fetch custom feeds
    cur.execute("SELECT name, url, type FROM custom_feeds")
    custom_feeds = cur.fetchall()
    for name, url, ftype in custom_feeds:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            import xml.etree.ElementTree as ET
            xml = ET.fromstring(resp.text)
            for item in xml.findall(".//item"):
                entry = {
                    "id": item.find("title").text if item.find("title") is not None else "N/A",
                    "description": item.find("description").text if item.find("description") is not None else "",
                    "published_date": item.find("pubDate").text if item.find("pubDate") is not None else "",
                    "type": ftype,
                    "source": name
                }
                save_cve_entry(entry)
                all_entries.append(entry)
        except Exception as e:
            print(f"Error fetching custom feed {name}: {e}")

    conn.close()
    return all_entries

# ------------------ Save CVE ------------------
def save_cve_entry(entry):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR REPLACE INTO cve_entries (id, description, published_date, type, source)
            VALUES (?,?,?,?,?)
        """, (entry["id"], entry["description"], entry["published_date"], entry["type"], entry["source"]))
        conn.commit()
    except Exception as e:
        print(f"Error saving entry {entry['id']}: {e}")
    finally:
        conn.close()

# ------------------ Get all CVEs from DB ------------------
def get_all_cves():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM cve_entries ORDER BY published_date DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ------------------ Add custom feed ------------------
def add_custom_feed(name, url, ftype):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO custom_feeds (name, url, type) VALUES (?,?,?)", (name, url, ftype))
    conn.commit()
    conn.close()
