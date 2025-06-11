@echo off
echo Setting up Windows Task Scheduler for CheapAmmo Scraper...
echo.

REM Create a task that runs every 30 minutes
schtasks /create /tn "CheapAmmo Scraper" /tr "python C:\Users\tcons\Cheapammo\direct_retailer_scraper.py" /sc minute /mo 30 /ru SYSTEM

if %errorlevel% == 0 (
    echo ✅ Task created successfully!
    echo.
    echo The scraper will now run every 30 minutes automatically
    echo even when you're not logged in.
    echo.
    echo To manage the task:
    echo - Open Task Scheduler (taskschd.msc)
    echo - Look for "CheapAmmo Scraper" task
    echo.
    echo To remove the task:
    echo schtasks /delete /tn "CheapAmmo Scraper" /f
) else (
    echo ❌ Failed to create task. Try running as Administrator.
)

echo.
pause 