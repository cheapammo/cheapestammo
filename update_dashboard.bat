@echo off
echo.
echo ========================================
echo   🎯 CheapAmmo Dashboard Updater
echo ========================================
echo.
echo 📊 Running ammunition price scrapers...
echo ------------------------
python shopify_generic_scraper.py
python magento_generic_scraper.py
python direct_retailer_scraper.py

echo 🔀 Combining CSVs into unified feed...
python combine_prices.py

echo ✅ Scraping & merge complete!
echo �� Starting dashboard server...
echo.

python start_dashboard_server.py 