import time
start_time = time.time()

import feedparser
import pandas as pd
import logging
import json
import os
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Paths - all relative to repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
SOURCE_FILE = os.path.join(ROOT_DIR, "source_links.xlsx")
DATA_FILE = os.path.join(ROOT_DIR, "data", "articles.json")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Scrape via RSS ---
substacks = pd.read_excel(SOURCE_FILE, sheet_name='archives')
articles = pd.DataFrame(columns=['title', 'link', 'pubdate', 'substack'])

for i in range(len(substacks)):
    name = substacks.iloc[i].Name
    url = substacks.iloc[i].URL

    # Convert any URL format to RSS feed URL
    base = url.split('/archive')[0].split('/feed')[0].rstrip('/')
    feed_url = f"{base}/feed"

    try:
        feed = feedparser.parse(
            feed_url,
            agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )

        if feed.bozo:
            logging.warning(f"Bozo flag (minor XML issue, continuing): {feed_url}")

        if not feed.entries:
            logging.warning(f"No entries found - skipping: {feed_url}")
            continue

        titles, links, dates = [], [], []

        for entry in feed.entries:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()

            pub = entry.get('published_parsed') or entry.get('updated_parsed')
            if pub:
                pub_date = datetime(*pub[:3]).strftime('%Y-%m-%d')
            else:
                pub_date = None

            if title and link and pub_date:
                titles.append(title)
                links.append(link)
                dates.append(pub_date)

        if not titles:
            logging.warning(f"No valid articles parsed for: {name}")
            continue

        df = pd.DataFrame({
            'title': titles,
            'link': links,
            'pubdate': dates
        })
        df['substack'] = name
        df['pubdate'] = pd.to_datetime(df['pubdate'], errors='coerce')

        articles = pd.concat([articles, df], ignore_index=True)
        logging.info(f"{name} | {feed_url} | {len(df)} articles | Total = {len(articles)}")

    except Exception as e:
        logging.error(f"Error processing {feed_url}: {e}")
        continue

articles.reset_index(drop=True, inplace=True)
articles.sort_values(by="pubdate", ascending=False, inplace=True)
articles = articles[['substack', 'title', 'link', 'pubdate']]

# --- Overwrite on 1st of month, otherwise deduplicate and append ---
today = date.today()
is_first_of_month = today.day == 1

if is_first_of_month or not os.path.exists(DATA_FILE):
    logging.info("First of month (or no existing data) - overwriting articles.json fresh.")
    final_df = articles
else:
    logging.info("Appending new articles and deduplicating by link...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        existing_records = json.load(f)
    existing_df = pd.DataFrame(existing_records)
    existing_df['pubdate'] = pd.to_datetime(existing_df['pubdate'], errors='coerce')
    combined = pd.concat([articles, existing_df], ignore_index=True)
    combined.drop_duplicates(subset='link', keep='first', inplace=True)
    combined.sort_values(by="pubdate", ascending=False, inplace=True)
    final_df = combined

# --- Save JSON for dashboard ---
final_df['pubdate'] = pd.to_datetime(final_df['pubdate']).dt.strftime('%Y-%m-%d')
final_df.to_json(DATA_FILE, orient='records', indent=2, force_ascii=False)
logging.info(f"Saved {len(final_df)} total articles to data/articles.json")

# --- Save dated Excel backup ---
backup_path = os.path.join(BACKUP_DIR, f"minsider_backup_{today}.xlsx")
final_df.to_excel(backup_path, index=False)
logging.info(f"Backup saved: {backup_path}")

end_time = time.time()
print(f"\nDone. {len(final_df)} total articles. Executed in {end_time - start_time:.2f}s.")