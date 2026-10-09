@echo off
echo ============================================
echo RCK Analytics - Substack Scraper
echo %date% %time%
echo ============================================

:: --- Config ---
set REPO_DIR=D:\Insider Monkey\insider-monkey-substacks
set VENV_PYTHON=D:\Insider Monkey\venv\Scripts\python.exe
set SCRIPT=D:\Insider Monkey\insider-monkey-substacks\scraper\scrape.py

:: Never open vim/editor - accept default messages automatically
set GIT_EDITOR=true

:: --- Git pull before scraping ---
cd /d "%REPO_DIR%"
echo Pulling latest changes from GitHub...
git pull --rebase --autostash origin main
if errorlevel 1 (
    echo.
    echo ERROR: git pull failed.
    pause
    exit /b 1
)
echo.

:: --- Run scraper ---
echo Running scraper...
echo.
"%VENV_PYTHON%" "%SCRIPT%"

if errorlevel 1 (
    echo.
    echo ERROR: Scraper failed.
    pause
    exit /b 1
)

echo.
echo Scraper done. Pushing to GitHub...

:: --- Git commit and push ---
cd /d "%REPO_DIR%"

git add data/articles.json
git diff --staged --quiet
if errorlevel 1 (
    git commit -m "chore: daily scrape %date%"

    REM Pick up anything GitHub Actions pushed while the scraper was running
    git pull --rebase origin main
    if errorlevel 1 (
        echo.
        echo ERROR: rebase failed. Aborting it so the repo is not left half-done.
        git rebase --abort
        pause
        exit /b 1
    )

    git push origin main
    if errorlevel 1 (
        echo.
        echo ERROR: push failed.
        pause
        exit /b 1
    )

    echo.
    echo Pushed to GitHub successfully.
) else (
    echo.
    echo No changes to commit - articles.json unchanged.
)

echo.
echo ============================================
echo All done! Dashboard will update in ~2 minutes.
echo ============================================