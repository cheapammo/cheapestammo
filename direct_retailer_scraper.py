#!/usr/bin/env python3
"""
Direct Retailer Scraper for Ammunition Prices
Scrapes actual retailer websites directly for live inventory and pricing
"""

import urllib.request
import urllib.parse
import csv
import re
import time
import random
from datetime import datetime
from html.parser import HTMLParser

class RetailerScraper:
    def __init__(self):
        self.products = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def make_request(self, url):
        """Make HTTP request to retailer website"""
        try:
            print(f"🌐 Scraping: {url}")
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', random.choice(self.user_agents))
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Cache-Control', 'no-cache')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    content = response.read()
                    # Handle gzip encoding
                    if response.info().get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    return content.decode('utf-8', errors='ignore')
                else:
                    print(f"⚠ HTTP {response.status} for {url}")
            return None
            
        except Exception as e:
            print(f"❌ Request failed for {url}: {e}")
            return None
    
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
        
        # More comprehensive price patterns
        patterns = [
            r'\$\s*([0-9,]+\.?[0-9]*)',  # $24.99, $1,299.99
            r'Price[:\s]*\$\s*([0-9,]+\.?[0-9]*)',  # Price: $24.99
            r'([0-9,]+\.?[0-9]*)\s*USD',  # 24.99 USD
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 0.1 <= price <= 10000:  # Reasonable range
                        return price
                except ValueError:
                    continue
        return None
    
    def extract_caliber(self, text):
        """Extract caliber from product text"""
        if not text:
            return None
        
        text = text.upper()
        
        # Comprehensive caliber detection
        caliber_patterns = {
            '9MM': [r'9\s*MM', r'9X19', r'9\s*LUGER'],
            '.223': [r'\.223', r'223\s*REM'],
            '5.56': [r'5\.56', r'5\.56X45', r'5\.56\s*NATO'],
            '.308': [r'\.308', r'308\s*WIN', r'7\.62X51'],
            '.45 ACP': [r'\.45\s*ACP', r'45\s*ACP'],
            '.40 S&W': [r'\.40\s*S&W', r'40\s*S&W'],
            '.380': [r'\.380', r'380\s*ACP'],
            '22LR': [r'22\s*LR', r'\.22\s*LR'],
            '7.62x39': [r'7\.62X39'],
            '300 BLK': [r'300\s*BLK', r'300\s*BLACKOUT'],
        }
        
        for standard, patterns in caliber_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return standard
        return None
    
    def extract_quantity(self, text):
        """Extract round count from text"""
        if not text:
            return 50  # Default
        
        text_upper = text.upper()
        
        patterns = [
            r'(\d+)\s*ROUNDS?',
            r'(\d+)\s*CT\b',
            r'(\d+)\s*COUNT',
            r'BOX\s*OF\s*(\d+)',
            r'(\d+)/BOX',
            r'(\d+)\s*RD',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    qty = int(match.group(1))
                    if 1 <= qty <= 10000:
                        return qty
                except ValueError:
                    continue
        
        # Defaults based on keywords
        if 'CASE' in text_upper:
            return 1000
        elif 'BOX' in text_upper:
            return 50
        
        return 50
    
    def is_in_stock(self, text):
        """Check stock status"""
        if not text:
            return False
        
        text_upper = text.upper()
        
        # Out of stock indicators
        out_indicators = [
            'OUT OF STOCK', 'SOLD OUT', 'UNAVAILABLE', 'BACKORDER',
            'NOTIFY WHEN AVAILABLE', 'TEMPORARILY UNAVAILABLE'
        ]
        
        for indicator in out_indicators:
            if indicator in text_upper:
                return False
        
        # In stock indicators
        in_indicators = [
            'IN STOCK', 'AVAILABLE', 'ADD TO CART', 'BUY NOW',
            'ORDER NOW', 'SHIPS', 'READY TO SHIP'
        ]
        
        for indicator in in_indicators:
            if indicator in text_upper:
                return True
        
        # If we see a price, assume it's in stock
        return self.extract_price(text) is not None
    
    def scrape_academy_sports(self):
        """Scrape Academy Sports ammunition section"""
        print("🎯 Scraping Academy Sports...")
        
        # Academy Sports ammunition categories
        urls = [
            'https://www.academy.com/shop/browse/sports-outdoors/hunting/ammunition/handgun-ammo',
            'https://www.academy.com/shop/browse/sports-outdoors/hunting/ammunition/rifle-ammo'
        ]
        
        found_count = 0
        
        for url in urls:
            html = self.make_request(url)
            if not html:
                continue
            
            # Academy uses product cards - look for price and title patterns
            lines = html.split('\n')
            
            for i, line in enumerate(lines):
                # Look for product information
                if 'data-product-name' in line or 'product-title' in line:
                    # Get context around this line
                    context_start = max(0, i - 10)
                    context_end = min(len(lines), i + 10)
                    context = ' '.join(lines[context_start:context_end])
                    
                    # Extract product name from the line
                    name_match = re.search(r'data-product-name="([^"]*)"', line)
                    if not name_match:
                        name_match = re.search(r'>([^<]*(?:ammo|ammunition)[^<]*)<', context, re.IGNORECASE)
                    
                    if name_match:
                        name = name_match.group(1).strip()
                        price = self.extract_price(context)
                        caliber = self.extract_caliber(name)
                        
                        if price and caliber and len(name) > 5:
                            quantity = self.extract_quantity(name)
                            
                            product = {
                                'name': name[:100],
                                'caliber': caliber,
                                'price': price,
                                'quantity': quantity,
                                'price_per_round': round(price / quantity, 4),
                                'retailer': 'Academy Sports',
                                'in_stock': self.is_in_stock(context),
                                'url': url,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            self.products.append(product)
                            found_count += 1
                            print(f"✓ Academy: {caliber} - ${price} (${product['price_per_round']}/round)")
                            
                            if found_count >= 10:  # Limit results per category
                                break
            
            time.sleep(2)  # Be respectful
        
        return found_count
    
    def scrape_sgammo(self):
        """Scrape SG Ammo"""
        print("🎯 Scraping SG Ammo...")
        
        # SG Ammo category pages
        urls = [
            'https://www.sgammo.com/catalog/rifle-ammo',
            'https://www.sgammo.com/catalog/handgun-ammo'
        ]
        
        found_count = 0
        
        for url in urls:
            html = self.make_request(url)
            if not html:
                continue
            
            # Look for product listings
            lines = html.split('\n')
            
            for i, line in enumerate(lines):
                # SG Ammo product patterns
                if 'product-name' in line or 'item-title' in line or ('href' in line and '/product/' in line):
                    context_start = max(0, i - 5)
                    context_end = min(len(lines), i + 15)
                    context = ' '.join(lines[context_start:context_end])
                    
                    # Extract product URL for more details
                    url_match = re.search(r'href="([^"]*product[^"]*)"', context)
                    product_url = None
                    if url_match:
                        product_url = url_match.group(1)
                        if not product_url.startswith('http'):
                            product_url = 'https://www.sgammo.com' + product_url
                    
                    # Extract basic info from listing
                    price = self.extract_price(context)
                    if price:
                        # Try to get product name
                        name_patterns = [
                            r'>([^<]*(?:ammo|ammunition|cartridge)[^<]*)<',
                            r'title="([^"]*)"',
                            r'alt="([^"]*)"'
                        ]
                        
                        name = None
                        for pattern in name_patterns:
                            name_match = re.search(pattern, context, re.IGNORECASE)
                            if name_match and len(name_match.group(1)) > 10:
                                name = name_match.group(1).strip()
                                break
                        
                        if name:
                            caliber = self.extract_caliber(name)
                            if caliber:
                                quantity = self.extract_quantity(name)
                                
                                product = {
                                    'name': name[:100],
                                    'caliber': caliber,
                                    'price': price,
                                    'quantity': quantity,
                                    'price_per_round': round(price / quantity, 4),
                                    'retailer': 'SG Ammo',
                                    'in_stock': self.is_in_stock(context),
                                    'url': product_url or url,
                                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                self.products.append(product)
                                found_count += 1
                                print(f"✓ SG Ammo: {caliber} - ${price} (${product['price_per_round']}/round)")
                                
                                if found_count >= 10:
                                    break
            
            time.sleep(3)  # Be respectful
        
        return found_count
    
    def scrape_bulkammo(self):
        """Scrape Bulk Ammo"""
        print("🎯 Scraping Bulk Ammo...")
        
        urls = [
            'https://www.bulkammo.com/handgun',
            'https://www.bulkammo.com/rifle'
        ]
        
        found_count = 0
        
        for url in urls:
            html = self.make_request(url)
            if not html:
                continue
            
            # Look for Bulk Ammo product patterns
            lines = html.split('\n')
            
            for i, line in enumerate(lines):
                if 'product' in line.lower() and ('$' in line or 'price' in line.lower()):
                    context_start = max(0, i - 8)
                    context_end = min(len(lines), i + 8)
                    context = ' '.join(lines[context_start:context_end])
                    
                    price = self.extract_price(context)
                    if price and price > 5:  # Filter out obviously wrong prices
                        # Look for product name in context
                        name_match = re.search(r'>([^<]*(?:mm|caliber|grain|gr)[^<]*)<', context, re.IGNORECASE)
                        if not name_match:
                            name_match = re.search(r'title="([^"]*)"', context)
                        
                        if name_match:
                            name = name_match.group(1).strip()
                            caliber = self.extract_caliber(name)
                            
                            if caliber and len(name) > 5:
                                quantity = self.extract_quantity(name)
                                
                                # Extract individual product URL (avoid #reviews)
                                product_url = url  # Default to category
                                url_match = re.search(r'href="([^"]*)"', context)
                                if url_match:
                                    candidate_url = url_match.group(1)
                                    if '#reviews' not in candidate_url and any(word in candidate_url for word in ['ammo', 'rounds', 'bulk']):
                                        if candidate_url.startswith('/'):
                                            product_url = 'https://www.bulkammo.com' + candidate_url
                                        elif candidate_url.startswith('http'):
                                            product_url = candidate_url
                                
                                product = {
                                    'name': name[:100],
                                    'caliber': caliber,
                                    'price': price,
                                    'quantity': quantity,
                                    'price_per_round': round(price / quantity, 4),
                                    'retailer': 'Bulk Ammo',
                                    'in_stock': self.is_in_stock(context),
                                    'url': product_url,
                                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                self.products.append(product)
                                found_count += 1
                                print(f"✓ Bulk Ammo: {caliber} - ${price} (${product['price_per_round']}/round)")
                                
                                if found_count >= 8:
                                    break
            
            time.sleep(3)
        
        return found_count
    
    def save_to_csv(self, filename='direct_retailer_prices.csv'):
        """Save to CSV"""
        if not self.products:
            print("No products to save")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'caliber', 'price', 'quantity', 'price_per_round', 'retailer', 'in_stock', 'url', 'scraped_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in self.products:
                    writer.writerow(product)
            
            print(f"✅ Saved {len(self.products)} products to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
    
    def display_results(self):
        """Display results"""
        if not self.products:
            print("❌ No products found")
            return
        
        print("\n" + "="*80)
        print("DIRECT RETAILER SCRAPING RESULTS")
        print("="*80)
        
        # Sort by price per round
        sorted_products = sorted(self.products, key=lambda x: x['price_per_round'])
        
        for i, product in enumerate(sorted_products, 1):
            stock_status = "✅ IN STOCK" if product['in_stock'] else "❌ OUT OF STOCK"
            print(f"""
#{i} - {product['name']}
Caliber: {product['caliber']}
Price: ${product['price']} ({product['quantity']} rounds)
Price/Round: ${product['price_per_round']}
Retailer: {product['retailer']}
Status: {stock_status}
{'-'*60}""")
    
    def run(self):
        """Run the direct retailer scraper"""
        print("🚀 Starting DIRECT RETAILER Ammunition Scraper")
        print("="*60)
        
        total_found = 0
        
        # Scrape Academy Sports
        print("\n1️⃣ Academy Sports...")
        academy_count = self.scrape_academy_sports()
        total_found += academy_count
        
        # Scrape SG Ammo
        print("\n2️⃣ SG Ammo...")
        sgammo_count = self.scrape_sgammo()
        total_found += sgammo_count
        
        # Scrape Bulk Ammo
        print("\n3️⃣ Bulk Ammo...")
        bulkammo_count = self.scrape_bulkammo()
        total_found += bulkammo_count
        
        print(f"\n📊 Scraping Summary:")
        print(f"Academy Sports: {academy_count}")
        print(f"SG Ammo: {sgammo_count}")
        print(f"Bulk Ammo: {bulkammo_count}")
        print(f"Total products: {total_found}")
        
        if total_found > 0:
            self.display_results()
            self.save_to_csv()
            print(f"\n🎉 Direct retailer scraping completed! Found {total_found} products.")
            print("📄 Check 'direct_retailer_prices.csv' for data.")
        else:
            print("\n⚠️ No products found. Possible issues:")
            print("- Retailers may have anti-bot protection")
            print("- Website structures may have changed")
            print("- Network connectivity issues")

def main():
    """Main function"""
    scraper = RetailerScraper()
    scraper.run()

if __name__ == "__main__":
    main() 