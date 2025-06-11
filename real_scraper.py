#!/usr/bin/env python3
"""
Real Ammunition Price Scraper
Scrapes actual retailer websites for live pricing data
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

class RealAmmoScraper:
    def __init__(self):
        self.products = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def make_request(self, url):
        """Make HTTP request with proper headers"""
        try:
            print(f"🌐 Requesting: {url}")
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', random.choice(self.user_agents))
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Upgrade-Insecure-Requests', '1')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    # Handle gzip encoding
                    content = response.read()
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
        
        # Multiple price patterns
        patterns = [
            r'\$([0-9,]+\.?[0-9]*)',  # $24.99
            r'([0-9,]+\.?[0-9]*)\s*dollars?',  # 24.99 dollars
            r'Price[:\s]*\$?([0-9,]+\.?[0-9]*)',  # Price: $24.99
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                    if 0.1 <= price <= 10000:  # Reasonable price range
                        return price
                except ValueError:
                    continue
        return None
    
    def extract_caliber(self, text):
        """Extract caliber from text"""
        if not text:
            return None
        
        text = text.upper()
        
        # Comprehensive caliber patterns
        caliber_patterns = {
            '9MM': [r'9\s*MM', r'9X19', r'9\s*LUGER', r'9\s*PARA'],
            '.223': [r'\.223', r'223\s*REM', r'223\s*REMINGTON'],
            '5.56': [r'5\.56', r'5\.56X45', r'5\.56\s*NATO'],
            '.308': [r'\.308', r'308\s*WIN', r'308\s*WINCHESTER', r'7\.62X51'],
            '.45 ACP': [r'\.45\s*ACP', r'45\s*ACP', r'\.45\s*AUTO'],
            '.40 S&W': [r'\.40\s*S&W', r'40\s*S&W', r'\.40\s*SW'],
            '.380': [r'\.380', r'380\s*ACP', r'380\s*AUTO'],
            '22LR': [r'22\s*LR', r'\.22\s*LR', r'22\s*LONG\s*RIFLE'],
            '7.62x39': [r'7\.62X39', r'7\.62\s*X\s*39'],
            '300 BLK': [r'300\s*BLK', r'300\s*BLACKOUT', r'300\s*AAC'],
            '6.5 CM': [r'6\.5\s*CM', r'6\.5\s*CREEDMOOR'],
            '.30-06': [r'\.30-06', r'30-06', r'30\.06'],
        }
        
        for standard, patterns in caliber_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return standard
        
        return None
    
    def extract_quantity(self, text):
        """Extract quantity from text"""
        if not text:
            return None
        
        text_upper = text.upper()
        
        # Quantity patterns
        patterns = [
            r'(\d+)\s*ROUNDS?',
            r'(\d+)\s*CT\b',
            r'(\d+)\s*COUNT',
            r'(\d+)\s*PCS?',
            r'BOX\s*OF\s*(\d+)',
            r'(\d+)/BOX',
            r'(\d+)\s*PIECE',
            r'QTY[:\s]*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_upper)
            if match:
                try:
                    qty = int(match.group(1))
                    if 1 <= qty <= 10000:  # Reasonable quantity range
                        return qty
                except ValueError:
                    continue
        
        # Default quantities based on common patterns
        if 'CASE' in text_upper:
            return 1000
        elif 'BOX' in text_upper:
            return 50
        
        return 20  # Conservative default
    
    def is_in_stock(self, text):
        """Determine stock status"""
        if not text:
            return False
        
        text_upper = text.upper()
        
        # Out of stock indicators (check first - more specific)
        out_indicators = [
            'OUT OF STOCK', 'SOLD OUT', 'UNAVAILABLE', 'BACKORDER',
            'NOTIFY WHEN AVAILABLE', 'EMAIL WHEN AVAILABLE', 'TEMPORARILY UNAVAILABLE',
            'DISCONTINUED', 'NO LONGER AVAILABLE'
        ]
        
        for indicator in out_indicators:
            if indicator in text_upper:
                return False
        
        # In stock indicators
        in_indicators = [
            'IN STOCK', 'AVAILABLE', 'ADD TO CART', 'BUY NOW',
            'PURCHASE', 'ORDER NOW', 'SHIPS', 'READY TO SHIP',
            'IMMEDIATE SHIPPING', 'QUICK SHIP'
        ]
        
        for indicator in in_indicators:
            if indicator in text_upper:
                return True
        
        # If price is shown, likely in stock
        if self.extract_price(text):
            return True
        
        return False
    
    def scrape_gun_deals_reddit(self):
        """Scrape Reddit gun deals for real ammunition posts"""
        print("🔍 Scraping Reddit r/gundeals for ammunition...")
        
        try:
            # Reddit JSON API for gun deals
            url = "https://www.reddit.com/r/gundeals/search.json?q=ammo+OR+ammunition&sort=new&limit=25&restrict_sr=1"
            
            html = self.make_request(url)
            if not html:
                print("❌ Failed to get Reddit data")
                return 0
            
            try:
                data = json.loads(html)
                posts = data.get('data', {}).get('children', [])
                found_count = 0
                
                for post in posts:
                    post_data = post.get('data', {})
                    title = post_data.get('title', '')
                    url = post_data.get('url', '')
                    
                    # Skip if not ammunition related
                    if not any(word in title.lower() for word in ['ammo', 'ammunition', 'rounds', 'cartridge']):
                        continue
                    
                    # Extract data from title
                    caliber = self.extract_caliber(title)
                    price = self.extract_price(title)
                    quantity = self.extract_quantity(title)
                    
                    if caliber and price:
                        if not quantity:
                            quantity = 50  # Default for Reddit deals
                        
                        # Extract retailer from URL or title
                        retailer = "Unknown Retailer"
                        if url:
                            try:
                                from urllib.parse import urlparse
                                domain = urlparse(url).netloc
                                if domain:
                                    retailer = domain.replace('www.', '').split('.')[0].title()
                            except:
                                pass
                        
                        product = {
                            'name': title[:100],  # Truncate long titles
                            'caliber': caliber,
                            'price': price,
                            'quantity': quantity,
                            'price_per_round': round(price / quantity, 4),
                            'retailer': f"Reddit: {retailer}",
                            'in_stock': True,  # Assume deals are in stock
                            'url': url,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        self.products.append(product)
                        found_count += 1
                        print(f"✓ Reddit Deal: {caliber} - ${price} (${product['price_per_round']}/round) from {retailer}")
                
                return found_count
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse Reddit JSON: {e}")
                return 0
                
        except Exception as e:
            print(f"❌ Reddit scraping failed: {e}")
            return 0
    
    def scrape_ammoseek_search(self, caliber="9mm"):
        """Try to scrape AmmoSeek search results (educational purposes)"""
        print(f"🎯 Attempting to scrape AmmoSeek for {caliber}...")
        
        try:
            # AmmoSeek search URL
            search_term = urllib.parse.quote(caliber)
            url = f"https://ammoseek.com/ammo/{search_term}"
            
            html = self.make_request(url)
            if not html:
                print("❌ Failed to get AmmoSeek data")
                return 0
            
            # Look for product data in HTML
            # This is a simplified approach - real scraping would need more sophisticated parsing
            lines = html.split('\n')
            found_count = 0
            
            for i, line in enumerate(lines):
                # Look for price patterns in the HTML
                if '$' in line and any(cal in line.upper() for cal in ['9MM', '.223', '.308', '5.56']):
                    # Try to extract product info from surrounding lines
                    context = ' '.join(lines[max(0, i-2):i+3])
                    
                    price = self.extract_price(context)
                    found_caliber = self.extract_caliber(context)
                    quantity = self.extract_quantity(context)
                    
                    if price and found_caliber:
                        if not quantity:
                            quantity = 50
                        
                        # Extract retailer name if possible
                        retailer_match = re.search(r'([A-Za-z\s]+(?:Ammo|Gun|Sport|Outdoor|Supply))', context)
                        retailer = retailer_match.group(1).strip() if retailer_match else "AmmoSeek Retailer"
                        
                        product = {
                            'name': f"{found_caliber} Ammunition",
                            'caliber': found_caliber,
                            'price': price,
                            'quantity': quantity,
                            'price_per_round': round(price / quantity, 4),
                            'retailer': retailer,
                            'in_stock': self.is_in_stock(context),
                            'url': url,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        self.products.append(product)
                        found_count += 1
                        print(f"✓ AmmoSeek: {found_caliber} - ${price} (${product['price_per_round']}/round)")
                        
                        if found_count >= 5:  # Limit results
                            break
            
            return found_count
            
        except Exception as e:
            print(f"❌ AmmoSeek scraping failed: {e}")
            return 0
    
    def scrape_gun_broker_completed(self):
        """Scrape GunBroker completed auctions for market pricing"""
        print("🔍 Checking GunBroker completed auctions...")
        
        try:
            # GunBroker completed auctions (public data)
            url = "https://www.gunbroker.com/All/search?Keywords=ammunition&Completed=1"
            
            html = self.make_request(url)
            if not html:
                print("❌ Failed to get GunBroker data")
                return 0
            
            # Simple pattern matching for completed auction data
            found_count = 0
            lines = html.split('\n')
            
            for line in lines:
                if 'sold' in line.lower() and '$' in line:
                    price = self.extract_price(line)
                    caliber = self.extract_caliber(line)
                    
                    if price and caliber:
                        quantity = self.extract_quantity(line) or 50
                        
                        product = {
                            'name': f"{caliber} Ammunition (Auction)",
                            'caliber': caliber,
                            'price': price,
                            'quantity': quantity,
                            'price_per_round': round(price / quantity, 4),
                            'retailer': "GunBroker (Completed)",
                            'in_stock': False,  # Completed auctions
                            'url': url,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        self.products.append(product)
                        found_count += 1
                        print(f"✓ GunBroker: {caliber} - ${price} (${product['price_per_round']}/round) [SOLD]")
                        
                        if found_count >= 3:
                            break
            
            return found_count
            
        except Exception as e:
            print(f"❌ GunBroker scraping failed: {e}")
            return 0
    
    def save_to_csv(self, filename='real_ammo_prices.csv'):
        """Save products to CSV file"""
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
        """Display results in terminal"""
        if not self.products:
            print("❌ No products found")
            return
        
        print("\n" + "="*100)
        print("REAL AMMUNITION PRICE RESULTS")
        print("="*100)
        
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
URL: {product.get('url', 'N/A')}
{'-'*80}""")
    
    def run(self):
        """Run the real scraper"""
        print("🚀 Starting REAL Ammunition Price Scraper")
        print("="*60)
        
        total_found = 0
        
        # Try multiple sources
        print("\n1️⃣ Scraping Reddit gun deals...")
        reddit_count = self.scrape_gun_deals_reddit()
        total_found += reddit_count
        
        # Add delay between requests
        time.sleep(2)
        
        print("\n2️⃣ Attempting AmmoSeek search...")
        ammoseek_count = self.scrape_ammoseek_search("9mm")
        total_found += ammoseek_count
        
        time.sleep(2)
        
        print("\n3️⃣ Checking GunBroker completed auctions...")
        gunbroker_count = self.scrape_gun_broker_completed()
        total_found += gunbroker_count
        
        print(f"\n📊 Scraping Summary:")
        print(f"Reddit deals: {reddit_count}")
        print(f"AmmoSeek results: {ammoseek_count}")
        print(f"GunBroker auctions: {gunbroker_count}")
        print(f"Total products: {total_found}")
        
        if total_found > 0:
            # Display results
            self.display_results()
            
            # Save to CSV
            self.save_to_csv()
            
            print(f"\n🎉 Real scraper completed! Found {total_found} products.")
            print("📄 Check 'real_ammo_prices.csv' for detailed data.")
        else:
            print("\n⚠️ No products found. This could be due to:")
            print("- Website blocking/rate limiting")
            print("- Changed website structure")
            print("- Network connectivity issues")
            print("- Anti-bot measures")

def main():
    """Main function"""
    scraper = RealAmmoScraper()
    scraper.run()

if __name__ == "__main__":
    main() 