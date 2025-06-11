from base_scraper import BaseScraper
from utils import scraping_utils
import re
from urllib.parse import urljoin

class SGAmmoScraper(BaseScraper):
    def __init__(self, retailer_config):
        super().__init__(retailer_config)
        
        # SGAmmo specific configuration
        self.category_urls = [
            '/catalog/rifle-ammo',
            '/catalog/handgun-ammo',
            '/catalog/rimfire-ammo',
            '/catalog/shotgun-ammo'
        ]
    
    def get_product_urls(self):
        """Get product URLs from category pages"""
        product_urls = []
        
        for category_url in self.category_urls:
            full_url = urljoin(self.base_url, category_url)
            self.logger.info(f"Scraping category: {full_url}")
            
            try:
                response = self.make_request(full_url)
                if not response:
                    continue
                
                soup = self.parse_html(response)
                if not soup:
                    continue
                
                # Find product links on category page
                category_products = self._extract_category_products(soup)
                product_urls.extend(category_products)
                
                self.logger.info(f"Found {len(category_products)} products in {category_url}")
                
            except Exception as e:
                self.logger.error(f"Error scraping category {category_url}: {e}")
                continue
        
        return product_urls
    
    def _extract_category_products(self, soup):
        """Extract product URLs from category page"""
        product_urls = []
        
        # SGAmmo uses product tiles with links
        # Look for product containers (adjust selectors based on actual HTML structure)
        product_containers = soup.find_all('div', class_=['product-item', 'item', 'product'])
        
        if not product_containers:
            # Try alternative selectors
            product_containers = soup.find_all('a', href=re.compile(r'/product/|/item/|/p/'))
        
        for container in product_containers:
            try:
                # Find product link
                link = None
                if container.name == 'a':
                    link = container
                else:
                    link = container.find('a', href=True)
                
                if link and link.get('href'):
                    product_url = scraping_utils.build_absolute_url(self.base_url, link['href'])
                    if product_url and scraping_utils.is_valid_url(product_url):
                        product_urls.append(product_url)
                        
            except Exception as e:
                self.logger.debug(f"Error extracting product URL: {e}")
                continue
        
        return list(set(product_urls))  # Remove duplicates
    
    def scrape_product_page(self, url):
        """Scrape individual product page"""
        try:
            response = self.make_request(url)
            if not response:
                return
            
            soup = self.parse_html(response)
            if not soup:
                return
            
            # Extract product data
            product_data = self._extract_product_details(soup, url)
            
            if product_data:
                self.products_found += 1
                if self.save_product(product_data):
                    self.logger.debug(f"Successfully scraped: {product_data['name']}")
                else:
                    self.logger.warning(f"Failed to save: {product_data['name']}")
            
        except Exception as e:
            self.logger.error(f"Error scraping product page {url}: {e}")
            self.errors.append(f"Product page error: {url} - {str(e)}")
    
    def _extract_product_details(self, soup, product_url=None):
        """Extract product details from SGAmmo product page"""
        try:
            product_data = {}
            
            # Product name (adjust selector based on actual HTML)
            name_element = soup.find('h1') or soup.find('h2') or soup.find(class_=['product-title', 'title'])
            if name_element:
                product_data['name'] = scraping_utils.clean_text(name_element.get_text())
            else:
                self.logger.warning(f"No product name found for {product_url}")
                return None
            
            # Description
            desc_element = soup.find(class_=['description', 'product-description']) or soup.find('div', class_='desc')
            if desc_element:
                product_data['description'] = scraping_utils.clean_text(desc_element.get_text())
            
            # Price - look for various price selectors
            price_element = (soup.find(class_=['price', 'product-price', 'current-price']) or 
                           soup.find('span', string=re.compile(r'\$\d+')) or
                           soup.find(text=re.compile(r'\$\d+')))
            
            if price_element:
                if hasattr(price_element, 'get_text'):
                    price_text = price_element.get_text()
                else:
                    price_text = str(price_element)
                
                product_data['price'] = scraping_utils.clean_price(price_text)
            
            if not product_data.get('price'):
                self.logger.warning(f"No price found for {product_data.get('name', 'Unknown')}")
                return None
            
            # Extract caliber from name/description
            full_text = f"{product_data.get('name', '')} {product_data.get('description', '')}"
            product_data['caliber'] = scraping_utils.extract_caliber(full_text)
            
            if not product_data.get('caliber'):
                self.logger.warning(f"No caliber found for {product_data.get('name', 'Unknown')}")
                return None
            
            # Extract other details
            product_data['grain_weight'] = scraping_utils.extract_grain_weight(full_text)
            product_data['bullet_type'] = scraping_utils.extract_bullet_type(full_text)
            product_data['quantity'] = scraping_utils.extract_quantity(full_text)
            
            # Default quantity if not found
            if not product_data.get('quantity'):
                # Try to infer from common patterns
                if 'case' in full_text.lower():
                    product_data['quantity'] = 1000  # Common case size
                elif 'box' in full_text.lower():
                    product_data['quantity'] = 50   # Common box size
                else:
                    product_data['quantity'] = 20   # Default assumption
            
            # Calculate price per round
            product_data['price_per_round'] = scraping_utils.calculate_price_per_round(
                product_data['price'], product_data['quantity']
            )
            
            if not product_data.get('price_per_round'):
                self.logger.warning(f"Could not calculate price per round for {product_data.get('name', 'Unknown')}")
                return None
            
            # Stock status
            stock_text = soup.get_text()
            product_data['in_stock'] = scraping_utils.is_in_stock(stock_text)
            
            # Product URL
            product_data['product_url'] = product_url
            
            # Try to find product image
            img_element = soup.find('img', class_=['product-image', 'main-image']) or soup.find('img')
            if img_element and img_element.get('src'):
                product_data['image_url'] = scraping_utils.build_absolute_url(
                    self.base_url, img_element['src']
                )
            
            # Extract manufacturer from name
            name_parts = product_data['name'].split()
            if name_parts:
                # First word is often the manufacturer
                potential_manufacturer = name_parts[0]
                common_manufacturers = [
                    'Federal', 'Winchester', 'Remington', 'Hornady', 'PMC', 
                    'Fiocchi', 'Sellier', 'Aguila', 'CCI', 'Blazer'
                ]
                if potential_manufacturer in common_manufacturers:
                    product_data['manufacturer'] = potential_manufacturer
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error extracting product details: {e}")
            return None

# Example usage function
def scrape_sgammo():
    """Function to run SGAmmo scraper"""
    from config import RETAILERS
    
    if not RETAILERS['sgammo']['enabled']:
        print("SGAmmo scraper is disabled in config")
        return
    
    scraper = SGAmmoScraper(RETAILERS['sgammo'])
    scraper.scrape_products()

if __name__ == "__main__":
    scrape_sgammo() 