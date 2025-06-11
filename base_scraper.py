import requests
import logging
import time
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import scraping_utils
from database import db_manager
from config import SCRAPING_CONFIG, PROXY_CONFIG

class BaseScraper(ABC):
    def __init__(self, retailer_config):
        self.retailer_config = retailer_config
        self.retailer_name = retailer_config['name']
        self.base_url = retailer_config['base_url']
        self.search_url = retailer_config['search_url']
        
        self.logger = logging.getLogger(f"{__name__}.{self.retailer_name}")
        self.session = requests.Session()
        self.driver = None
        
        # Statistics
        self.products_found = 0
        self.products_updated = 0
        self.products_new = 0
        self.errors = []
        
        # Get or create retailer in database
        self.retailer_db = db_manager.add_retailer(
            name=self.retailer_name,
            website=self.base_url,
            base_url=self.base_url
        )
    
    def setup_session(self):
        """Setup requests session with headers and proxies"""
        self.session.headers.update(scraping_utils.get_headers())
        
        if PROXY_CONFIG['enabled'] and PROXY_CONFIG['proxy_list']:
            proxy = self._get_random_proxy()
            if proxy:
                self.session.proxies.update(proxy)
    
    def setup_selenium(self, headless=True):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--user-agent={scraping_utils.get_random_user_agent()}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(SCRAPING_CONFIG['timeout'])
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            return False
    
    def make_request(self, url, use_selenium=False, retries=None):
        """Make HTTP request with error handling and retries"""
        if retries is None:
            retries = SCRAPING_CONFIG['retries']
        
        for attempt in range(retries + 1):
            try:
                if use_selenium:
                    return self._selenium_request(url)
                else:
                    return self._requests_request(url)
                    
            except Exception as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries:
                    scraping_utils.random_delay()
                else:
                    self.logger.error(f"All {retries + 1} attempts failed for {url}")
                    self.errors.append(f"Request failed: {url} - {str(e)}")
                    return None
    
    def _requests_request(self, url):
        """Make request using requests library"""
        response = self.session.get(
            url, 
            timeout=SCRAPING_CONFIG['timeout'],
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Add delay between requests
        scraping_utils.random_delay()
        
        return response
    
    def _selenium_request(self, url):
        """Make request using Selenium WebDriver"""
        if not self.driver:
            if not self.setup_selenium():
                raise Exception("Selenium driver not available")
        
        self.driver.get(url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Add delay between requests
        scraping_utils.random_delay()
        
        return self.driver
    
    def parse_html(self, response):
        """Parse HTML response into BeautifulSoup object"""
        if hasattr(response, 'text'):
            # requests response
            return BeautifulSoup(response.text, 'html.parser')
        elif hasattr(response, 'page_source'):
            # selenium response
            return BeautifulSoup(response.page_source, 'html.parser')
        else:
            return None
    
    def extract_product_data(self, product_element, product_url=None):
        """Extract product data from HTML element - to be implemented by subclasses"""
        try:
            # This method should be overridden by each retailer scraper
            product_data = self._extract_product_details(product_element, product_url)
            
            if product_data and self._validate_product_data(product_data):
                product_data['retailer_id'] = self.retailer_db.id
                return product_data
            
        except Exception as e:
            self.logger.error(f"Error extracting product data: {e}")
            self.errors.append(f"Product extraction error: {str(e)}")
        
        return None
    
    def _validate_product_data(self, product_data):
        """Validate extracted product data"""
        required_fields = ['name', 'caliber', 'price', 'quantity', 'price_per_round']
        
        for field in required_fields:
            if not product_data.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate price range
        price = product_data.get('price')
        if price and (price < 0.1 or price > 10000):
            self.logger.warning(f"Price out of range: {price}")
            return False
        
        return True
    
    def save_product(self, product_data):
        """Save product data to database"""
        try:
            success = db_manager.upsert_product(product_data)
            if success:
                self.products_updated += 1
                self.logger.debug(f"Saved product: {product_data['name']}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving product: {e}")
            self.errors.append(f"Database error: {str(e)}")
            return False
    
    def scrape_products(self):
        """Main scraping method - to be implemented by subclasses"""
        self.logger.info(f"Starting scrape for {self.retailer_name}")
        
        try:
            self.setup_session()
            
            # Get product URLs or pages to scrape
            urls_to_scrape = self.get_product_urls()
            
            if not urls_to_scrape:
                self.logger.warning("No URLs found to scrape")
                return
            
            self.logger.info(f"Found {len(urls_to_scrape)} URLs to scrape")
            
            # Scrape each URL
            for url in urls_to_scrape:
                try:
                    self.scrape_product_page(url)
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {e}")
                    self.errors.append(f"Page scraping error: {url} - {str(e)}")
                    continue
            
            # Log results
            self.log_scraping_results()
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            self.errors.append(f"Scraping failed: {str(e)}")
        finally:
            self.cleanup()
    
    def log_scraping_results(self):
        """Log scraping session results"""
        status = "success" if not self.errors else "partial" if self.products_found > 0 else "failed"
        error_message = "; ".join(self.errors) if self.errors else None
        
        db_manager.log_scraping_session(
            retailer_id=self.retailer_db.id,
            status=status,
            products_found=self.products_found,
            products_updated=self.products_updated,
            products_new=self.products_new,
            error_message=error_message
        )
        
        self.logger.info(f"Scraping completed - Found: {self.products_found}, "
                        f"Updated: {self.products_updated}, Errors: {len(self.errors)}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()
    
    def _get_random_proxy(self):
        """Get random proxy from configuration"""
        if PROXY_CONFIG['proxy_list']:
            import random
            proxy_url = random.choice(PROXY_CONFIG['proxy_list'])
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        return None
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def get_product_urls(self):
        """Get list of product URLs to scrape"""
        pass
    
    @abstractmethod
    def scrape_product_page(self, url):
        """Scrape individual product page"""
        pass
    
    @abstractmethod
    def _extract_product_details(self, product_element, product_url=None):
        """Extract product details from HTML element"""
        pass 