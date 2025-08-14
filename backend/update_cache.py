# backend/update_cache.py
from utils import fetch_cves

if __name__ == "__main__":
    print("Updating CVE cache...")
    fetch_cves()
    print("CVE cache updated successfully.")
