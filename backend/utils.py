import os, json, feedparser, requests, sqlite3
from datetime import datetime, timedelta

CACHE_FILE = "data/cve_cache.json"
CACHE_EXPIRY_MINUTES = 30
DB_FILE = "data/threatintel.db"

# verified free feeds
FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "type": "Malware", "source": "BleepingComputer"},
    {"url": "https://blog.google/threat-analysis/feed/", "type": "CVE", "source": "Google Security Blog"},
    {"url": "https://msrc.microsoft.com/update-guide/rss", "type": "CVE", "source": "Microsoft Security"}
]

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    type TEXT,
                    source TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS read_cves (
                    id TEXT PRIMARY KEY
                )''')
    conn.commit()
    conn.close()

init_db()

def get_user_feeds():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT url, type, source FROM user_feeds")
    feeds = [{"url": row[0], "type": row[1], "source": row[2]} for row in c.fetchall()]
    conn.close()
    return feeds

def add_custom_feed(url, feed_type="Other", source="User Feed"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_feeds (url, type, source) VALUES (?, ?, ?)",
              (url, feed_type, source))
    conn.commit()
    conn.close()

def mark_read(cve_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO read_cves (id) VALUES (?)", (cve_id,))
    conn.commit()
    conn.close()

def is_read(cve_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM read_cves WHERE id=?", (cve_id,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def set_cache_interval(minutes):
    global CACHE_EXPIRY_MINUTES
    CACHE_EXPIRY_MINUTES = minutes

def fetch_all_feeds():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(minutes=CACHE_EXPIRY_MINUTES):
            print(f"[{datetime.now().isoformat()}] Using cached CVEs from {CACHE_FILE}")
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    all_feeds = FEEDS + get_user_feeds()
    cves = []

    for feed in all_feeds:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries:
                cve_id = entry.get("id") or entry.get("title")[:10]
                cves.append({
                    "id": cve_id,
                    "description": entry.get("summary", entry.get("description", "")),
                    "published_date": entry.get("published", ""),
                    "source": feed.get("source"),
                    "type": feed.get("type"),
                    "read_flag": is_read(cve_id)
                })
        except Exception as e:
            print(f"Error fetching {feed.get('source')}: {e}")

    with open(CACHE_FILE, "w") as f:
        json.dump(cves, f, indent=2)

    return cves
