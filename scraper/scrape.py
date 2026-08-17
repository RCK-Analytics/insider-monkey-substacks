import time
start_time = time.time()

import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import logging
import json
import os
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

user_agents_list = [
    'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'
]

# Paths - all relative to repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
SOURCE_FILE = os.path.join(ROOT_DIR, "source_links.xlsx")
DATA_FILE = os.path.join(ROOT_DIR, "data", "articles.json")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Scrape ---
substacks = pd.read_excel(SOURCE_FILE, sheet_name='archives')
articles = pd.DataFrame(columns=['title', 'link', 'pubdate', 'substack'])

for i in range(len(substacks)):
    name = substacks.iloc[i].Name
    url = substacks.iloc[i].URL

    try:
        headers = {'User-Agent': random.choice(user_agents_list)}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}: Status {response.status_code}")
            continue

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
            logging.warning(f"No articles found for: {name}")
            continue

        df = pd.DataFrame({
            'title': titles[:min_len],
            'link': links[:min_len],
            'pubdate': dates[:min_len]
        })
        df['substack'] = name
        df['pubdate'] = pd.to_datetime(df['pubdate'], errors='coerce')

        if not df.empty:
            articles = pd.concat([articles, df], ignore_index=True)
            logging.info(f"{name} | {len(df)} articles | Total = {len(articles)}")

        time.sleep(random.uniform(1, 3))

    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
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
