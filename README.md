<p align="center">
  <img src="favicon.jpg" alt="RCK Analytics" width="80" style="border-radius: 12px;" />
</p>

<h1 align="center">Substack Intelligence Feed</h1>
<p align="center">
  <strong>RCK Analytics</strong> · Automated scraper + live dashboard for 300+ Substack newsletters and Reddit/stocks
</p>

<p align="center">
  <a href="https://rckanalytics.com">rckanalytics.com</a> ·
  <a href="https://linkedin.com/company/rck-analytics">LinkedIn</a> ·
  <a href="https://github.com/rck-analytics/insider-monkey-substacks">GitHub</a>
</p>

---

## What this does

Two scrapers run on separate schedules. The Substack scraper runs once daily at 8:45 AM IST on a local machine, fetching articles from 300+ Substack newsletters via RSS (with a BeautifulSoup fallback for feeds that block RSS). The Reddit scraper runs every 3 hours via GitHub Actions, keeping the Reddit/stocks feed fresh around the clock without needing the local machine to be on. Both deduplicate by article link and push results to this repo. GitHub Pages serves a clean dashboard the whole team can open in any browser — no login, no Power BI, no manual steps.

---

## How it works

```
8:45 AM IST  - Windows Task Scheduler triggers run.bat (local machine)
             -> git pull origin main (picks up latest reddit_articles.json)
             -> scraper/scrape.py runs locally
                -> tries RSS feed for each Substack
                -> falls back to requests + BeautifulSoup if RSS blocked
                -> deduplicates by article link (link = UID)
                -> saves data/articles.json
                -> git commit + push to main

Every 3 hours - GitHub Actions cron triggers scrape-reddit.yml
             -> scraper/scrape_reddit.py runs on GitHub's servers
                -> fetches Reddit/stocks RSS feed
                -> deduplicates by link
                -> saves data/reddit_articles.json
                -> commits only if data changed, pushes to main

             -> GitHub Pages detects change
             -> dashboard updated within 2 minutes
```

---

## Dashboard features

### Substack tab
- Default view: last 7 days, sorted newest first
- Date filters: Today / 7 Days / 14 Days / 30 Days / All Time
- Search: filter by title or substack name
- Substack dropdown: focus on a single source
- NEW badge: highlights articles from the last 24 hours
- Clickable titles: open article in new tab
- **Visited link tracking:** clicked rows dim and change colour so you always know what you've already read (persists across sessions via localStorage)
- Live article + substack count in header

### Reddit tab (separate, no mixing with Substack)
- Same filtering and sorting controls as Substack tab
- Visited link tracking works independently
- Source tags styled differently (orange) to distinguish Reddit from Substacks
- Switching tabs resets filters cleanly

---

## Scraper logic

### scrape.py (Substack) — runs once daily at 8:45 AM IST on local machine

| Scenario | Behaviour |
|---|---|
| RSS works | Parse feed, add only new links |
| RSS blocked | Fallback to requests + BeautifulSoup on archive URL |
| Link already in JSON | Skip — link is the unique ID |
| No existing JSON | Fresh build from scratch |

### scrape_reddit.py (Reddit) — runs every 3 hours via GitHub Actions

| Scenario | Behaviour |
|---|---|
| RSS fetch succeeds | Parse entries, add only new links |
| Link already in JSON | Skip — link is the unique ID |
| No data changed | No commit made (workflow skips push) |
| No existing JSON | Fresh build from scratch |

No monthly overwrites. Data only ever grows. Every article link is unique across runs.

---

## File structure

```
insider-monkey-substacks/
├── .github/
│   └── workflows/
│       ├── scrape-main.yml         # Disabled - Substack runs locally via Task Scheduler
│       ├── scrape-staging.yml      # Manual trigger for testing
│       └── scrape-reddit.yml       # Cron every 3h - Reddit scraper on GitHub Actions
├── scraper/
│   ├── scrape.py                   # Substack scraper - RSS + BeautifulSoup fallback
│   ├── scrape_reddit.py            # Reddit scraper - RSS only
│   └── requirements.txt            # Python dependencies
├── data/
│   ├── articles.json               # Substack data - updated daily at 8:45 AM IST
│   └── reddit_articles.json        # Reddit data - updated every 3 hours via GitHub Actions
├── backups/
│   └── minsider_backup_YYYY-MM-DD.xlsx  # Daily Excel backups (Substack)
├── run.bat                         # Windows batch file to pull, scrape, and push (Substack)
├── index.html                      # The dashboard (Substack + Reddit tabs)
├── favicon.jpg                     # RCK Analytics logo
├── source_links.xlsx               # 380 Substack URLs (Name + URL columns, archives sheet)
└── README.md
```

---

## Local setup (Substack scraper only)

### Requirements

- Python 3.11+
- Git configured with push access to this repo
- Windows machine with Task Scheduler

### Install dependencies

```bash
cd scraper
pip install -r requirements.txt
```

### Configure run.bat

`run.bat` is included in the repo root. Before using it, open it and update the three paths at the top to match your machine:

```bat
set REPO_DIR=D:\Insider Monkey\insider-monkey-substacks
set VENV_PYTHON=D:\Insider Monkey\venv\Scripts\python.exe
set SCRIPT=D:\Insider Monkey\insider-monkey-substacks\scraper\scrape.py
```

### Run manually

```bash
cmd /c "D:\Insider Monkey\run.bat"
```

### Task Scheduler setup

1. Open **Task Scheduler** → click **Create Task**
2. **General tab**
   - Name: `RCK Substack Scraper`
   - Check **Run whether user is logged on or not**
3. **Triggers tab** → New
   - Begin the task: **On a schedule**
   - Daily at **8:45 AM**
   - Check **Enabled**
4. **Actions tab** → New
   - Action: **Start a program**
   - Program/script: `cmd`
   - Add arguments: `/c "D:\Insider Monkey\run.bat"`
5. **Settings tab**
   - Check **Run task as soon as possible after a scheduled start is missed** — this ensures it catches up if the machine was off at 8:45 AM
6. Click **OK** and enter your Windows password when prompted

---

## GitHub Actions (Reddit scraper)

The Reddit scraper runs entirely on GitHub's servers — no local machine needed.

- **Schedule:** every 3 hours (`0 */3 * * *`)
- **Manual trigger:** available via `workflow_dispatch` from the Actions tab
- **Smart commits:** only commits and pushes if `reddit_articles.json` actually changed — no noise in git history

---

## Data format

### articles.json (Substack)

```json
[
  {
    "substack": "Source Name",
    "title": "Article Title",
    "link": "https://...",
    "pubdate": "2026-08-19"
  }
]
```

### reddit_articles.json (Reddit)

```json
[
  {
    "substack": "Reddit/stocks",
    "title": "Post Title",
    "link": "https://...",
    "pubdate": "2026-08-19"
  }
]
```

Both store date only. Article link is always the unique ID used for deduplication.

---

## Branches

| Branch | Purpose |
|---|---|
| `main` | Production — Substack daily (local) + Reddit every 3h (GitHub Actions) |
| `staging` | Testing — trigger manually from Actions tab |

---

## Coverage

- **380** Substacks in `source_links.xlsx`
- **~330** covered per daily run (~87%)
- **~6000+** articles in `articles.json`
- Uncovered Substacks are either paywalled, deleted, or have RSS fully disabled
- Reddit/stocks feed fetched fresh every 3 hours, 24/7

---

<p align="center">
  Built by <a href="https://rckanalytics.com">RCK Analytics</a> ·
  <a href="https://linkedin.com/company/rck-analytics">LinkedIn</a>
</p>