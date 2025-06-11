#!/usr/bin/env python3
"""
Smart BulkAmmo Scraper
Discovers actual site structure first, then extracts products from real category pages
"""

import urllib.request
import re
import time
from datetime import datetime

def make_request(url):
    """Make HTTP request"""
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

def discover_categories(homepage_html):
    """Discover actual category URLs from homepage"""
    if not homepage_html:
        return []
    
    print("🔍 Discovering category structure...")
    
    # Find all links on homepage
    all_links = re.findall(r'href=["\']([^"\']+)["\']', homepage_html, re.IGNORECASE)
    
    categories = []
    base_url = "https://www.bulkammo.com"
    
    for link in all_links:
        # Make full URL
        if link.startswith('/'):
            full_url = base_url + link
        elif link.startswith('http') and 'bulkammo.com' in link:
            full_url = link
        else:
            continue
        
        # Look for category-like URLs
        if any(word in link.lower() for word in ['category', 'shop', 'products', 'ammo', 'caliber', 'brand']):
            if full_url not in categories:
                categories.append(full_url)
    
    print(f"✅ Found {len(categories)} potential category URLs")
    return categories[:5]  # Limit to first 5

def extract_products_from_page(html, page_url):
    """Extract products from any page"""
    if not html:
        return []
    
    print("🔍 Looking for product links...")
    
    products = []
    base_url = "https://www.bulkammo.com"
    
    # Find all links that might be products
    all_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html, re.IGNORECASE | re.DOTALL)
    
    for link, link_text in all_links:
        # Clean up link text
        link_text = re.sub(r'<[^>]+>', '', link_text).strip()
        
        # Skip if link text is too short or doesn't look like ammunition
        if len(link_text) < 10:
            continue
        
        # Look for ammunition keywords in link or text
        ammo_keywords = ['ammo', 'ammunition', 'rounds', 'cartridge', 'grain', 'gr', 'fmj', 'hollow', 'bulk']
        if not any(keyword in (link + " " + link_text).lower() for keyword in ammo_keywords):
            continue
        
        # Skip obvious non-product links
        if any(skip in link.lower() for skip in ['blog', 'about', 'contact', 'policy', 'cart', 'account', 'login', 'search']):
            continue
        
        # Make full URL
        if link.startswith('/'):
            full_url = base_url + link
        elif not link.startswith('http'):
            continue
        else:
            full_url = link
        
        # Must be bulkammo.com
        if 'bulkammo.com' not in full_url:
            continue
        
        # Try to extract price from surrounding context
        price = extract_price_from_context(html, link)
        if not price:
            continue
        
        # Extract other info
        caliber = extract_caliber(link_text)
        quantity = extract_quantity(link_text)
        
        if caliber == "Unknown":
            continue
        
        product = {
            'title': link_text,
            'price': price,
            'caliber': caliber,
            'quantity': quantity,
            'price_per_round': round(price / max(quantity, 1), 4),
            'stock_status': 'IN STOCK',  # Assume in stock if listed
            'url': full_url,
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        products.append(product)
        print(f"✅ Found: {caliber} - ${price}")
        
        if len(products) >= 15:  # Limit products per page
            break
    
    return products

def extract_price_from_context(html, link):
    """Extract price from context around a link"""
    # Find the area around the link
    link_pos = html.lower().find(link.lower())
    if link_pos == -1:
        return None
    
    # Get 500 characters before and after the link
    start = max(0, link_pos - 500)
    end = min(len(html), link_pos + len(link) + 500)
    context = html[start:end]
    
    # Look for price patterns
    price_patterns = [
        r'\$([0-9,]+\.\d{2})',  # $123.45
        r'\$([0-9,]+)',         # $123
        r'price[^>]*>[\s$]*([0-9,]+\.?\d*)',
        r'([0-9,]+\.\d{2})',    # Just numbers with decimal
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            try:
                price = float(match.replace(',', ''))
                if 15 <= price <= 3000:  # Reasonable ammo price range
                    return price
            except:
                continue
    
    return None

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
        '300 BLK': ['300 BLK', '300 BLACKOUT'],
    }
    
    for standard, variations in calibers.items():
        for variation in variations:
            if variation in text:
                return standard
    return "Unknown"

def extract_quantity(text):
    """Extract quantity from text"""
    patterns = [r'(\d+)\s*ROUNDS?', r'(\d+)\s*RDS?', r'(\d+)\s*CT']
    
    text_upper = text.upper()
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            try:
                qty = int(match.group(1))
                if 10 <= qty <= 5000:
                    return qty
            except:
                continue
    
    return 50  # Default

def main():
    """Main function"""
    print("🚀 Smart BulkAmmo Discovery & Scraping")
    print("="*60)
    
    # Step 1: Get homepage
    print("1️⃣ Loading homepage...")
    homepage_html = make_request("https://www.bulkammo.com")
    
    if not homepage_html:
        print("❌ Cannot access BulkAmmo homepage")
        return
    
    print("✅ Homepage loaded successfully")
    
    # Step 2: Extract products directly from homepage
    print("\n2️⃣ Extracting products from homepage...")
    products = extract_products_from_page(homepage_html, "https://www.bulkammo.com")
    
    if len(products) < 10:
        # Step 3: Try to find category pages
        print(f"\n3️⃣ Only found {len(products)} products, looking for categories...")
        categories = discover_categories(homepage_html)
        
        for category_url in categories[:3]:  # Try first 3 categories
            print(f"\n💻 Checking: {category_url}")
            category_html = make_request(category_url)
            
            if category_html:
                new_products = extract_products_from_page(category_html, category_url)
                products.extend(new_products)
                print(f"✅ Added {len(new_products)} more products")
            
            time.sleep(2)
            
            if len(products) >= 10:
                break
    
    # Remove duplicates
    unique_products = []
    seen_urls = set()
    
    for product in products:
        if product['url'] not in seen_urls:
            unique_products.append(product)
            seen_urls.add(product['url'])
    
    # Display results
    final_products = unique_products[:10]
    
    if final_products:
        print(f"\n" + "="*100)
        print(f"🎯 DISCOVERED {len(final_products)} BULKAMMO PRODUCTS")
        print("="*100)
        print("👆 Click each URL to verify prices and availability")
        print("="*100)
        
        for i, product in enumerate(final_products, 1):
            print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['title']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {product['stock_status']}
🔗 VERIFY: {product['url']}
{'-'*90}""")
        
        print(f"\n✅ SUCCESS: Found {len(final_products)} products for verification!")
        print("📝 These were discovered from BulkAmmo's actual site structure")
    else:
        print("\n❌ No products found")
        print("🔍 The site structure may have changed significantly")

if __name__ == "__main__":
    main() 