def fetch_rss_feed(url):
    headers = {"User-Agent": "OpenThreatIQ/1.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items = []

    for entry in feed.entries:
        # Get summary or content
        content = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
        content = BeautifulSoup(content, "html.parser").get_text()

        # Attempt to fetch full article for known sources
        try:
            if "bleepingcomputer.com" in entry.link or "other-news-site.com" in entry.link:
                page_resp = requests.get(entry.link, headers=headers, timeout=10)
                page_resp.raise_for_status()
                soup = BeautifulSoup(page_resp.text, "html.parser")
                # Example selector; adjust per site
                full_article_div = soup.find("div", class_="article-content") or soup.find("div", class_="post-content")
                if full_article_div:
                    content = full_article_div.get_text(separator="\n").strip()
        except Exception as e:
            print(f"Failed to fetch full article from {entry.link}: {e}")

        items.append({
            "id": entry.get("id") or entry.get("link"),
            "title": entry.get("title"),
            "description": content,  # store full content
            "link": entry.get("link"),
            "published_date": entry.get("published") or entry.get("updated") or ""
        })
    return items
