#!/usr/bin/env python3
"""
CheapAmmo Automatic Scraper Scheduler
Runs ammunition price scraper at regular intervals
"""

import schedule
import time
import subprocess
import logging
import os
from datetime import datetime
import json

class AmmoScraperScheduler:
    def __init__(self):
        self.setup_logging()
        self.config = {
            "scraper_script": "direct_retailer_scraper.py",
            "interval_minutes": 30,  # Run every 30 minutes
            "max_failures": 5,       # Stop after 5 consecutive failures
            "log_file": "scraper_scheduler.log",
            "stats_file": "scheduler_stats.json"
        }
        self.consecutive_failures = 0
        self.total_runs = 0
        self.successful_runs = 0
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper_scheduler.log'),
                logging.StreamHandler()  # Also print to console
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def run_scraper(self):
        """Run the ammunition scraper"""
        self.total_runs += 1
        start_time = datetime.now()
        
        self.logger.info(f"🚀 Starting scraper run #{self.total_runs}")
        self.logger.info(f"⏰ Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run the scraper script
            result = subprocess.run(
                ["python", self.config["scraper_script"]], 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.returncode == 0:
                self.successful_runs += 1
                self.consecutive_failures = 0
                
                # Check if CSV was updated
                csv_updated = self.check_csv_updated()
                
                self.logger.info(f"✅ Scraper completed successfully in {duration:.1f}s")
                if csv_updated:
                    self.logger.info(f"📊 CSV file updated with fresh data")
                else:
                    self.logger.warning(f"⚠️  CSV file may not have been updated")
                    
                # Log any output from scraper
                if result.stdout.strip():
                    self.logger.info(f"📝 Scraper output: {result.stdout.strip()}")
                    
            else:
                self.consecutive_failures += 1
                self.logger.error(f"❌ Scraper failed with exit code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                
                # Stop if too many consecutive failures
                if self.consecutive_failures >= self.config["max_failures"]:
                    self.logger.critical(f"🛑 Stopping scheduler after {self.consecutive_failures} consecutive failures")
                    self.save_stats()
                    return schedule.CancelJob
                    
        except subprocess.TimeoutExpired:
            self.consecutive_failures += 1
            self.logger.error(f"⏱️  Scraper timed out after 5 minutes")
            
        except Exception as e:
            self.consecutive_failures += 1
            self.logger.error(f"💥 Unexpected error running scraper: {str(e)}")
            
        # Update and save statistics
        self.save_stats()
        
        # Log summary
        success_rate = (self.successful_runs / self.total_runs) * 100
        self.logger.info(f"📈 Stats: {self.successful_runs}/{self.total_runs} successful ({success_rate:.1f}%)")
        self.logger.info("="*60)
        
    def check_csv_updated(self):
        """Check if the CSV file was recently updated"""
        csv_file = "direct_retailer_prices.csv"
        try:
            if os.path.exists(csv_file):
                file_mod_time = os.path.getmtime(csv_file)
                current_time = time.time()
                # Consider "updated" if modified within last 2 minutes
                return (current_time - file_mod_time) < 120
            return False
        except:
            return False
            
    def save_stats(self):
        """Save running statistics"""
        stats = {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": (self.successful_runs / self.total_runs * 100) if self.total_runs > 0 else 0,
            "last_run": datetime.now().isoformat(),
            "config": self.config
        }
        
        try:
            with open(self.config["stats_file"], 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save stats: {e}")
            
    def start_scheduler(self, interval_minutes=None):
        """Start the automated scheduler"""
        if interval_minutes:
            self.config["interval_minutes"] = interval_minutes
            
        self.logger.info("🎯 CheapAmmo Automatic Scraper Scheduler Starting")
        self.logger.info("="*60)
        self.logger.info(f"📂 Working directory: {os.getcwd()}")
        self.logger.info(f"🐍 Scraper script: {self.config['scraper_script']}")
        self.logger.info(f"⏰ Interval: Every {self.config['interval_minutes']} minutes")
        self.logger.info(f"📋 Log file: {self.config['log_file']}")
        self.logger.info(f"📊 Stats file: {self.config['stats_file']}")
        self.logger.info("="*60)
        
        # Check if scraper script exists
        if not os.path.exists(self.config["scraper_script"]):
            self.logger.error(f"❌ Scraper script not found: {self.config['scraper_script']}")
            return
            
        # Schedule the job
        schedule.every(self.config["interval_minutes"]).minutes.do(self.run_scraper)
        
        # Run once immediately
        self.logger.info("🚀 Running initial scrape...")
        self.run_scraper()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Scheduler stopped by user")
            self.save_stats()
            
        except Exception as e:
            self.logger.error(f"💥 Scheduler error: {str(e)}")
            self.save_stats()

def main():
    """Main function with command line options"""
    import sys
    
    scheduler = AmmoScraperScheduler()
    
    # Parse command line arguments
    interval = 30  # Default 30 minutes
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
            print(f"Using custom interval: {interval} minutes")
        except ValueError:
            print("Invalid interval specified, using default 30 minutes")
    
    print(f"🎯 Starting CheapAmmo scraper every {interval} minutes")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    scheduler.start_scheduler(interval)

if __name__ == "__main__":
    main() 