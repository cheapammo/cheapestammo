import random
import time
import re
import logging
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
from config import SCRAPING_CONFIG, DATA_CONFIG

class ScrapingUtils:
    def __init__(self):
        self.ua = UserAgent()
        self.logger = logging.getLogger(__name__)
    
    def get_random_user_agent(self):
        """Get a random user agent string"""
        try:
            return self.ua.random
        except:
            # Fallback user agents if fake_useragent fails
            fallback_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
            ]
            return random.choice(fallback_agents)
    
    def get_headers(self):
        """Get randomized headers for requests"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(
            SCRAPING_CONFIG['delay_min'], 
            SCRAPING_CONFIG['delay_max']
        )
        time.sleep(delay)
        return delay
    
    def clean_price(self, price_text):
        """Extract and clean price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extra whitespace
        price_text = str(price_text).strip()
        
        # Extract price using regex
        price_match = re.search(r'[\$]?([0-9,]+\.?[0-9]*)', price_text)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            try:
                price = float(price_str)
                # Validate price range
                if (DATA_CONFIG['price_validation']['min_price'] <= price <= 
                    DATA_CONFIG['price_validation']['max_price'] * 100):  # Allow for bulk pricing
                    return price
            except ValueError:
                pass
        
        return None
    
    def extract_caliber(self, text):
        """Extract caliber from product name or description"""
        if not text:
            return None
        
        text = text.upper()
        
        # Common caliber patterns
        caliber_patterns = [
            r'9MM|9 MM',
            r'\.223|223 REM|223 REMINGTON',
            r'5\.56|5\.56X45|5\.56 NATO',
            r'\.308|308 WIN|308 WINCHESTER',
            r'\.45 ACP|45 ACP|\.45 AUTO',
            r'\.40 S&W|40 S&W|\.40 SW',
            r'\.380|380 ACP|380 AUTO',
            r'7\.62X39|7\.62 X 39',
            r'\.22 LR|22 LR|\.22LR',
            r'300 AAC|300 BLACKOUT|300 BLK',
            r'6\.5 CREEDMOOR|6\.5 CM',
            r'\.30-06|30-06|30\.06',
        ]
        
        for pattern in caliber_patterns:
            if re.search(pattern, text):
                # Map to standardized caliber names
                for standard_cal, variations in DATA_CONFIG['caliber_mapping'].items():
                    for variation in variations:
                        if variation.upper() in text:
                            return standard_cal
        
        return None
    
    def extract_grain_weight(self, text):
        """Extract grain weight from text"""
        if not text:
            return None
        
        grain_match = re.search(r'(\d+)\s*GR|(\d+)\s*GRAIN', text.upper())
        if grain_match:
            try:
                return int(grain_match.group(1) or grain_match.group(2))
            except ValueError:
                pass
        
        return None
    
    def extract_bullet_type(self, text):
        """Extract bullet type from text"""
        if not text:
            return None
        
        text = text.upper()
        
        bullet_types = {
            'FMJ': ['FMJ', 'FULL METAL JACKET'],
            'HP': ['HP', 'HOLLOW POINT', 'HOLLOWPOINT'],
            'SP': ['SP', 'SOFT POINT', 'SOFTPOINT'],
            'JHP': ['JHP', 'JACKETED HOLLOW POINT'],
            'JSP': ['JSP', 'JACKETED SOFT POINT'],
            'TMJ': ['TMJ', 'TOTAL METAL JACKET'],
            'LRN': ['LRN', 'LEAD ROUND NOSE'],
            'LSWC': ['LSWC', 'LEAD SEMI WADCUTTER'],
            'MATCH': ['MATCH', 'MATCH GRADE'],
            'BALL': ['BALL', 'BALL AMMO'],
        }
        
        for bullet_type, variations in bullet_types.items():
            for variation in variations:
                if variation in text:
                    return bullet_type
        
        return None
    
    def extract_quantity(self, text):
        """Extract quantity/count from text"""
        if not text:
            return None
        
        # Look for patterns like "50 rounds", "20 ct", "100 count", etc.
        quantity_patterns = [
            r'(\d+)\s*ROUNDS?',
            r'(\d+)\s*CT',
            r'(\d+)\s*COUNT',
            r'(\d+)\s*PCS?',
            r'(\d+)\s*PIECES?',
            r'BOX OF (\d+)',
            r'(\d+)/BOX',
        ]
        
        text_upper = text.upper()
        for pattern in quantity_patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def calculate_price_per_round(self, price, quantity):
        """Calculate price per round"""
        if not price or not quantity or quantity == 0:
            return None
        
        try:
            ppr = price / quantity
            # Validate reasonable price per round
            if (DATA_CONFIG['price_validation']['min_price'] <= ppr <= 
                DATA_CONFIG['price_validation']['max_price']):
                return round(ppr, 4)
        except (TypeError, ZeroDivisionError):
            pass
        
        return None
    
    def is_in_stock(self, text):
        """Determine if product is in stock based on text"""
        if not text:
            return False
        
        text = text.upper()
        
        # In stock indicators
        in_stock_indicators = [
            'IN STOCK', 'AVAILABLE', 'ADD TO CART', 'BUY NOW', 
            'PURCHASE', 'ORDER NOW', 'SHIPS'
        ]
        
        # Out of stock indicators
        out_of_stock_indicators = [
            'OUT OF STOCK', 'SOLD OUT', 'UNAVAILABLE', 'BACKORDER',
            'NOTIFY WHEN AVAILABLE', 'EMAIL WHEN AVAILABLE'
        ]
        
        # Check out of stock first (more specific)
        for indicator in out_of_stock_indicators:
            if indicator in text:
                return False
        
        # Check in stock indicators
        for indicator in in_stock_indicators:
            if indicator in text:
                return True
        
        # Default to False if unclear
        return False
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return None
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\-\(\)\/]', '', text)
        
        return text.strip()
    
    def build_absolute_url(self, base_url, relative_url):
        """Build absolute URL from base and relative URLs"""
        if not relative_url:
            return None
        
        if relative_url.startswith('http'):
            return relative_url
        
        return urljoin(base_url, relative_url)
    
    def is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

# Initialize utils instance
scraping_utils = ScrapingUtils() 