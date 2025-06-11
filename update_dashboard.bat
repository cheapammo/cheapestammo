@echo off
echo.
echo ========================================
echo   🎯 CheapAmmo Dashboard Updater
echo ========================================
echo.
echo 📊 Running ammunition price scraper...
echo.

python direct_retailer_scraper.py

echo.
echo ✅ Scraping complete!
echo 🌐 Starting dashboard server...
echo.

python start_dashboard_server.py 