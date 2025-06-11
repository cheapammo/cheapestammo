#!/usr/bin/env python3
"""
Simple test script for the ammunition scraper
"""

import sys
import logging
from database import db_manager
from sgammo_scraper import SGAmmoScraper
from config import RETAILERS

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and setup"""
    logger.info("Testing database connection...")
    
    try:
        # Create tables
        db_manager.create_tables()
        logger.info("✓ Database tables created successfully")
        
        # Test adding a retailer
        retailer = db_manager.add_retailer(
            name="Test Retailer",
            website="https://test.com",
            base_url="https://test.com"
        )
        logger.info(f"✓ Test retailer added: {retailer.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False

def test_scraper_basic():
    """Test basic scraper functionality"""
    logger.info("Testing SGAmmo scraper...")
    
    try:
        # Initialize scraper
        scraper = SGAmmoScraper(RETAILERS['sgammo'])
        logger.info("✓ Scraper initialized")
        
        # Test session setup
        scraper.setup_session()
        logger.info("✓ Session setup completed")
        
        # Test making a simple request
        response = scraper.make_request(scraper.base_url)
        if response and response.status_code == 200:
            logger.info("✓ Base URL request successful")
        else:
            logger.warning("⚠ Base URL request failed or returned non-200 status")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Scraper test failed: {e}")
        return False

def test_product_extraction():
    """Test product data extraction"""
    logger.info("Testing product data extraction...")
    
    try:
        scraper = SGAmmoScraper(RETAILERS['sgammo'])
        scraper.setup_session()
        
        # Try to get a few product URLs
        logger.info("Getting product URLs...")
        product_urls = scraper.get_product_urls()
        
        if product_urls:
            logger.info(f"✓ Found {len(product_urls)} product URLs")
            
            # Test scraping first few products
            test_count = min(3, len(product_urls))
            logger.info(f"Testing extraction on {test_count} products...")
            
            for i, url in enumerate(product_urls[:test_count]):
                logger.info(f"Testing product {i+1}: {url}")
                
                try:
                    scraper.scrape_product_page(url)
                    logger.info(f"✓ Product {i+1} processed")
                except Exception as e:
                    logger.warning(f"⚠ Product {i+1} failed: {e}")
            
            logger.info(f"✓ Extraction test completed. Found {scraper.products_found} valid products")
            return True
        else:
            logger.warning("⚠ No product URLs found")
            return False
            
    except Exception as e:
        logger.error(f"✗ Product extraction test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    logger.info("=" * 50)
    logger.info("AMMUNITION SCRAPER TEST SUITE")
    logger.info("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Scraper Basic Functionality", test_scraper_basic),
        ("Product Data Extraction", test_product_extraction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 50)
    
    if passed == total:
        logger.info("🎉 All tests passed! Scraper is ready to use.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 