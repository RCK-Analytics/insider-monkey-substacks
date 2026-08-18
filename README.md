<p align="center">
  <img src="favicon.jpg" alt="RCK Analytics" width="80" style="border-radius: 12px;" />
</p>

<h1 align="center">Substack Intelligence Feed</h1>
<p align="center">
  <strong>RCK Analytics</strong> · Automated daily scraper + live dashboard for 300+ Substack newsletters
</p>

<p align="center">
  <a href="https://rck-analytics.github.io/insider-monkey-substacks/">🔗 Live Dashboard</a> &nbsp;·&nbsp;
  <a href="https://rckanalytics.com">🌐 rckanalytics.com</a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/company/rck-analytics">💼 LinkedIn</a>
</p>

---

## What this does

Every morning at 9:00 AM IST, a Python scraper runs automatically on a local machine, fetches the latest articles from 300+ Substack newsletters via RSS (with a BeautifulSoup fallback for feeds that block RSS), deduplicates by article link, and pushes the result to this repo. GitHub Pages serves a clean dashboard the whole team can open in any browser - no login, no Power BI, no manual steps.

---

## How it works

```
9:00 AM IST - Windows Task Scheduler triggers run.bat
            -> scraper/scrape.py runs locally
            -> tries RSS feed for each Substack
            -> falls back to requests + BeautifulSoup if RSS blocked
            -> deduplicates by article link (link = UID)
            -> saves data/articles.json
            -> git commit + push to main
            -> GitHub Pages detects change
            -> dashboard updated within 2 minutes
```

---

## Dashboard features

- Default view: last 7 days, sorted newest first
- Date filters: Today / 7 Days / 14 Days / 30 Days / All Time
- Search: filter by title or substack name
- Substack dropdown: focus on a single source
- NEW badge: highlights articles from the last 24 hours
- Clickable titles: open article in new tab
- Live article + substack count in header

---

## Scraper logic

| Scenario | Behaviour |
|---|---|
| RSS works | Parse feed, add only new links |
| RSS blocked | Fallback to requests + BeautifulSoup on archive URL |
| Link already in JSON | Skip - link is the unique ID |
| No existing JSON | Fresh build from scratch |

No monthly overwrites. Data only ever grows. Every article link is unique.

---

## File structure

```
insider-monkey-substacks/
├── .github/
│   └── workflows/
│       ├── scrape-main.yml       # Disabled - runs locally via Task Scheduler
│       └── scrape-staging.yml    # Manual trigger for testing
├── scraper/
│   ├── scrape.py                 # Main scraper - RSS + fallback
│   └── requirements.txt          # Python dependencies
├── data/
│   └── articles.json             # Dashboard data - auto updated daily
├── backups/
│   └── minsider_backup_YYYY-MM-DD.xlsx  # Daily Excel backups
├── index.html                    # The dashboard
├── favicon.jpg                   # RCK Analytics logo
├── source_links.xlsx             # 380 Substack URLs (Name + URL columns, archives sheet)
└── README.md
```

---

## Local setup

### Requirements

- Python 3.11+
- Git configured with push access to this repo
- Windows Task Scheduler (for automation)

### Install dependencies

```bash
cd scraper
pip install -r requirements.txt
```

### Run manually

```bash
cmd /c "D:\Insider Monkey\run.bat"
```

### Task Scheduler

Task is set to run `run.bat` daily at 9:00 AM IST. If the machine is off at that time, it runs as soon as the machine turns on - configured via "Run task as soon as possible after a scheduled start is missed."

---

## Branches

| Branch | Purpose |
|---|---|
| `main` | Production - runs daily via local Task Scheduler |
| `staging` | Testing - trigger manually from Actions tab |

---

## Coverage

- **380** Substacks in `source_links.xlsx`
- **~330** covered per daily run (~87%)
- **~6000+** articles in `articles.json`
- Uncovered substacks are either paywalled, deleted, or have RSS fully disabled

---

<p align="center">
  Built by <a href="https://rckanalytics.com"><strong>RCK Analytics</strong></a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/company/rck-analytics">LinkedIn</a>
</p>