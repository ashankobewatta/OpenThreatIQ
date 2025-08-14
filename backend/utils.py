# backend/utils.py
import requests
import json
import os
import gzip
import io
from datetime import datetime, timedelta

CACHE_FILE = "data/cve_cache.json"
FEED_URL = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz"
CACHE_EXPIRY_HOURS = 24

def fetch_cves():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Check if cache exists and is still valid
    if os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.now() - mtime < timedelta(hours=CACHE_EXPIRY_HOURS):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    # If cache is missing or old, download fresh feed
    print("Fetching latest CVE feed from NVD...")
    resp = requests.get(FEED_URL, headers={"User-Agent": "OpenThreatIQ/1.0"})
    resp.raise_for_status()

    # Decompress gzip content
    with gzip.open(io.BytesIO(resp.content), 'rt', encoding='utf-8') as f:
        data = json.load(f)

    # Extract relevant CVE info
    cves = []
    for item in data.get("CVE_Items", []):
        cves.append({
            "id": item["cve"]["CVE_data_meta"]["ID"],
            "description": item["cve"]["description"]["description_data"][0]["value"],
            "publishedDate": item["publishedDate"]
        })

    # Save to cache
    with open(CACHE_FILE, "w") as f:
        json.dump(cves, f, indent=2)

    print(f"Fetched and cached {len(cves)} CVEs.")
    return cves
