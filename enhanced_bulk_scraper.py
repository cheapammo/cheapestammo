#!/usr/bin/env python3
"""
Enhanced Bulk Ammo Scraper - Maximizes Product Collection
Scrapes all ammunition categories with maximum products per page
"""

import urllib.request
import urllib.parse
import csv
import re
import time
import random
from datetime import datetime

class EnhancedBulkAmmoScraper:
    def __init__(self):
        self.products = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # BulkAmmo category URLs with maximum products per page
        self.category_urls = {
            'handgun': 'https://www.bulkammo.com/handgun?limit=100&p={}',
            'rifle': 'https://www.bulkammo.com/rifle?limit=100&p={}', 
            'rimfire': 'https://www.bulkammo.com/rimfire?limit=100&p={}',
            'shotgun': 'https://www.bulkammo.com/shotgun?limit=100&p={}'
        }
        
        self.max_pages_per_category = 2  # Scrape up to 2 pages per category
    
    def make_request(self, url):
        """Make HTTP request with proper headers"""
        try:
            print(f"🌐 Scraping: {url}")
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', random.choice(self.user_agents))
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            req.add_header('Connection', 'keep-alive')
            req.add_header('Cache-Control', 'no-cache')
            req.add_header('Referer', 'https://www.bulkammo.com/')
            
            with urllib.request.urlopen(req, timeout=20) as response:
                if response.status == 200:
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
        
        patterns = [
            r'\$\s*([0-9,]+\.?[0-9]*)',
            r'Price[:\s]*\$\s*([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.?[0-9]*)\s*USD',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 1 <= price <= 10000:
                        return price
                except ValueError:
                    continue
        return None
    
    def extract_caliber(self, text):
        """Extract caliber from product text"""
        if not text:
            return None
        
        text = text.upper()
        
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
            '.357': [r'\.357', r'357\s*MAG'],
            '.44': [r'\.44', r'44\s*MAG'],
            '12GA': [r'12\s*GA', r'12\s*GAUGE'],
            '20GA': [r'20\s*GA', r'20\s*GAUGE'],
            '.17 HMR': [r'\.17\s*HMR'],
            '.22 WMR': [r'\.22\s*WMR', r'22\s*MAG'],
        }
        
        for standard, patterns in caliber_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return standard
        return None
    
    def extract_quantity(self, text):
        """Extract round count from text"""
        if not text:
            return 50
        
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
        
        out_indicators = [
            'OUT OF STOCK', 'SOLD OUT', 'UNAVAILABLE', 'BACKORDER',
            'NOTIFY WHEN AVAILABLE', 'TEMPORARILY UNAVAILABLE', 'DISCONTINUED'
        ]
        
        for indicator in out_indicators:
            if indicator in text_upper:
                return False
        
        in_indicators = [
            'IN STOCK', 'AVAILABLE', 'ADD TO CART', 'BUY NOW',
            'ORDER NOW', 'SHIPS', 'READY TO SHIP', 'QUICK VIEW'
        ]
        
        for indicator in in_indicators:
            if indicator in text_upper:
                return True
        
        return self.extract_price(text) is not None
    
    def extract_product_url(self, html_chunk, base_url):
        """Extract individual product URL from HTML chunk"""
        # Look for product links
        url_patterns = [
            r'href="([^"]*(?:rounds|ammo|cartridge)[^"]*)"',
            r'href="(/[^"]*\.html)"',
            r'href="(/product[^"]*)"'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, html_chunk, re.IGNORECASE)
            if match:
                url = match.group(1)
                if url.startswith('/'):
                    return 'https://www.bulkammo.com' + url
                elif url.startswith('http'):
                    return url
        
        return base_url  # Fallback to category page
    
    def scrape_category_page(self, category, page_num):
        """Scrape a single category page"""
        url = self.category_urls[category].format(page_num)
        html = self.make_request(url)
        
        if not html:
            return 0
        
        found_count = 0
        
        # Split HTML into manageable chunks around product containers
        # Look for common BulkAmmo product container patterns
        product_chunks = []
        
        # Method 1: Split by product item containers
        if 'product-item' in html:
            product_chunks = re.split(r'<[^>]*product-item[^>]*>', html)
        elif 'item product' in html:
            product_chunks = re.split(r'<[^>]*item\s+product[^>]*>', html)
        else:
            # Method 2: Split by lines and group
            lines = html.split('\n')
            current_chunk = []
            
            for line in lines:
                current_chunk.append(line)
                
                # If we hit a product-related line, process the chunk
                if any(keyword in line.lower() for keyword in ['product', 'item', 'price', '$']):
                    if len(current_chunk) > 5:  # Minimum chunk size
                        product_chunks.append(' '.join(current_chunk))
                        current_chunk = []
        
        print(f"📦 Found {len(product_chunks)} potential product chunks in {category} page {page_num}")
        
        for chunk in product_chunks:
            if len(chunk) < 50:  # Skip tiny chunks
                continue
                
            # Look for price in this chunk
            price = self.extract_price(chunk)
            if not price or price < 5:  # Skip invalid prices
                continue
            
            # Look for product name/title
            name_patterns = [
                r'title="([^"]*)"',
                r'alt="([^"]*)"',
                r'>([^<]*(?:rounds|ammo|ammunition|cartridge|grain|gr)[^<]*)<',
                r'product-name[^>]*>([^<]+)<',
                r'<h[1-6][^>]*>([^<]*(?:rounds|ammo)[^<]*)</h[1-6]>'
            ]
            
            name = None
            for pattern in name_patterns:
                match = re.search(pattern, chunk, re.IGNORECASE)
                if match:
                    candidate_name = match.group(1).strip()
                    if len(candidate_name) > 10 and any(word in candidate_name.lower() for word in ['rounds', 'ammo', 'ammunition', 'cartridge']):
                        name = candidate_name
                        break
            
            if not name:
                continue
            
            # Extract caliber
            caliber = self.extract_caliber(name)
            if not caliber:
                continue
            
            # Extract quantity
            quantity = self.extract_quantity(name)
            
            # Extract product URL
            product_url = self.extract_product_url(chunk, url)
            
            # Check stock status
            in_stock = self.is_in_stock(chunk)
            
            product = {
                'name': name[:100],
                'caliber': caliber,
                'price': price,
                'quantity': quantity,
                'price_per_round': round(price / quantity, 4),
                'retailer': 'Bulk Ammo',
                'in_stock': in_stock,
                'url': product_url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.products.append(product)
            found_count += 1
            
            stock_emoji = "✅" if in_stock else "❌"
            print(f"{stock_emoji} {category.upper()}: {caliber} - ${price} (${product['price_per_round']}/round) - {name[:50]}...")
        
        return found_count
    
    def scrape_all_categories(self):
        """Scrape all ammunition categories"""
        print("🎯 Enhanced BulkAmmo Scraper - Maximizing Product Collection")
        print("="*70)
        
        total_found = 0
        
        for category in self.category_urls.keys():
            print(f"\n📂 Scraping {category.upper()} category...")
            category_total = 0
            
            for page in range(1, self.max_pages_per_category + 1):
                print(f"   📄 Page {page}...")
                page_count = self.scrape_category_page(category, page)
                category_total += page_count
                
                if page_count == 0:
                    print(f"   ⚠️ No products found on page {page}, stopping category")
                    break
                
                # Be respectful - delay between pages
                time.sleep(random.uniform(2, 4))
            
            print(f"   ✅ {category.upper()} total: {category_total} products")
            total_found += category_total
            
            # Delay between categories
            time.sleep(random.uniform(3, 5))
        
        return total_found
    
    def save_to_csv(self, filename='direct_retailer_prices.csv'):
        """Save products to CSV"""
        if not self.products:
            print("❌ No products to save")
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
    
    def display_summary(self):
        """Display scraping summary"""
        if not self.products:
            print("❌ No products found")
            return
        
        print("\n" + "="*70)
        print("ENHANCED BULK AMMO SCRAPING RESULTS")
        print("="*70)
        
        # Statistics
        total_products = len(self.products)
        in_stock_count = sum(1 for p in self.products if p['in_stock'])
        calibers = set(p['caliber'] for p in self.products)
        avg_price_per_round = sum(p['price_per_round'] for p in self.products) / total_products
        
        print(f"📊 Total Products: {total_products}")
        print(f"✅ In Stock: {in_stock_count}")
        print(f"🎯 Calibers Found: {len(calibers)}")
        print(f"💰 Average Price/Round: ${avg_price_per_round:.4f}")
        print(f"🏷️ Calibers: {', '.join(sorted(calibers))}")
        
        # Show best deals (lowest price per round)
        print(f"\n🏆 TOP 10 BEST DEALS (Price per Round):")
        sorted_products = sorted(self.products, key=lambda x: x['price_per_round'])
        
        for i, product in enumerate(sorted_products[:10], 1):
            stock_status = "✅" if product['in_stock'] else "❌"
            print(f"{i:2d}. {product['caliber']} - ${product['price_per_round']:.4f}/rd - ${product['price']} ({product['quantity']} rds) {stock_status}")
    
    def run(self):
        """Run the enhanced scraper"""
        print("🚀 Starting Enhanced BulkAmmo Scraper")
        print("🎯 Hitting all categories: handgun, rifle, rimfire, shotgun")
        print("="*70)
        
        start_time = time.time()
        total_found = self.scrape_all_categories()
        end_time = time.time()
        
        print(f"\n⏱️ Scraping completed in {end_time - start_time:.1f} seconds")
        print(f"📦 Total products collected: {total_found}")
        
        if total_found > 0:
            self.display_summary()
            self.save_to_csv()
            print(f"\n🎉 Enhanced scraping completed successfully!")
            print(f"📄 Data saved to 'direct_retailer_prices.csv'")
            print(f"🌐 Dashboard: https://cheapammo.github.io/cheapestammo/admin_dashboard.html")
        else:
            print("\n⚠️ No products found. Possible issues:")
            print("- Website structure may have changed")
            print("- Anti-bot protection may be active")
            print("- Network connectivity issues")

def main():
    """Main function"""
    scraper = EnhancedBulkAmmoScraper()
    scraper.run()

if __name__ == "__main__":
    main() 