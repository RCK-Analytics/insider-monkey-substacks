import time
start_time = time.time()

import feedparser
import json
import os
import logging
from datetime import datetime, date, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_FILE = os.path.join(ROOT_DIR, "data", "reddit_articles.json")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
RSS_URLS = [
    "https://www.reddit.com/user/famous-feedback-11/m/stocks/new/.rss?limit=100",
    "https://www.reddit.com/user/famous-feedback-11/m/stocks/top/.rss?limit=100",
]
SOURCE_NAME = "Reddit/stocks"
# ──────────────────────────────────────────────────────────────────────────────

# --- Load existing reddit_articles.json ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        existing_records = json.load(f)
    seen_links = {r["link"] for r in existing_records if r.get("link")}
    logging.info(f"Loaded {len(existing_records)} existing articles, {len(seen_links)} unique links")
else:
    existing_records = []
    seen_links = set()
    logging.info("No existing reddit_articles.json — fresh start")

# --- Fetch RSS ---
new_articles = []
skipped = 0

for RSS_URL in RSS_URLS:
    logging.info(f"Fetching: {RSS_URL}")
    feed = feedparser.parse(
        RSS_URL,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    if feed.bozo and not feed.entries:
        logging.error(f"RSS parse failed for {RSS_URL}: {feed.bozo_exception}")
        continue

    logging.info(f"Feed returned {len(feed.entries)} entries")

    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link  = (entry.get("link")  or "").strip()

        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        pub_date = datetime(*pub[:3], tzinfo=timezone.utc).strftime("%Y-%m-%d") if pub else datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if not title or not link:
            continue
        if link in seen_links:
            skipped += 1
            continue

        # extract r/subreddit from link e.g. https://www.reddit.com/r/stocks/comments/...
        try:
            subreddit = 'r/' + link.split('/r/')[1].split('/')[0]
        except Exception:
            subreddit = SOURCE_NAME
        new_articles.append({"substack": subreddit, "title": title, "link": link, "pubdate": pub_date})
        seen_links.add(link)

logging.info(f"New articles: {len(new_articles)} | Already seen (skipped): {skipped}")

# --- Merge, deduplicate, sort ---
combined = existing_records + new_articles
seen = set()
deduped = []
for r in combined:
    if r["link"] not in seen:
        deduped.append(r)
        seen.add(r["link"])

deduped.sort(key=lambda r: r.get("pubdate", ""), reverse=True)

# --- Save ---
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(deduped, f, indent=2, ensure_ascii=False)

end_time = time.time()
print(f"\nDone. {len(deduped)} total | {len(new_articles)} new today | {end_time - start_time:.2f}s")