import requests
import json
import os

CACHE_FILE = "data/cve_cache.json"

def fetch_cves():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    else:
        url = "https://services.nvd.nist.gov/rest/json/cves/1.0?resultsPerPage=20"
        resp = requests.get(url)
        data = resp.json()
        cves = []
        for item in data.get("result", {}).get("CVE_Items", []):
            cves.append({
                "id": item["cve"]["CVE_data_meta"]["ID"],
                "description": item["cve"]["description"]["description_data"][0]["value"],
                "publishedDate": item["publishedDate"]
            })
        os.makedirs("data", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cves, f, indent=2)
        return cves
