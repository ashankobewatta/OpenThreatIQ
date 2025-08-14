import os
import json
import requests
import feedparser
from datetime import datetime, timedelta

CACHE_FILE = "data/cve_cache.json"
CACHE_EXPIRY_HOURS = 24

# ------------------- Verified free public feeds -------------------
FEEDS = [
    {"name": "NVD", "type": "CVE", "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"},
    {"name": "MSRC", "type": "Update", "url": "https://api.msrc.microsoft.com/sug/v2.0/en-US/vuln"},
    {"name": "MalwareBazaar", "type": "Malware", "url": "https://bazaar.abuse.ch/export/csv/"},
    {"name": "PhishTank", "type": "Phishing", "url": "https://data.phishtank.com/data/online-valid.csv"},
    {"name": "OpenPhish", "type": "Phishing", "url": "https://openphish.com/feed.txt"},
    {"name": "ExploitDB", "type": "Exploit", "url": "https://www.exploit-db.com/rss.xml"},
    {"name": "BleepingComputer", "type": "Update", "url": "https://www.bleepingcomputer.com/feed/"},
    {"name": "GoogleChrome", "type": "Update", "url": "https://chromereleases.googleblog.com/feeds/posts/default?alt=rss"},
    {"name": "Mozilla", "type": "Update", "url": "https://www.mozilla.org/en-US/security/advisories/feed/"}
]

# ------------------- Helper: read cache -------------------
def read_cache():
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
            print(f"[{datetime.now().isoformat()}] Using cached data from {CACHE_FILE}")
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

# ------------------- Helper: fetch JSON feed -------------------
def fetch_json_feed(feed):
    try:
        resp = requests.get(feed["url"], headers={"User-Agent": "OpenThreatIQ/1.0"})
        resp.raise_for_status()
        if feed["url"].endswith(".gz"):
            import gzip, io
            with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
                data = json.load(f)
                items = []
                for entry in data.get("CVE_Items", []):
                    items.append({
                        "id": entry["cve"]["CVE_data_meta"]["ID"],
                        "description": entry["cve"]["description"]["description_data"][0]["value"],
                        "publishedDate": entry["publishedDate"],
                        "type": feed["type"],
                        "source": feed["name"]
                    })
                return items
        else:
            # Non-gzip JSON (like MSRC)
            data = resp.json()
            items = []
            for entry in data.get("value", []):
                items.append({
                    "id": entry.get("VulnID", entry.get("CVEID", "N/A")),
                    "description": entry.get("Title", ""),
                    "publishedDate": entry.get("PublishDate", ""),
                    "type": feed["type"],
                    "source": feed["name"]
                })
            return items
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching {feed['name']}: {e}")
        return []

# ------------------- Helper: fetch RSS/CSV feed -------------------
def fetch_rss_csv_feed(feed):
    items = []
    try:
        if feed["url"].endswith(".csv"):
            resp = requests.get(feed["url"], headers={"User-Agent": "OpenThreatIQ/1.0"})
            resp.raise_for_status()
            lines = resp.text.splitlines()
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) >= 2:
                    items.append({
                        "id": parts[0],
                        "description": ",".join(parts[1:]),
                        "publishedDate": "",
                        "type": feed["type"],
                        "source": feed["name"]
                    })
        else:
            feed_data = feedparser.parse(feed["url"])
            for entry in feed_data.entries:
                items.append({
                    "id": entry.get("title", "N/A"),
                    "description": entry.get("summary", ""),
                    "publishedDate": entry.get("published", ""),
                    "type": feed["type"],
                    "source": feed["name"]
                })
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching {feed['name']}: {e}")
    return items

# ------------------- Main fetch all feeds -------------------
def fetch_all_feeds():
    os.makedirs("data", exist_ok=True)
    all_entries = []

    # Try to fetch all feeds
    for feed in FEEDS:
        if feed["url"].endswith(".json") or feed["url"].endswith(".gz"):
            entries = fetch_json_feed(feed)
        else:
            entries = fetch_rss_csv_feed(feed)
        all_entries.extend(entries)

    # Fallback to cache if no entries fetched
    if not all_entries:
        print(f"[{datetime.now().isoformat()}] No feeds fetched, using fallback cache.")
        return read_cache()

    # Save to cache
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)
        print(f"[{datetime.now().isoformat()}] Cache updated with {len(all_entries)} entries.")
    
    return all_entries
