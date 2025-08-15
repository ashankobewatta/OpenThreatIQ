import gzip
import io
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

import feedparser
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "threats.db")
CACHE_EXPIRY_MINUTES = 30

FEEDS = [
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "type": "Malware", "format": "rss"},
    {"url": "https://feeds.feedburner.com/GoogleChromeReleases", "source": "Google Chrome", "type": "Patch", "format": "rss"},
    {"url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz", "source": "NVD", "type": "CVE", "format": "json"},
]

UA = {"User-Agent": "OpenThreatIQ/1.0 (+https://example.local)"}

def init_db():
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS threats (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            link TEXT,
            source TEXT,
            type TEXT,
            published_date TEXT,
            read_flag INTEGER DEFAULT 0
        )"""
    )
    c.execute("""CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    conn.close()

def fetch_all_feeds(force: bool = False):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    now = datetime.utcnow()
    if not force:
        c.execute("SELECT value FROM config WHERE key='last_update'")
        row = c.fetchone()
        if row:
            last_update = datetime.fromisoformat(row[0])
            if now - last_update < timedelta(minutes=get_cache_interval()):
                conn.close()
                return get_all_threats()

    for feed in FEEDS:
        try:
            if feed["format"] == "rss":
                items = fetch_rss_feed(feed["url"])
                for item in items:
                    upsert_threat(
                        c,
                        tid=item["id"],
                        title=item["title"],
                        description=item["description"],
                        link=item["link"],
                        source=feed["source"],
                        ttype=feed["type"],
                        pubdate=item["published_date"],
                    )
            elif feed["format"] == "json":
                items = fetch_nvd_json(feed["url"])
                for item in items:
                    # Provide a useful link to NVD detail page
                    link = f"https://nvd.nist.gov/vuln/detail/{item['id']}"
                    upsert_threat(
                        c,
                        tid=item["id"],
                        title=item["id"],
                        description=item["description"],
                        link=link,
                        source=feed["source"],
                        ttype=feed["type"],
                        pubdate=item["publishedDate"],
                    )
        except Exception as e:
            print(f"Error fetching {feed['source']}: {e}")

    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("last_update", now.isoformat()))
    conn.commit()
    conn.close()
    return get_all_threats()

def upsert_threat(cursor, tid, title, description, link, source, ttype, pubdate):
    # Keep read_flag as-is when updating
    cursor.execute(
        """
        INSERT INTO threats (id, title, description, link, source, type, published_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            description=excluded.description,
            link=excluded.link,
            source=excluded.source,
            type=excluded.type,
            published_date=excluded.published_date
        """,
        (tid, title, description, link, source, ttype, pubdate),
    )

def fetch_rss_feed(url):
    resp = requests.get(url, headers=UA, timeout=12)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items = []

    for entry in feed.entries:
        link = entry.get("link") or ""
        # Start with best available summary
        content_html = (entry.get("content", [{}])[0].get("value")
                        or entry.get("summary_detail", {}).get("value")
                        or entry.get("summary")
                        or "")
        # Clean summary HTML -> text
        summary_text = clean_text(BeautifulSoup(content_html, "html.parser").get_text(separator="\n"))

        full_text = summary_text
        # Try to fetch full article for BleepingComputer (and any site we can parse)
        if link:
            try:
                full_text = fetch_article_fulltext(link) or summary_text
            except Exception as e:
                print(f"Fulltext fetch failed for {link}: {e}")
                full_text = summary_text

        items.append({
            "id": entry.get("id") or link,
            "title": entry.get("title") or "(untitled)",
            "description": full_text,  # store full content
            "link": link,
            "published_date": entry.get("published") or entry.get("updated") or "",
        })
    return items

def fetch_article_fulltext(url: str) -> str | None:
    """
    Robust full-text extractor with special care for BleepingComputer:
    1) JSON-LD NewsArticle.articleBody if present
    2) Known containers: [div.article-content, div.articleBody, article, div[itemprop='articleBody'], div.entry-content]
    3) Fallback: collect <p> inside <article> or main content area
    """
    r = requests.get(url, headers=UA, timeout=12)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # 1) JSON-LD NewsArticle / Article
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            # could be a list
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if not isinstance(obj, dict):
                    continue
                t = obj.get("@type")
                if t in ("NewsArticle", "Article", "Report") and obj.get("articleBody"):
                    body = clean_text(obj["articleBody"])
                    if len(body) > 200:
                        return body
        except Exception:
            continue

    # 2) Known containers (BleepingComputer commonly uses .article-content)
    containers = [
        {"name": "div", "attrs": {"class": re.compile(r"(article-content|articleBody|entry-content)")}},
        {"name": "div", "attrs": {"itemprop": "articleBody"}},
        {"name": "article", "attrs": {}},
        {"name": "section", "attrs": {"class": re.compile(r"article")}},
        {"name": "div", "attrs": {"id": re.compile(r"article|content", re.I)}},
    ]
    for sel in containers:
        node = soup.find(sel["name"], attrs=sel["attrs"])
        if node:
            text = extract_rich_text(node)
            if len(text) > 200:
                return text

    # 3) Fallback: gather paragraphs from main / article
    main = soup.find("main") or soup.find("article")
    if main:
        text = extract_rich_text(main)
        if len(text) > 200:
            return text

    # 4) Last resort: all <p>
    ps = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = clean_text("\n\n".join(ps))
    return text if len(text) > 200 else None

def extract_rich_text(root) -> str:
    # collect headings, paragraphs, and list items in order
    parts = []
    for el in root.find_all(["h2", "h3", "p", "li"], recursive=True):
        t = el.get_text(" ", strip=True)
        if t:
            parts.append(t)
    return clean_text("\n\n".join(parts))

def clean_text(s: str) -> str:
    # collapse whitespace, strip boilerplate remnants
    s = re.sub(r"\r\n?", "\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def fetch_nvd_json(url):
    resp = requests.get(url, headers=UA, timeout=20)
    resp.raise_for_status()
    with gzip.open(io.BytesIO(resp.content), "rt", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for item in data.get("CVE_Items", []):
        cve_id = item["cve"]["CVE_data_meta"]["ID"]
        desc = item["cve"]["description"]["description_data"][0]["value"]
        pubdate = item.get("publishedDate", "")
        items.append({"id": cve_id, "description": desc, "publishedDate": pubdate})
    return items

def get_all_threats():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM threats ORDER BY published_date DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def mark_read(threat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE threats SET read_flag=1 WHERE id=?", (threat_id,))
    conn.commit()
    conn.close()

def add_user_feed(url, source="Custom", ttype="Unknown"):
    FEEDS.append({"url": url, "source": source, "type": ttype, "format": "rss"})
    fetch_all_feeds(force=True)

def get_cache_interval():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='cache_interval'")
    row = c.fetchone()
    conn.close()
    return int(row[0]) if row else CACHE_EXPIRY_MINUTES

def set_cache_interval(minutes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO config(key, value) VALUES (?, ?)", ("cache_interval", str(minutes)))
    conn.commit()
    conn.close()
