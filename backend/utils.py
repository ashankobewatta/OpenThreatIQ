import requests, json, os, gzip, io, sqlite3
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

DB_FILE = "data/threatiq.db"
CACHE_SETTINGS_FILE = "data/cache_settings.json"
DEFAULT_CACHE_EXPIRY_MINUTES = 30

FEED_URLS = [
    {"name": "NVD", "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "type": "CVE"},
    {"name": "Google Security Blog", "url": "https://security.googleblog.com/feeds/posts/default", "type": "Update"},
    {"name": "Microsoft Security Blog", "url": "https://www.microsoft.com/en-us/security/blog/feed/", "type": "Update"},
    {"name": "Bleeping Computer", "url": "https://www.bleepingcomputer.com/feed/", "type": "Update"}
]

# ---------------- DB Initialization ----------------
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

# ---------------- Cache Interval ----------------
def get_cache_interval():
    if os.path.exists(CACHE_SETTINGS_FILE):
        try:
            with open(CACHE_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("cache_expiry_minutes", DEFAULT_CACHE_EXPIRY_MINUTES))
        except:
            return DEFAULT_CACHE_EXPIRY_MINUTES
    return DEFAULT_CACHE_EXPIRY_MINUTES

def set_cache_interval(minutes):
    os.makedirs("data", exist_ok=True)
    with open(CACHE_SETTINGS_FILE, "w") as f:
        json.dump({"cache_expiry_minutes": minutes}, f)

# ---------------- Fetch All Feeds ----------------
def fetch_all_feeds():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # check cache freshness
    cur.execute("SELECT MAX(published_date) FROM cve_entries")
    last_date_row = cur.fetchone()
    cache_expiry_minutes = get_cache_interval()

    if last_date_row and last_date_row[0]:
        try:
            last_date = datetime.fromisoformat(last_date_row[0].replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            if now_utc - last_date < timedelta(minutes=cache_expiry_minutes):
                print(f"[{now_utc.isoformat()}] Using cached CVEs from DB")
                conn.close()
                return get_all_cves()
        except:
            pass

    all_entries = []

    for feed in FEED_URLS:
        print(f"Fetching feed: {feed['name']}")
        try:
            resp = requests.get(feed["url"], headers={"User-Agent": "OpenThreatIQ/1.0"}, timeout=15)
            resp.raise_for_status()

            if feed["url"].endswith(".gz"):
                with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                for item in data.get("CVE_Items", []):
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
        except requests.exceptions.SSLError as ssl_err:
            print(f"SSL Error fetching {feed['name']}: {ssl_err}")
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")

    # custom feeds
    cur.execute("SELECT name, url, type FROM custom_feeds")
    for name, url, ftype in cur.fetchall():
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
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

# ---------------- DB helpers ----------------
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
        print(f"Error saving {entry['id']}: {e}")
    finally:
        conn.close()

def get_all_cves():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM cve_entries ORDER BY published_date DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_cve_read(cve_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE cve_entries SET read_flag=1 WHERE id=?", (cve_id,))
    conn.commit()
    conn.close()
