#!/usr/bin/env python3
"""
MVP Ammunition Price Scraper
Uses only built-in Python libraries - no external dependencies needed!
"""

import urllib.request
import urllib.parse
import json
import csv
import re
import time
import random
from datetime import datetime
from html.parser import HTMLParser

class SimpleAmmoParser(HTMLParser):
    """Simple HTML parser to extract product data"""
    
    def __init__(self):
        super().__init__()
        self.products = []
        self.current_product = {}
        self.in_product = False
        self.in_price = False
        self.in_title = False
        self.current_data = ""
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Look for product containers (common patterns)
        if tag == 'div' and any('product' in str(v).lower() for v in attrs_dict.values()):
            self.in_product = True
            self.current_product = {}
        
        # Look for price elements
        elif tag in ['span', 'div', 'p'] and any('price' in str(v).lower() for v in attrs_dict.values()):
            self.in_price = True
        
        # Look for title/name elements
        elif tag in ['h1', 'h2', 'h3', 'h4', 'a'] and any('title' in str(v).lower() or 'name' in str(v).lower() for v in attrs_dict.values()):
            self.in_title = True
        
        # Capture links
        elif tag == 'a' and 'href' in attrs_dict:
            if self.in_product:
                self.current_product['url'] = attrs_dict['href']
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_product:
            if self.current_product:
                self.products.append(self.current_product.copy())
            self.in_product = False
        elif self.in_price:
            self.in_price = False
        elif self.in_title:
            self.in_title = False
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        
        if self.in_price and '$' in data:
            self.current_product['price_text'] = data
        elif self.in_title and len(data) > 5:
            self.current_product['name'] = data

class MVPScraper:
    def __init__(self):
        self.products = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
    
    def make_request(self, url):
        """Make HTTP request with random user agent"""
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', random.choice(self.user_agents))
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    return response.read().decode('utf-8', errors='ignore')
            return None
        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def extract_price(self, price_text):
        """Extract price from text"""
        if not price_text:
            return None
        
        # Find price pattern
        price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', price_text)
        if price_match:
            try:
                return float(price_match.group(1).replace(',', ''))
            except ValueError:
                pass
        return None
    
    def extract_caliber(self, text):
        """Extract caliber from text"""
        if not text:
            return None
        
        text = text.upper()
        
        # Common calibers
        calibers = {
            '9MM': ['9MM', '9 MM', '9X19'],
            '.223': ['.223', '223 REM'],
            '5.56': ['5.56', '5.56X45', '5.56 NATO'],
            '.308': ['.308', '308 WIN'],
            '.45 ACP': ['.45 ACP', '45 ACP'],
            '.40 S&W': ['.40 S&W', '40 S&W'],
            '.380': ['.380', '380 ACP'],
            '22LR': ['22LR', '.22 LR', '22 LONG RIFLE'],
        }
        
        for standard, variations in calibers.items():
            for variation in variations:
                if variation in text:
                    return standard
        
        return None
    
    def extract_quantity(self, text):
        """Extract quantity from text"""
        if not text:
            return None
        
        # Look for quantity patterns
        patterns = [
            r'(\d+)\s*ROUNDS?',
            r'(\d+)\s*CT',
            r'(\d+)\s*COUNT',
            r'BOX OF (\d+)',
            r'(\d+)/BOX',
        ]
        
        text_upper = text.upper()
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return 50  # Default assumption
    
    def scrape_ammoseek_api(self):
        """Scrape using a simple approach - look for public data"""
        print("🎯 Scraping ammunition data...")
        
        # Simple test data for MVP (in real version, this would scrape actual sites)
        sample_data = [
            {
                'name': '9mm Luger 115gr FMJ Federal',
                'price': 24.99,
                'quantity': 50,
                'caliber': '9MM',
                'retailer': 'Sample Store 1',
                'in_stock': True
            },
            {
                'name': '.223 Remington 55gr FMJ Winchester',
                'price': 18.99,
                'quantity': 20,
                'caliber': '.223',
                'retailer': 'Sample Store 2',
                'in_stock': True
            },
            {
                'name': '.308 Winchester 150gr SP Hornady',
                'price': 35.99,
                'quantity': 20,
                'caliber': '.308',
                'retailer': 'Sample Store 3',
                'in_stock': False
            },
            {
                'name': '5.56x45 NATO 62gr FMJ PMC',
                'price': 28.99,
                'quantity': 30,
                'caliber': '5.56',
                'retailer': 'Sample Store 4',
                'in_stock': True
            },
            {
                'name': '.45 ACP 230gr FMJ Remington',
                'price': 42.99,
                'quantity': 50,
                'caliber': '.45 ACP',
                'retailer': 'Sample Store 5',
                'in_stock': True
            }
        ]
        
        # Process sample data
        for item in sample_data:
            product = {
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'price_per_round': round(item['price'] / item['quantity'], 4),
                'caliber': item['caliber'],
                'retailer': item['retailer'],
                'in_stock': item['in_stock'],
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.products.append(product)
            print(f"✓ Found: {product['name']} - ${product['price']} (${product['price_per_round']}/round)")
        
        return len(self.products)
    
    def scrape_gun_deals_reddit(self):
        """Try to get some real data from gun deals (public RSS/JSON if available)"""
        print("🔍 Looking for real ammunition deals...")
        
        try:
            # Try Reddit's JSON API for gun deals (public data)
            url = "https://www.reddit.com/r/gundeals/search.json?q=ammo&sort=new&limit=10"
            
            html = self.make_request(url)
            if html:
                try:
                    data = json.loads(html)
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        title = post_data.get('title', '')
                        
                        if 'ammo' in title.lower() or any(cal in title.upper() for cal in ['9MM', '.223', '.308', '5.56']):
                            # Extract basic info from title
                            caliber = self.extract_caliber(title)
                            
                            # Try to extract price from title
                            price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', title)
                            price = None
                            if price_match:
                                try:
                                    price = float(price_match.group(1).replace(',', ''))
                                except:
                                    pass
                            
                            if caliber and price:
                                quantity = self.extract_quantity(title) or 50
                                
                                product = {
                                    'name': title[:100],  # Truncate long titles
                                    'price': price,
                                    'quantity': quantity,
                                    'price_per_round': round(price / quantity, 4),
                                    'caliber': caliber,
                                    'retailer': 'Reddit Deal',
                                    'in_stock': True,
                                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                self.products.append(product)
                                print(f"✓ Reddit Deal: {caliber} - ${price} (${product['price_per_round']}/round)")
                
                except json.JSONDecodeError:
                    print("⚠ Could not parse Reddit data")
            
        except Exception as e:
            print(f"⚠ Reddit scraping failed: {e}")
        
        return len([p for p in self.products if p['retailer'] == 'Reddit Deal'])
    
    def save_to_csv(self, filename='ammo_prices.csv'):
        """Save products to CSV file"""
        if not self.products:
            print("No products to save")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'caliber', 'price', 'quantity', 'price_per_round', 'retailer', 'in_stock', 'scraped_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in self.products:
                    writer.writerow(product)
            
            print(f"✓ Saved {len(self.products)} products to {filename}")
            
        except Exception as e:
            print(f"✗ Failed to save CSV: {e}")
    
    def display_results(self):
        """Display results in terminal"""
        if not self.products:
            print("No products found")
            return
        
        print("\n" + "="*80)
        print("AMMUNITION PRICE RESULTS")
        print("="*80)
        
        # Sort by price per round
        sorted_products = sorted(self.products, key=lambda x: x['price_per_round'])
        
        for product in sorted_products:
            stock_status = "✓ IN STOCK" if product['in_stock'] else "✗ OUT OF STOCK"
            print(f"""
Name: {product['name']}
Caliber: {product['caliber']}
Price: ${product['price']} ({product['quantity']} rounds)
Price/Round: ${product['price_per_round']}
Retailer: {product['retailer']}
Status: {stock_status}
{'-'*60}""")
    
    def run(self):
        """Run the MVP scraper"""
        print("🚀 Starting MVP Ammunition Price Scraper")
        print("=" * 50)
        
        # Get sample data
        sample_count = self.scrape_ammoseek_api()
        
        # Try to get some real data
        real_count = self.scrape_gun_deals_reddit()
        
        # Add small delay to be respectful
        time.sleep(1)
        
        print(f"\n📊 Scraping completed!")
        print(f"Sample products: {sample_count}")
        print(f"Real deals found: {real_count}")
        print(f"Total products: {len(self.products)}")
        
        # Display results
        self.display_results()
        
        # Save to CSV
        self.save_to_csv()
        
        print(f"\n🎉 MVP Scraper completed! Check 'ammo_prices.csv' for data.")

def main():
    """Main function"""
    scraper = MVPScraper()
    scraper.run()

if __name__ == "__main__":
    main() 