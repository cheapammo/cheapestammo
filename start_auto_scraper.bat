@echo off
title CheapAmmo Auto Scraper
echo.
echo ============================================
echo    CheapAmmo Automatic Scraper Scheduler
echo ============================================
echo.
echo This will automatically run the scraper every 30 minutes
echo Press Ctrl+C to stop the scheduler
echo.
pause

cd /d "C:\Users\tcons\Cheapammo"
python automatic_scraper_scheduler.py

echo.
echo Scheduler stopped. Press any key to exit.
pause 