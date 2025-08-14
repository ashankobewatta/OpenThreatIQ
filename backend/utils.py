import requests
import json
import os
import gzip
import io
import csv
import feedparser
from datetime import datetime, timedelta

CACHE_FILE = "data/cve_cache.json"
CACHE_EXPIRY_HOURS = 24
TEMP_CSV = "data/temp_feeds.csv"

# Feed URLs
NVD_FEED_URL = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"
MALWAREBAZAAR_URL = "https://mb-api.abuse.ch/api/v1/"
PHISHTANK_CSV_URL = "https://data.phishtank.com/data/online-valid.csv"
OPENPHISH_TXT_URL = "https://openphish.com/feed.txt"
EXPLOITDB_CSV_URL = "https://www.exploit-db.com/archive.csv"
MSRC_JSON_URL = "https://api.msrc.microsoft.com/cvrf/cvrf.json"

# Verified RSS feeds
RSS_FEEDS = [
    ("https://www.bleepingcomputer.com/feed/", "BleepingComputer"),
    ("https://chromereleases.googleblog.com/feeds/posts/default?alt=rss", "Google Chrome"),
    ("https://www.mozilla.org/en-US/security/advisories/feed.xml", "Mozilla")
]

# ----------------- Temporary CSV fallback -----------------
def load_temp_csv():
    if not os.path.exists(TEMP_CSV):
        return []
    entries = []
    with open(TEMP_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append({
                "id": row["id"],
                "description": row["description"],
                "publishedDate": row.get("publishedDate") or datetime.now().isoformat(),
                "source": row.get("source") or "Unknown",
                "type": row.get("type") or "Unknown"
            })
    return entries

# ----------------- NVD -----------------
def fetch_nvd():
    try:
        resp = requests.get(NVD_FEED_URL, headers={"User-Agent": "OpenThreatIQ/1.0"}, timeout=10)
        resp.raise_for_status()
        with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
            data = json.load(f)
        entries = []
        for item in data.get("CVE_Items", []):
            entries.append({
                "id": item["cve"]["CVE_data_meta"]["ID"],
                "description": item["cve"]["description"]["description_data"][0]["value"],
                "publishedDate": item["publishedDate"],
                "source": "NVD",
                "type": "CVE"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching NVD: {e}")
        return load_temp_csv()

# ----------------- MalwareBazaar -----------------
def fetch_malwarebazaar():
    try:
        resp = requests.post(MALWAREBAZAAR_URL, data={"query": "get_recent"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        entries = []
        for item in data.get("data", []):
            entries.append({
                "id": item.get("sha256"),
                "description": item.get("signature"),
                "publishedDate": item.get("date_added"),
                "source": "MalwareBazaar",
                "type": "Malware"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching MalwareBazaar: {e}")
        return load_temp_csv()

# ----------------- PhishTank -----------------
def fetch_phishtank():
    try:
        resp = requests.get(PHISHTANK_CSV_URL, timeout=10)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        reader = csv.DictReader(lines)
        entries = []
        for row in reader:
            entries.append({
                "id": row.get("phish_id"),
                "description": row.get("url"),
                "publishedDate": row.get("online_since"),
                "source": "PhishTank",
                "type": "Phishing"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching PhishTank: {e}")
        return load_temp_csv()

# ----------------- OpenPhish -----------------
def fetch_openphish():
    try:
        resp = requests.get(OPENPHISH_TXT_URL, timeout=10)
        resp.raise_for_status()
        urls = resp.text.splitlines()
        entries = []
        for i, url in enumerate(urls):
            entries.append({
                "id": f"openphish-{i+1}",
                "description": url,
                "publishedDate": datetime.now().isoformat(),
                "source": "OpenPhish",
                "type": "Phishing"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching OpenPhish: {e}")
        return load_temp_csv()

# ----------------- ExploitDB -----------------
def fetch_exploitdb():
    try:
        resp = requests.get(EXPLOITDB_CSV_URL, timeout=10)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        reader = csv.DictReader(lines)
        entries = []
        for row in reader:
            entries.append({
                "id": row.get("id"),
                "description": row.get("description"),
                "publishedDate": row.get("date"),
                "source": "ExploitDB",
                "type": "Exploit"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching ExploitDB: {e}")
        return load_temp_csv()

# ----------------- MSRC -----------------
def fetch_msrc():
    try:
        resp = requests.get(MSRC_JSON_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        entries = []
        for item in data.get("Vulnerability", []):
            entries.append({
                "id": item.get("CVE"),
                "description": item.get("Title"),
                "publishedDate": item.get("DiscoveryDate") or datetime.now().isoformat(),
                "source": "MSRC",
                "type": "CVE"
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching MSRC: {e}")
        return load_temp_csv()

# ----------------- RSS Feed -----------------
def fetch_rss_feed(url, source_name, entry_type="Update"):
    try:
        feed = feedparser.parse(url)
        entries = []
        for item in feed.entries:
            entries.append({
                "id": item.get("id", item.get("link", "N/A")),
                "description": (item.get("title", "") + " - " + item.get("summary", "")).strip(),
                "publishedDate": item.get("published", datetime.now().isoformat()),
                "source": source_name,
                "type": entry_type
            })
        return entries
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error fetching RSS {source_name}: {e}")
        return load_temp_csv()

# ----------------- Aggregate -----------------
def fetch_all_feeds():
    os.makedirs("data", exist_ok=True)

    # Check cache
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
            print(f"[{datetime.now().isoformat()}] Using cached CVEs from {CACHE_FILE}")
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    all_entries = []

    # JSON/CSV/TXT feeds
    feed_functions = [
        fetch_nvd,
        fetch_malwarebazaar,
        fetch_phishtank,
        fetch_openphish,
        fetch_exploitdb,
        fetch_msrc
    ]
    for fn in feed_functions:
        all_entries.extend(fn())

    # RSS feeds
    for url, name in RSS_FEEDS:
        all_entries.extend(fetch_rss_feed(url, name))

    # Save cache
    with open(CACHE_FILE, "w") as f:
        json.dump(all_entries, f, indent=2)

    print(f"[{datetime.now().isoformat()}] Fetched and cached {len(all_entries)} entries.")
    return all_entries
