import time
start_time = time.time()

import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import json
import os
import random
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

user_agents_list = [
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
SOURCE_FILE = os.path.join(ROOT_DIR, "source_links.xlsx")
DATA_FILE = os.path.join(ROOT_DIR, "data", "articles.json")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Load existing articles.json as seen links set ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        existing_records = json.load(f)
    existing_df = pd.DataFrame(existing_records)
    existing_df['pubdate'] = pd.to_datetime(existing_df['pubdate'], errors='coerce')
    seen_links = set(existing_df['link'].dropna().unique())
    logging.info(f"Loaded {len(existing_df)} existing articles, {len(seen_links)} unique links")
else:
    existing_df = pd.DataFrame(columns=['substack', 'title', 'link', 'pubdate'])
    seen_links = set()
    logging.info("No existing articles.json - fresh start")

substacks = pd.read_excel(SOURCE_FILE, sheet_name='archives')
new_articles = pd.DataFrame(columns=['title', 'link', 'pubdate', 'substack'])

rss_success = 0
rss_fail = 0
fallback_success = 0
fallback_fail = 0

def scrape_via_requests(name, url):
    """Fallback: scrape archive page via requests + BeautifulSoup"""
    try:
        headers = {'User-Agent': random.choice(user_agents_list)}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        titles, links, dates = [], [], []

        for link in soup.find_all('a'):
            if link.get('data-testid') == 'post-preview-title':
                href = link.get('href')
                text = link.string.strip() if link.string else ''
                if href and text:
                    links.append(href)
                    titles.append(text)

        for date_tag in soup.find_all('time', class_='date-rtYe1v'):
            datetime_val = date_tag.get('datetime')
            if datetime_val:
                dates.append(datetime_val.split('T')[0])

        min_len = min(len(titles), len(links), len(dates))
        if min_len == 0:
            return None

        df = pd.DataFrame({
            'title': titles[:min_len],
            'link': links[:min_len],
            'pubdate': dates[:min_len]
        })
        df['substack'] = name
        df['pubdate'] = pd.to_datetime(df['pubdate'], errors='coerce')
        return df

    except Exception as e:
        logging.error(f"Fallback requests error for {url}: {e}")
        return None

for i in range(len(substacks)):
    name = substacks.iloc[i].Name
    url = str(substacks.iloc[i].URL).strip()

    base = url.split('/archive')[0].split('/feed')[0].rstrip('/')
    feed_url = f"{base}/feed"

    titles, links, dates = [], [], []
    used_fallback = False

    try:
        # --- Try RSS first ---
        feed = feedparser.parse(
            feed_url,
            agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )

        rss_ok = (not feed.bozo or feed.entries) and len(feed.entries) > 0

        if rss_ok:
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

            if titles:
                rss_success += 1
            else:
                rss_ok = False

        if not rss_ok:
            # --- Fallback to requests ---
            logging.warning(f"RSS failed for {name} - falling back to requests: {url}")
            df_fallback = scrape_via_requests(name, url)
            if df_fallback is not None and not df_fallback.empty:
                # Filter only new links
                df_fallback = df_fallback[~df_fallback['link'].isin(seen_links)]
                if not df_fallback.empty:
                    new_articles = pd.concat([new_articles, df_fallback], ignore_index=True)
                    seen_links.update(df_fallback['link'].tolist())
                    logging.info(f"[FALLBACK] {name} | {len(df_fallback)} new articles")
                    fallback_success += 1
                else:
                    logging.info(f"[FALLBACK] {name} | 0 new articles (all seen)")
                    fallback_success += 1
            else:
                logging.warning(f"[FALLBACK] {name} | failed completely")
                fallback_fail += 1
            continue

        # --- Filter only new links from RSS ---
        df = pd.DataFrame({'title': titles, 'link': links, 'pubdate': dates})
        df['substack'] = name
        df['pubdate'] = pd.to_datetime(df['pubdate'], errors='coerce')
        df = df[~df['link'].isin(seen_links)]

        if not df.empty:
            new_articles = pd.concat([new_articles, df], ignore_index=True)
            seen_links.update(df['link'].tolist())
            logging.info(f"{name} | {len(df)} new articles | Total new = {len(new_articles)}")
        else:
            logging.info(f"{name} | 0 new articles (all seen)")

    except Exception as e:
        logging.error(f"Error processing {name}: {e}")
        continue

# --- Merge new into existing, deduplicate by link ---
logging.info(f"\nRSS success: {rss_success} | RSS fail: {rss_fail}")
logging.info(f"Fallback success: {fallback_success} | Fallback fail: {fallback_fail}")
logging.info(f"New articles found: {len(new_articles)}")

if not new_articles.empty:
    combined = pd.concat([existing_df, new_articles], ignore_index=True)
    combined.drop_duplicates(subset='link', keep='first', inplace=True)
    combined.sort_values(by="pubdate", ascending=False, inplace=True)
    final_df = combined
else:
    final_df = existing_df
    logging.info("No new articles found - articles.json unchanged")

# --- Save JSON ---
final_df['pubdate'] = pd.to_datetime(final_df['pubdate']).dt.strftime('%Y-%m-%d')
final_df.to_json(DATA_FILE, orient='records', indent=2, force_ascii=False)
logging.info(f"Saved {len(final_df)} total articles to data/articles.json")

# --- Save dated Excel backup ---
today = date.today()
backup_path = os.path.join(BACKUP_DIR, f"minsider_backup_{today}.xlsx")
final_df.to_excel(backup_path, index=False)
logging.info(f"Backup saved: {backup_path}")

end_time = time.time()
print(f"\nDone. {len(final_df)} total articles. {len(new_articles)} new today. Executed in {end_time - start_time:.2f}s.")