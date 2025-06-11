#!/usr/bin/env python3
"""
Combined Monitor - Runs both web scraping and email monitoring
"""

import threading
import time
import logging
import signal
import sys
from datetime import datetime

from email_monitor import EmailMonitor
from direct_retailer_scraper import DirectRetailerScraper
from config import EMAIL_CONFIG

class CombinedMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.email_monitor = EmailMonitor()
        self.web_scraper = DirectRetailerScraper()
        self.running = False
        self.threads = []
        
    def run_email_monitoring(self):
        """Run email monitoring in a separate thread"""
        self.logger.info("Starting email monitoring thread...")
        
        while self.running:
            try:
                # Run one monitoring cycle
                result = self.email_monitor.run_monitoring_cycle()
                
                self.logger.info(
                    f"Email cycle complete: {result['emails_checked']} checked, "
                    f"{result['deals_found']} deals found"
                )
                
                # Wait for next cycle
                time.sleep(EMAIL_CONFIG['check_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in email monitoring: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def run_web_scraping(self):
        """Run web scraping in a separate thread"""
        self.logger.info("Starting web scraping thread...")
        
        while self.running:
            try:
                # Run scraping cycle
                self.logger.info("Running web scraping cycle...")
                self.web_scraper.run_all_retailers()
                
                self.logger.info("Web scraping cycle complete")
                
                # Wait 30 minutes before next scrape
                time.sleep(1800)  # 30 minutes
                
            except Exception as e:
                self.logger.error(f"Error in web scraping: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def start(self):
        """Start both monitoring systems"""
        self.running = True
        
        # Create and start threads
        email_thread = threading.Thread(target=self.run_email_monitoring, name="EmailMonitor")
        scraper_thread = threading.Thread(target=self.run_web_scraping, name="WebScraper")
        
        email_thread.daemon = True
        scraper_thread.daemon = True
        
        self.threads = [email_thread, scraper_thread]
        
        # Start threads
        email_thread.start()
        scraper_thread.start()
        
        self.logger.info("Combined monitoring started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop all monitoring"""
        self.logger.info("Stopping combined monitoring...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=10)
        
        self.logger.info("Combined monitoring stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('combined_monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create monitor
    monitor = CombinedMonitor()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    # Print startup info
    print("=" * 60)
    print("🎯 CheapAmmo Combined Monitor")
    print("=" * 60)
    print("📧 Email Monitoring: Active")
    print(f"   - Check interval: {EMAIL_CONFIG['check_interval']} seconds")
    print("🌐 Web Scraping: Active")
    print("   - Check interval: 30 minutes")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("")
    
    # Start monitoring
    monitor.start()


if __name__ == "__main__":
    main()