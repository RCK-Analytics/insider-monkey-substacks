@echo off
echo ============================================
echo RCK Analytics - Substack Scraper
echo %date% %time%
echo ============================================

:: --- Config ---
set REPO_DIR=D:\Insider Monkey\insider-monkey-substacks
set VENV_PYTHON=D:\Insider Monkey\venv\Scripts\python.exe
set SCRIPT=D:\Insider Monkey\insider-monkey-substacks\scraper\scrape.py

:: --- Git pull before scraping ---
cd /d "%REPO_DIR%"
echo Pulling latest changes from GitHub...
git pull origin main
echo.

:: --- Run scraper ---
echo Running scraper...
echo.
"%VENV_PYTHON%" "%SCRIPT%"

if %ERRORLEVEL% NEQ 0 (
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
if %ERRORLEVEL% NEQ 0 (
    git commit -m "chore: daily scrape %date%"
    git push origin main
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