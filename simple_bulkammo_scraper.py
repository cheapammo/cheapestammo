#!/usr/bin/env python3
"""
Simple & Fast BulkAmmo Scraper
Avoids complex regex, targets product links efficiently
"""

import urllib.request
import re
import time
import random
from datetime import datetime

def make_request(url):
    """Make HTTP request"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_price(text):
    """Simple price extraction"""
    matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', text)
    for match in matches:
        try:
            price = float(match.replace(',', ''))
            if 15 <= price <= 3000:
                return price
        except:
            continue
    return None

def extract_caliber(text):
    """Simple caliber extraction"""
    text = text.upper()
    if '9MM' in text or '9 MM' in text:
        return '9MM'
    elif '.223' in text or '223' in text:
        return '.223'
    elif '5.56' in text:
        return '5.56'
    elif '.308' in text:
        return '.308'
    elif '.45' in text:
        return '.45 ACP'
    elif '.40' in text:
        return '.40 S&W'
    elif '22LR' in text or '.22' in text:
        return '22LR'
    return None

def extract_quantity(text):
    """Simple quantity extraction"""
    match = re.search(r'(\d+)\s*ROUNDS?', text.upper())
    if match:
        try:
            qty = int(match.group(1))
            if 10 <= qty <= 5000:
                return qty
        except:
            pass
    return 50

def scrape_simple():
    """Simple scraping approach"""
    print("🚀 Simple BulkAmmo Scraper - Fast & Efficient")
    print("="*60)
    
    category_urls = [
        'https://www.bulkammo.com/handgun',
        'https://www.bulkammo.com/rifle'
    ]
    
    all_products = []
    
    for category_url in category_urls:
        print(f"\n📄 Scanning: {category_url}")
        html = make_request(category_url)
        
        if not html:
            continue
        
        # Simple approach: Find all links first, then filter
        all_links = re.findall(r'href=["\']([^"\']+)["\']', html)
        
        print(f"🔗 Found {len(all_links)} total links")
        
        # Filter for product-like links (avoid #reviews)
        product_links = []
        for link in all_links:
            # Skip fragments and reviews
            if '#' in link:
                continue
            
            # Must look like a product URL
            if any(word in link.lower() for word in ['ammo', 'rounds', 'bulk', 'cartridge']):
                if not any(skip in link.lower() for skip in ['blog', 'cart', 'account', 'search']):
                    product_links.append(link)
        
        print(f"🎯 Filtered to {len(product_links)} product links")
        
        # For each product link, find its price and name in the HTML
        for link in product_links[:15]:  # Limit to avoid slowdown
            # Make full URL
            if link.startswith('/'):
                full_url = 'https://www.bulkammo.com' + link
            elif link.startswith('http'):
                full_url = link
            else:
                continue
            
            # Find this link in the HTML and get surrounding text
            link_pos = html.find(link)
            if link_pos == -1:
                continue
            
            # Get 200 chars before and after (much smaller than before)
            start = max(0, link_pos - 200)
            end = min(len(html), link_pos + 200)
            context = html[start:end]
            
            # Extract price from context
            price = extract_price(context)
            if not price:
                continue
            
            # Extract product name (look for text near the link)
            name_match = re.search(r'>([^<]*(?:rounds?|ammo|cartridge)[^<]*)<', context, re.IGNORECASE)
            if not name_match:
                continue
            
            name = name_match.group(1).strip()
            if len(name) < 10:
                continue
            
            # Extract caliber
            caliber = extract_caliber(name)
            if not caliber:
                continue
            
            quantity = extract_quantity(name)
            
            product = {
                'name': name[:80],
                'caliber': caliber,
                'price': price,
                'quantity': quantity,
                'price_per_round': round(price / quantity, 4),
                'url': full_url,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            all_products.append(product)
            print(f"✓ {caliber} - ${price} (${product['price_per_round']}/round)")
            
            if len(all_products) >= 12:
                break
        
        time.sleep(2)
        
        if len(all_products) >= 10:
            break
    
    # Remove duplicates
    unique_products = []
    seen_urls = set()
    
    for product in all_products:
        if product['url'] not in seen_urls:
            unique_products.append(product)
            seen_urls.add(product['url'])
    
    return unique_products[:10]

def display_results(products):
    """Display results"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*90)
    print(f"🎯 FOUND {len(products)} PRODUCTS WITH CLEAN URLS")
    print("="*90)
    
    for i, product in enumerate(products, 1):
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['name']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
🔗 URL: {product['url']}
{'-'*80}""")
    
    print(f"\n📋 VERIFICATION:")
    print("These URLs should go to main product pages (no #reviews)")

def main():
    """Main function"""
    products = scrape_simple()
    
    if products:
        display_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products quickly!")
    else:
        print("\n❌ No products found")

if __name__ == "__main__":
    main() 