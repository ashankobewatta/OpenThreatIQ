import requests, json, os, gzip, io, csv, feedparser
from datetime import datetime, timedelta
from io import StringIO

CACHE_FILE = "data/cve_cache.json"
CACHE_EXPIRY_HOURS = 24
TEMP_CSV = "data/temp_feeds.csv"

# Feed URLs
NVD_FEED_URL = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"
PHISHTANK_CSV_URL = "https://data.phishtank.com/data/online-valid.csv"
MALWAREBAZAAR_URL = "https://mb-api.abuse.ch/api/v1/"
BEEPING_COMPUTER_RSS = "https://www.beepingcomputer.com/feed/"
GOOGLE_CHROME_RSS = "https://chromereleases.googleblog.com/feeds/posts/default?alt=rss"
APPLE_ATOM = "https://support.apple.com/en-us/HT201222.atom"
MOZILLA_RSS = "https://www.mozilla.org/en-US/security/advisories/feed/"
ADOBE_RSS = "https://helpx.adobe.com/security/updates/feed.rss"
EXPLOITDB_CSV = "https://www.exploit-db.com/archive.csv"
OPENPHISH_TXT = "https://openphish.com/feed.txt"
MSRC_JSON = "https://api.msrc.microsoft.com/cvrf/cvrf.json"

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

# ----------------- Fetch Functions -----------------
def fetch_nvd():
    try:
        resp = requests.get(NVD_FEED_URL, headers={"User-Agent": "OpenThreatIQ/1.0"})
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
        print(f"Error fetching NVD: {e}")
        return load_temp_csv()  # fallback

# Similarly wrap all other feed fetch functions with try/except
# and return load_temp_csv() on failure

# ----------------- RSS Fetch -----------------
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
        print(f"Error fetching RSS {source_name}: {e}")
        return load_temp_csv()  # fallback

# ----------------- Aggregate Feeds -----------------
def fetch_all_feeds():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    all_entries = []

    feed_functions = [
        fetch_nvd,
        # fetch_malwarebazaar,
        # fetch_phishtank,
        # fetch_openphish,
        # fetch_exploitdb,
        # fetch_msrc
    ]

    for fn in feed_functions:
        try:
            all_entries.extend(fn())
        except Exception as e:
            print(f"Error fetching {fn.__name__}: {e}")
            all_entries.extend(load_temp_csv())

    # RSS feeds
    rss_feeds = [
        (BEEPING_COMPUTER_RSS, "BeepingComputer"),
        (GOOGLE_CHROME_RSS, "Google"),
        (APPLE_ATOM, "Apple"),
        (MOZILLA_RSS, "Mozilla"),
        (ADOBE_RSS, "Adobe")
    ]
    for url, name in rss_feeds:
        try:
            all_entries.extend(fetch_rss_feed(url, name))
        except Exception as e:
            print(f"Error fetching RSS {name}: {e}")
            all_entries.extend(load_temp_csv())

    # Save cache
    with open(CACHE_FILE, "w") as f:
        json.dump(all_entries, f, indent=2)

    print(f"Fetched and cached {len(all_entries)} entries.")
    return all_entries
