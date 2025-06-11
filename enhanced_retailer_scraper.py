#!/usr/bin/env python3
"""
Enhanced Retailer Scraper with Individual Product URLs
Captures specific product page links for direct user click-through
"""

import urllib.request
import urllib.parse
import csv
import re
import time
import random
from datetime import datetime

class EnhancedRetailerScraper:
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
            print(f"🌐 Fetching: {url[:60]}...")
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', random.choice(self.user_agents))
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Accept-Language', 'en-US,en;q=0.5')
            req.add_header('Connection', 'keep-alive')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    content = response.read()
                    if response.info().get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    return content.decode('utf-8', errors='ignore')
                else:
                    print(f"⚠ HTTP {response.status}")
            return None
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
        
        patterns = [
            r'\$\s*([0-9,]+\.?[0-9]*)',
            r'Price[:\s]*\$\s*([0-9,]+\.?[0-9]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 5 <= price <= 10000:  # Reasonable range
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
        
        out_indicators = [
            'OUT OF STOCK', 'SOLD OUT', 'UNAVAILABLE', 'BACKORDER',
            'NOTIFY WHEN AVAILABLE', 'TEMPORARILY UNAVAILABLE'
        ]
        
        for indicator in out_indicators:
            if indicator in text_upper:
                return False
        
        in_indicators = [
            'IN STOCK', 'AVAILABLE', 'ADD TO CART', 'BUY NOW',
            'ORDER NOW', 'SHIPS', 'READY TO SHIP'
        ]
        
        for indicator in in_indicators:
            if indicator in text_upper:
                return True
        
        return self.extract_price(text) is not None
    
    def scrape_bulkammo_with_product_urls(self):
        """Scrape Bulk Ammo and extract individual product URLs"""
        print("🎯 Scraping Bulk Ammo with Product URLs...")
        
        category_urls = [
            'https://www.bulkammo.com/handgun',
            'https://www.bulkammo.com/rifle'
        ]
        
        found_count = 0
        
        for category_url in category_urls:
            html = self.make_request(category_url)
            if not html:
                continue
            
            print(f"📄 Parsing {category_url} for product links...")
            
            # Extract product links from category page
            # Look for links that go to individual product pages
            product_link_patterns = [
                r'<a[^>]+href="(/[^"]*(?:rounds?|ammo|ammunition)[^"]*)"[^>]*>([^<]+)</a>',
                r'<a[^>]+href="(/bulk-[^"]+)"[^>]*>([^<]+)</a>',
                r'href="(/[^"]*-ammo-[^"]*)"',
                r'href="(/[^"]*-rounds?-[^"]*)"'
            ]
            
            product_links = []
            for pattern in product_link_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        href, title = match
                    else:
                        href = match
                        title = ""
                    
                    # Build full URL
                    if href.startswith('/'):
                        full_url = 'https://www.bulkammo.com' + href
                    else:
                        full_url = href
                    
                    # Check if this looks like a product page
                    if any(word in href.lower() for word in ['rounds', 'ammo', 'ammunition', 'bulk-']):
                        product_links.append((full_url, title))
            
            # Remove duplicates
            product_links = list(set(product_links))
            print(f"🔗 Found {len(product_links)} potential product links")
            
            # Visit each product page to get details
            for product_url, title_hint in product_links[:15]:  # Limit to avoid overwhelming
                if found_count >= 20:  # Overall limit
                    break
                
                product_data = self.scrape_product_page(product_url, title_hint)
                if product_data:
                    self.products.append(product_data)
                    found_count += 1
                    print(f"✓ Product {found_count}: {product_data['caliber']} - ${product_data['price']} (${product_data['price_per_round']}/round)")
                
                # Be respectful with delays
                time.sleep(1.5)
            
            time.sleep(2)  # Delay between categories
        
        return found_count
    
    def scrape_product_page(self, product_url, title_hint=""):
        """Scrape individual product page for details"""
        try:
            html = self.make_request(product_url)
            if not html:
                return None
            
            # Extract product details from the individual page
            product_name = self.extract_product_name(html, title_hint)
            price = self.extract_price(html)
            
            if not product_name or not price:
                return None
            
            caliber = self.extract_caliber(product_name + " " + html[:2000])
            if not caliber:
                return None
            
            quantity = self.extract_quantity(product_name + " " + html[:2000])
            price_per_round = round(price / quantity, 4)
            
            return {
                'name': product_name[:100],
                'caliber': caliber,
                'price': price,
                'quantity': quantity,
                'price_per_round': price_per_round,
                'retailer': 'Bulk Ammo',
                'in_stock': self.is_in_stock(html[:3000]),
                'product_url': product_url,  # Individual product URL!
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error scraping product page {product_url}: {e}")
            return None
    
    def extract_product_name(self, html, title_hint=""):
        """Extract product name from product page"""
        # Try multiple patterns for product name
        name_patterns = [
            r'<h1[^>]*>([^<]+)</h1>',
            r'<title>([^<]+)</title>',
            r'<h2[^>]*>([^<]+)</h2>',
            r'class="[^"]*product[^"]*title[^"]*"[^>]*>([^<]+)</a>',
            r'class="[^"]*title[^"]*"[^>]*>([^<]+)</a>',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up HTML entities
                import html as html_module
                name = html_module.unescape(name)
                
                # If it looks like a product name (contains key terms)
                if any(word in name.lower() for word in ['rounds', 'ammo', 'ammunition', 'cartridge', 'mm', 'grain', 'gr']):
                    return name
        
        # Fallback to title hint if available
        if title_hint and len(title_hint) > 10:
            return title_hint.strip()
        
        return None
    
    def scrape_academy_with_product_urls(self):
        """Scrape Academy Sports with individual product URLs"""
        print("🎯 Scraping Academy Sports with Product URLs...")
        
        category_urls = [
            'https://www.academy.com/shop/browse/sports-outdoors/hunting/ammunition/handgun-ammo',
            'https://www.academy.com/shop/browse/sports-outdoors/hunting/ammunition/rifle-ammo'
        ]
        
        found_count = 0
        
        for category_url in category_urls:
            html = self.make_request(category_url)
            if not html:
                continue
            
            # Academy uses JSON data in their pages - look for product data
            # Extract product URLs from Academy's structure
            product_links = re.findall(r'href="(/shop/pdp/[^"]+)"', html, re.IGNORECASE)
            
            # Make URLs absolute
            full_urls = ['https://www.academy.com' + link for link in product_links if '/ammunition' in link or '/ammo' in link]
            full_urls = list(set(full_urls))  # Remove duplicates
            
            print(f"🔗 Found {len(full_urls)} Academy product links")
            
            for product_url in full_urls[:10]:  # Limit to avoid overwhelming
                if found_count >= 10:
                    break
                
                product_data = self.scrape_product_page(product_url)
                if product_data:
                    product_data['retailer'] = 'Academy Sports'
                    self.products.append(product_data)
                    found_count += 1
                    print(f"✓ Academy Product {found_count}: {product_data['caliber']} - ${product_data['price']}")
                
                time.sleep(2)  # Be respectful
            
            time.sleep(3)
        
        return found_count
    
    def save_to_csv(self, filename='enhanced_retailer_prices.csv'):
        """Save to CSV with individual product URLs"""
        if not self.products:
            print("No products to save")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'caliber', 'price', 'quantity', 'price_per_round', 'retailer', 'in_stock', 'product_url', 'scraped_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in self.products:
                    writer.writerow(product)
            
            print(f"✅ Saved {len(self.products)} products with individual URLs to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
    
    def display_results(self):
        """Display results with clickable URLs"""
        if not self.products:
            print("❌ No products found")
            return
        
        print("\n" + "="*100)
        print("ENHANCED RETAILER SCRAPING RESULTS - WITH PRODUCT URLS")
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
🔗 DIRECT LINK: {product['product_url']}
{'-'*80}""")
    
    def run(self):
        """Run the enhanced scraper"""
        print("🚀 Starting ENHANCED RETAILER Scraper - Individual Product URLs")
        print("="*70)
        
        total_found = 0
        
        # Scrape Bulk Ammo with product URLs
        print("\n1️⃣ Bulk Ammo with Product URLs...")
        bulkammo_count = self.scrape_bulkammo_with_product_urls()
        total_found += bulkammo_count
        
        # Scrape Academy Sports with product URLs
        print("\n2️⃣ Academy Sports with Product URLs...")
        academy_count = self.scrape_academy_with_product_urls()
        total_found += academy_count
        
        print(f"\n📊 Enhanced Scraping Summary:")
        print(f"Bulk Ammo products: {bulkammo_count}")
        print(f"Academy Sports products: {academy_count}")
        print(f"Total products with individual URLs: {total_found}")
        
        if total_found > 0:
            self.display_results()
            self.save_to_csv()
            print(f"\n🎉 Enhanced scraping completed! Found {total_found} products with direct URLs.")
            print("📄 Check 'enhanced_retailer_prices.csv' for data with individual product links.")
            print("💡 Users can now click directly from your site to purchase!")
        else:
            print("\n⚠️ No products found.")

def main():
    """Main function"""
    scraper = EnhancedRetailerScraper()
    scraper.run()

if __name__ == "__main__":
    main() 