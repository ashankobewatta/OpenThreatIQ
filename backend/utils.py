import requests, json, os, gzip, io, csv, feedparser
from datetime import datetime, timedelta
from io import StringIO

CACHE_FILE = "data/cve_cache.json"
CACHE_EXPIRY_HOURS = 24

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

# ----------------- Fetch Functions -----------------
def fetch_nvd():
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

def fetch_malwarebazaar():
    resp = requests.post(MALWAREBAZAAR_URL, data={"query": "get_recent"}, headers={"User-Agent": "OpenThreatIQ/1.0"})
    data = resp.json()
    entries = []
    for item in data.get("data", []):
        entries.append({
            "id": item.get("sha256"),
            "description": item.get("file_type"),
            "publishedDate": item.get("first_seen"),
            "source": "MalwareBazaar",
            "type": "Malware"
        })
    return entries

def fetch_phishtank():
    resp = requests.get(PHISHTANK_CSV_URL)
    resp.raise_for_status()
    reader = csv.DictReader(StringIO(resp.text))
    entries = []
    for row in reader:
        entries.append({
            "id": row["phish_id"],
            "description": row["url"],
            "publishedDate": row["submission_time"],
            "source": "PhishTank",
            "type": "Phishing"
        })
    return entries

def fetch_openphish():
    resp = requests.get(OPENPHISH_TXT)
    resp.raise_for_status()
    entries = []
    for i, line in enumerate(resp.text.splitlines()):
        entries.append({
            "id": f"openphish-{i}",
            "description": line,
            "publishedDate": datetime.now().isoformat(),
            "source": "OpenPhish",
            "type": "Phishing"
        })
    return entries

def fetch_rss_feed(url, source_name, entry_type="Update"):
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

def fetch_exploitdb():
    resp = requests.get(EXPLOITDB_CSV)
    resp.raise_for_status()
    reader = csv.DictReader(resp.text.splitlines())
    entries = []
    for row in reader:
        entries.append({
            "id": row.get("id", "N/A"),
            "description": row.get("description", ""),
            "publishedDate": row.get("date_published", ""),
            "source": "ExploitDB",
            "type": "Exploit"
        })
    return entries

def fetch_msrc():
    resp = requests.get(MSRC_JSON, headers={"User-Agent": "OpenThreatIQ/1.0"})
    resp.raise_for_status()
    data = resp.json()
    entries = []
    for vuln in data.get("Vulnerabilities", []):
        entries.append({
            "id": vuln.get("CVE"),
            "description": vuln.get("Title", ""),
            "publishedDate": vuln.get("DatePublic", ""),
            "source": "Microsoft",
            "type": "CVE"
        })
    return entries

# ----------------- Aggregate Feeds -----------------
def fetch_all_feeds():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    all_entries = []

    for fn in [fetch_nvd, fetch_malwarebazaar, fetch_phishtank, fetch_openphish, fetch_exploitdb, fetch_msrc]:
        try:
            all_entries.extend(fn())
        except Exception as e:
            print(f"Error fetching {fn.__name__}: {e}")

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

    with open(CACHE_FILE, "w") as f:
        json.dump(all_entries, f, indent=2)

    print(f"Fetched and cached {len(all_entries)} entries.")
    return all_entries
