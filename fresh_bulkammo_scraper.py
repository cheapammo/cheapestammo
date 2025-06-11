#!/usr/bin/env python3
"""
Fresh BulkAmmo Product Scraper
Gets 10 new/different products for manual verification
"""

import urllib.request
import re
import time
import random
from datetime import datetime

def make_request(url):
    """Make HTTP request"""
    try:
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        req = urllib.request.Request(url, headers={'User-Agent': ua})
        response = urllib.request.urlopen(req, timeout=15)
        return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def detect_stock_status(html):
    """Detect stock status with improved logic"""
    if not html:
        return "Unknown"
    
    html_lower = html.lower()
    
    # Check for out of stock first
    out_indicators = ['out of stock', 'sold out', 'unavailable', 'backorder', 'notify when available']
    for indicator in out_indicators:
        if indicator in html_lower:
            return "OUT OF STOCK"
    
    # Check for in stock indicators
    in_indicators = ['add to cart', 'buy now', 'in stock', 'available']
    for indicator in in_indicators:
        if indicator in html_lower:
            return "IN STOCK"
    
    return "Unknown"

def extract_caliber(text):
    """Extract caliber from text"""
    text = text.upper()
    calibers = {
        '9MM': ['9MM', '9 MM', '9X19', '9 LUGER'],
        '.223': ['.223', '223 REM', '223 REMINGTON'],
        '5.56': ['5.56', '5.56X45', '5.56 NATO'],
        '.308': ['.308', '308 WIN', '308 WINCHESTER'],
        '.45 ACP': ['.45 ACP', '45 ACP', '.45 AUTO'],
        '.40 S&W': ['.40 S&W', '40 S&W', '.40 SW'],
        '.380': ['.380', '380 ACP', '380 AUTO'],
        '22LR': ['22LR', '.22 LR', '22 LONG RIFLE'],
        '7.62x39': ['7.62X39', '7.62 X 39'],
        '300 BLK': ['300 BLK', '300 BLACKOUT', '300 AAC'],
        '6.5 CM': ['6.5 CM', '6.5 CREEDMOOR'],
        '.30-06': ['.30-06', '30-06', '30.06'],
        '12 GAUGE': ['12 GAUGE', '12GA', '12 GA'],
        '20 GAUGE': ['20 GAUGE', '20GA', '20 GA'],
    }
    
    for standard, variations in calibers.items():
        for variation in variations:
            if variation in text:
                return standard
    return "Unknown"

def extract_quantity(text):
    """Extract quantity from text"""
    patterns = [r'(\d+)\s*ROUNDS?', r'(\d+)\s*CT', r'(\d+)\s*COUNT', r'(\d+)\s*RDS?']
    text_upper = text.upper()
    
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            try:
                return int(match.group(1))
            except:
                continue
    
    if 'CASE' in text_upper:
        return 1000
    elif 'BOX' in text_upper:
        return 50
    return 50

def scrape_fresh_products():
    """Scrape fresh products from BulkAmmo"""
    print("🎯 Scraping BulkAmmo for 10 Fresh Products")
    print("="*60)
    
    # Try both rifle and handgun categories
    categories = [
        'https://www.bulkammo.com/rifle',
        'https://www.bulkammo.com/handgun'
    ]
    
    all_products = []
    
    for category_url in categories:
        print(f"📄 Checking {category_url}...")
        html = make_request(category_url)
        if not html:
            continue
        
        # Look for product links using different patterns
        patterns = [
            r'href="(/bulk-[^"]+)"',
            r'href="(/[^"]*-rounds?-[^"]*)"',
            r'href="(/[^"]*ammo[^"]*)"'
        ]
        
        product_links = set()
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if any(word in match.lower() for word in ['ammo', 'rounds', 'bulk', 'cartridge']):
                    product_links.add('https://www.bulkammo.com' + match)
        
        print(f"🔗 Found {len(product_links)} potential links")
        
        # Visit each product page
        for product_url in list(product_links)[:20]:  # Limit per category
            if len(all_products) >= 15:  # Get extra in case some fail
                break
            
            print(f"🌐 Checking: {product_url[-50:]}...")
            product_html = make_request(product_url)
            if not product_html:
                continue
            
            # Extract product title
            title_match = re.search(r'<title>([^<]+)</title>', product_html, re.IGNORECASE)
            if not title_match:
                title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', product_html, re.IGNORECASE)
            
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Skip if not ammunition
            if not any(word in title.lower() for word in ['ammo', 'ammunition', 'rounds', 'cartridge']):
                continue
            
            # Extract price
            price_match = re.search(r'\$([0-9,]+\.?\d*)', product_html)
            price = None
            if price_match:
                try:
                    price = float(price_match.group(1).replace(',', ''))
                except:
                    continue
            
            if not price or price < 10:  # Skip obviously wrong prices
                continue
            
            # Extract other details
            caliber = extract_caliber(title + " " + product_html[:1000])
            quantity = extract_quantity(title + " " + product_html[:1000])
            stock_status = detect_stock_status(product_html)
            
            if caliber == "Unknown":
                continue
            
            product = {
                'title': title,
                'price': price,
                'caliber': caliber,
                'quantity': quantity,
                'price_per_round': round(price / quantity, 4),
                'stock_status': stock_status,
                'url': product_url,
                'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            all_products.append(product)
            print(f"✅ Found: {caliber} - ${price}")
            
            time.sleep(1)  # Be respectful
        
        time.sleep(2)  # Between categories
    
    # Return first 10 unique products
    unique_products = []
    seen_titles = set()
    
    for product in all_products:
        if len(unique_products) >= 10:
            break
        if product['title'] not in seen_titles:
            unique_products.append(product)
            seen_titles.add(product['title'])
    
    return unique_products

def display_verification_list(products):
    """Display products for manual verification"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*100)
    print("🔍 MANUAL VERIFICATION LIST - 10 FRESH BULKAMMO PRODUCTS")
    print("="*100)
    print("👆 Click each link to verify: PRICE | AVAILABILITY | CALIBER")
    print("="*100)
    
    for i, product in enumerate(products, 1):
        stock_emoji = "✅" if "IN STOCK" in product['stock_status'] else "❌" if "OUT" in product['stock_status'] else "❓"
        
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['title']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {stock_emoji} {product['stock_status']}
🔗 VERIFY HERE: {product['url']}
{'-'*90}""")
    
    print(f"\n📋 VERIFICATION CHECKLIST:")
    print("For each link above, check:")
    print("1. ✅ Does the PRICE match what we found?")
    print("2. ✅ Is the STOCK STATUS accurate?") 
    print("3. ✅ Is the CALIBER correct?")
    print("4. ✅ Does the product actually exist (no 404)?")
    
    print(f"\n🎯 Expected Results:")
    print("- Some may be out of stock (that's normal)")
    print("- Prices should match exactly")
    print("- Calibers should be correct")
    print("- All links should work")

def main():
    """Main function"""
    print("🚀 Getting 10 Fresh Products for Manual Verification")
    
    products = scrape_fresh_products()
    
    if len(products) >= 10:
        display_verification_list(products[:10])
        print(f"\n✅ SUCCESS: Found {len(products)} products for verification")
    else:
        print(f"\n⚠️ Only found {len(products)} products (need 10)")
        if products:
            display_verification_list(products)

if __name__ == "__main__":
    main() 