import os
import json
from utils import fetch_all_feeds, CACHE_FILE
from datetime import datetime

def update_offline_cache():
    os.makedirs("data", exist_ok=True)
    
    print(f"[{datetime.now().isoformat()}] Fetching all threat feeds...")
    all_entries = fetch_all_feeds()
    
    # Save offline copy
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)
    
    print(f"[{datetime.now().isoformat()}] Cached {len(all_entries)} entries to {CACHE_FILE}")

if __name__ == "__main__":
    update_offline_cache()
