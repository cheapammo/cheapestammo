#!/usr/bin/env python3
"""
Main scraper runner for ammunition price aggregation
"""

import logging
import sys
import argparse
from datetime import datetime
from config import RETAILERS, LOGGING_CONFIG
from database import db_manager
from sgammo_scraper import SGAmmoScraper

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['file']),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ScraperRunner:
    def __init__(self):
        self.scrapers = {}
        self.setup_scrapers()
    
    def setup_scrapers(self):
        """Initialize all enabled scrapers"""
        logger.info("Setting up scrapers...")
        
        # SGAmmo scraper
        if RETAILERS['sgammo']['enabled']:
            self.scrapers['sgammo'] = SGAmmoScraper(RETAILERS['sgammo'])
            logger.info("SGAmmo scraper enabled")
        
        # Add more scrapers here as they're implemented
        # if RETAILERS['bulkammo']['enabled']:
        #     self.scrapers['bulkammo'] = BulkAmmoScraper(RETAILERS['bulkammo'])
        
        logger.info(f"Initialized {len(self.scrapers)} scrapers")
    
    def run_all_scrapers(self):
        """Run all enabled scrapers"""
        logger.info("Starting scraping session for all retailers")
        start_time = datetime.now()
        
        total_products = 0
        total_errors = 0
        
        for retailer_name, scraper in self.scrapers.items():
            logger.info(f"Starting scraper for {retailer_name}")
            
            try:
                scraper.scrape_products()
                total_products += scraper.products_found
                total_errors += len(scraper.errors)
                
                logger.info(f"Completed {retailer_name}: "
                          f"{scraper.products_found} products, "
                          f"{len(scraper.errors)} errors")
                
            except Exception as e:
                logger.error(f"Scraper {retailer_name} failed: {e}")
                total_errors += 1
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"Scraping session completed in {duration}")
        logger.info(f"Total products found: {total_products}")
        logger.info(f"Total errors: {total_errors}")
        
        return {
            'duration': duration,
            'total_products': total_products,
            'total_errors': total_errors,
            'scrapers_run': len(self.scrapers)
        }
    
    def run_single_scraper(self, retailer_name):
        """Run a single scraper by name"""
        if retailer_name not in self.scrapers:
            logger.error(f"Scraper {retailer_name} not found or not enabled")
            return False
        
        logger.info(f"Running single scraper: {retailer_name}")
        
        try:
            scraper = self.scrapers[retailer_name]
            scraper.scrape_products()
            
            logger.info(f"Completed {retailer_name}: "
                      f"{scraper.products_found} products, "
                      f"{len(scraper.errors)} errors")
            return True
            
        except Exception as e:
            logger.error(f"Scraper {retailer_name} failed: {e}")
            return False
    
    def test_scraper(self, retailer_name, limit_pages=1):
        """Test a scraper with limited pages"""
        if retailer_name not in self.scrapers:
            logger.error(f"Scraper {retailer_name} not found or not enabled")
            return False
        
        logger.info(f"Testing scraper: {retailer_name} (limited to {limit_pages} pages)")
        
        try:
            scraper = self.scrapers[retailer_name]
            
            # Override the get_product_urls method to limit results
            original_method = scraper.get_product_urls
            def limited_get_product_urls():
                urls = original_method()
                return urls[:limit_pages] if urls else []
            
            scraper.get_product_urls = limited_get_product_urls
            scraper.scrape_products()
            
            logger.info(f"Test completed for {retailer_name}: "
                      f"{scraper.products_found} products, "
                      f"{len(scraper.errors)} errors")
            return True
            
        except Exception as e:
            logger.error(f"Test scraper {retailer_name} failed: {e}")
            return False

def setup_database():
    """Initialize database tables"""
    try:
        logger.info("Setting up database...")
        db_manager.create_tables()
        logger.info("Database setup completed")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Ammunition Price Scraper')
    parser.add_argument('--setup-db', action='store_true', help='Setup database tables')
    parser.add_argument('--scraper', type=str, help='Run specific scraper (sgammo, bulkammo, etc.)')
    parser.add_argument('--test', type=str, help='Test specific scraper with limited pages')
    parser.add_argument('--all', action='store_true', help='Run all enabled scrapers')
    
    args = parser.parse_args()
    
    # Setup database if requested
    if args.setup_db:
        if not setup_database():
            sys.exit(1)
        if not any([args.scraper, args.test, args.all]):
            logger.info("Database setup completed. Use --all, --scraper, or --test to run scrapers.")
            sys.exit(0)
    
    # Initialize scraper runner
    runner = ScraperRunner()
    
    if not runner.scrapers:
        logger.error("No scrapers enabled. Check configuration.")
        sys.exit(1)
    
    # Run based on arguments
    if args.test:
        success = runner.test_scraper(args.test, limit_pages=5)
        sys.exit(0 if success else 1)
    
    elif args.scraper:
        success = runner.run_single_scraper(args.scraper)
        sys.exit(0 if success else 1)
    
    elif args.all:
        results = runner.run_all_scrapers()
        logger.info(f"Session summary: {results}")
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 