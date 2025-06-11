#!/usr/bin/env python3
"""
Discover BulkAmmo's Current Site Structure
Find working product URLs by examining their homepage and navigation
"""

import urllib.request
import re
import time
from datetime import datetime

def make_request(url):
    """Make HTTP request with better error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=20)
        return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def find_all_links(html, base_url="https://www.bulkammo.com"):
    """Find all links on the page"""
    if not html:
        return []
    
    # Find all href links
    links = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    
    full_links = []
    for link in links:
        if link.startswith('/'):
            full_links.append(base_url + link)
        elif link.startswith('http'):
            full_links.append(link)
    
    return full_links

def extract_product_data(html, url):
    """Extract product data from a page"""
    if not html:
        return None
    
    # Look for product indicators
    product_indicators = ['add to cart', 'buy now', 'price', '$', 'ammo', 'rounds', 'caliber']
    if not any(indicator in html.lower() for indicator in product_indicators):
        return None
    
    # Extract title
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    if not title_match:
        return None
    
    title = title_match.group(1).strip()
    
    # Look for ammunition keywords
    ammo_keywords = ['ammo', 'ammunition', 'rounds', 'cartridge', 'grain', 'gr', 'fmj', 'hollow']
    if not any(keyword in title.lower() for keyword in ammo_keywords):
        return None
    
    # Extract price
    price_patterns = [
        r'\$([0-9,]+\.?\d*)',
        r'price[^>]*>[\s$]*([0-9,]+\.?\d*)',
    ]
    
    price = None
    for pattern in price_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            try:
                price_val = float(match.replace(',', ''))
                if 15 <= price_val <= 3000:  # Reasonable range
                    price = price_val
                    break
            except:
                continue
        if price:
            break
    
    if not price:
        return None
    
    # Extract other info
    caliber = extract_caliber_simple(title)
    quantity = extract_quantity_simple(title)
    stock = "IN STOCK" if "add to cart" in html.lower() else "UNKNOWN"
    
    return {
        'title': title,
        'price': price,
        'caliber': caliber,
        'quantity': quantity,
        'price_per_round': round(price / max(quantity, 1), 4),
        'stock_status': stock,
        'url': url
    }

def extract_caliber_simple(text):
    """Simple caliber extraction"""
    text = text.upper()
    
    # Common calibers
    calibers = ['9MM', '.223', '5.56', '.308', '.45', '.40', '.380', '22LR', '7.62', '300', '6.5', '.30-06', '12GA', '20GA']
    
    for caliber in calibers:
        if caliber in text:
            return caliber
    
    return "Unknown"

def extract_quantity_simple(text):
    """Simple quantity extraction"""
    text = text.upper()
    
    # Look for numbers followed by rounds/rds
    patterns = [r'(\d+)\s*ROUNDS?', r'(\d+)\s*RDS?', r'(\d+)\s*CT']
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except:
                continue
    
    return 50  # Default

def main():
    """Main discovery function"""
    print("🔍 Discovering BulkAmmo's Current Site Structure")
    print("="*60)
    
    # Start with homepage
    print("1. Checking homepage...")
    homepage_html = make_request("https://www.bulkammo.com")
    
    if not homepage_html:
        print("❌ Cannot access homepage")
        return
    
    print("✅ Homepage loaded successfully")
    
    # Find all links
    all_links = find_all_links(homepage_html)
    print(f"🔗 Found {len(all_links)} total links")
    
    # Filter for potential product links
    product_links = []
    for link in all_links:
        if 'bulkammo.com' in link and any(word in link.lower() for word in ['ammo', 'rounds', 'bulk', 'cartridge']):
            if not any(exclude in link.lower() for exclude in ['blog', 'about', 'contact', 'policy']):
                product_links.append(link)
    
    print(f"🎯 Found {len(product_links)} potential product links")
    
    # Test first 15 product links
    products = []
    tested = 0
    
    for link in product_links[:15]:
        tested += 1
        print(f"\n🌐 Testing {tested}/15: {link[-50:]}...")
        
        html = make_request(link)
        if html:
            product = extract_product_data(html, link)
            if product:
                products.append(product)
                print(f"✅ FOUND: {product['caliber']} - ${product['price']}")
            else:
                print("❌ Not a valid product")
        else:
            print("❌ Failed to load")
        
        time.sleep(1)
    
    print(f"\n" + "="*80)
    print(f"🎯 DISCOVERY RESULTS: Found {len(products)} working products")
    print("="*80)
    
    if products:
        for i, product in enumerate(products, 1):
            print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['title']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {product['stock_status']}
🔗 URL: {product['url']}
{'-'*70}""")
        
        print(f"\n✅ SUCCESS: Found {len(products)} working BulkAmmo products!")
        print("👆 You can now verify these by clicking the URLs above")
    else:
        print("❌ No working products found")
        print("🔍 Showing homepage structure instead...")
        
        # Show some sample links found
        print("\n📋 Sample links found on homepage:")
        for i, link in enumerate(all_links[:20], 1):
            print(f"{i}. {link}")

if __name__ == "__main__":
    main() 