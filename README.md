# Substack Intelligence Feed - RCK Analytics

Automated daily scraper + GitHub Pages dashboard for 300+ Substack newsletters.

**Live dashboard:** `https://rck-analytics.github.io/insider-monkey-substacks/`

---

## How it works

1. GitHub Actions runs `scraper/scrape.py` every morning at 7:00 AM IST
2. Scraper hits all Substack archive URLs from `source_links.xlsx`
3. New articles are deduplicated and appended to `data/articles.json`
4. On the 1st of every month, `articles.json` is wiped and rebuilt fresh
5. GitHub Pages serves `index.html` which reads the JSON and renders the dashboard

---

## Setup (one time)

### 1. Create the repo

In the `rck-analytics` GitHub org, create a new repo called `substack-feed`.
Add two branches: `main` and `staging`.

### 2. Push these files

```
git clone https://github.com/rck-analytics/insider-monkey-substacks
cd insider-monkey-substacks
# copy all files here
git add .
git commit -m "init: substack feed project"
git push origin main
```

### 3. Add source_links.xlsx to the repo

Copy your `source_links.xlsx` file (with the `archives` sheet containing Name and URL columns)
to the root of the repo and commit it.

```
git add source_links.xlsx
git commit -m "add: source links"
git push origin main
```

### 4. Enable GitHub Pages

- Go to repo Settings -> Pages
- Source: Deploy from a branch
- Branch: `main` / `/ (root)`
- Save

Your dashboard will be live at: `https://rck-analytics.github.io/insider-monkey-substacks`

### 5. Enable Actions write permissions

- Go to repo Settings -> Actions -> General
- Under "Workflow permissions" select "Read and write permissions"
- Save

This lets the GitHub Actions bot commit the updated `articles.json` back to the repo.

---

## Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production - runs daily at 7 AM IST automatically |
| `staging` | Testing - runs on every push to staging, or manually |

To test a scrape manually without waiting for 7 AM:
- Go to Actions tab in GitHub
- Select "Scrape Substacks (Production)" or "(Staging)"
- Click "Run workflow"

---

## Data logic

| Scenario | Behaviour |
|----------|-----------|
| Daily runs | New articles appended, duplicates removed by link |
| 1st of month | Full overwrite - fresh start |
| First ever run | Creates articles.json from scratch |

---

## File structure

```
insider-monkey-substacks/
- .github/workflows/
  - scrape-main.yml       # Production cron job
  - scrape-staging.yml    # Staging workflow
- scraper/
  - scrape.py             # Main scraper
  - requirements.txt      # Python dependencies
- data/
  - articles.json         # Dashboard data (auto-updated)
- backups/
  - minsider_backup_YYYY-MM-DD.xlsx  # Daily Excel backups (gitignored)
- index.html              # The dashboard
- source_links.xlsx       # Your 300+ Substack URLs (you add this)
- README.md
```

---

## Dashboard features

- Default view: last 7 days, sorted newest first
- Date filters: Today / 7 Days / 14 Days / 30 Days / All Time
- Search: filters by title or substack name
- Substack dropdown: filter to a single source
- NEW badge: highlights articles from the last 24 hours
- Clickable titles: open article in new tab
- Article + substack count in header
