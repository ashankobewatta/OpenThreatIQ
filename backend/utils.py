import requests, sqlite3, feedparser, json, gzip, io
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

DB_FILE = "data/threats.db"
CACHE_EXPIRY_MINUTES = 30  # Default

FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "type": "Malware", "format": "rss"},
    {"url": "https://feeds.feedburner.com/GoogleChromeReleases", "source": "Google Chrome", "type": "Patch", "format": "rss"},
    {"url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "source": "NVD", "type": "CVE", "format": "json"}
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS threats (
        id TEXT PRIMARY KEY, title TEXT, description TEXT,
        link TEXT, source TEXT, type TEXT, published_date TEXT, read_flag INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    conn.commit()
    conn.close()

def fetch_all_feeds():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # cache expiry
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
            if feed["format"]=="rss":
                items = fetch_rss_feed(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["title"], item["description"], item["link"], feed["source"], feed["type"], item["published_date"])
            else:
                items = fetch_nvd_json(feed["url"])
                for item in items:
                    upsert_threat(c, item["id"], item["title"], item["description"], item.get("link",""), feed["source"], feed["type"], item["published_date"])
        except Exception as e:
            print(f"Error fetching {feed['source']}: {e}")

    c.execute("REPLACE INTO config(key,value) VALUES (?,?)", ("last_update", now.isoformat()))
    conn.commit()
    conn.close()
    return get_all_threats()

def upsert_threat(c, tid, title, desc, link, source, ttype, pubdate):
    c.execute('''INSERT OR REPLACE INTO threats(id,title,description,link,source,type,published_date)
                 VALUES (?,?,?,?,?,?,?)''', (tid,title,desc,link,source,ttype,pubdate))

def fetch_rss_feed(url):
    headers = {"User-Agent": "OpenThreatIQ/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items=[]
    for entry in feed.entries:
        content = entry.get("content", [{}])[0].get("value") or entry.get("summary","")
        content = BeautifulSoup(content,"html.parser").get_text()
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
        data=json.load(f)
    items=[]
    for item in data.get("CVE_Items", []):
        cve_id = item["cve"]["CVE_data_meta"]["ID"]
        desc = item["cve"]["description"]["description_data"][0]["value"]
        pubdate = item.get("publishedDate","")
        items.append({"id":cve_id,"title":cve_id,"description":desc,"published_date":pubdate})
    return items

def get_all_threats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM threats ORDER BY published_date DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def mark_read(tid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE threats SET read_flag=1 WHERE id=?",(tid,))
    conn.commit()
    conn.close()

def get_cache_interval():
    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()
    c.execute("SELECT value FROM config WHERE key='cache_interval'")
    row=c.fetchone()
    conn.close()
    return int(row[0]) if row else CACHE_EXPIRY_MINUTES

def set_cache_interval(minutes):
    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()
    c.execute("REPLACE INTO config(key,value) VALUES (?,?)",("cache_interval",str(minutes)))
    conn.commit()
    conn.close()

def add_user_feed(url, source, ttype):
    FEEDS.append({"url":url,"source":source,"type":ttype,"format":"rss"})
