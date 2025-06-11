#!/usr/bin/env python3
"""
BulkAmmo Category Page Scraper
Scans category pages to extract product info and URLs from listings
Much more efficient than visiting individual pages
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
        print(f"❌ Error accessing {url}: {e}")
        return None

def extract_products_from_category(html, base_url="https://www.bulkammo.com"):
    """Extract all products from a category page"""
    if not html:
        return []
    
    products = []
    
    # Common patterns for product listings on e-commerce sites
    product_patterns = [
        # Product containers with links
        r'<div[^>]*product[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</div>',
        r'<article[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</article>',
        r'<li[^>]*product[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</li>',
        # Direct product links
        r'<a[^>]*href=["\']([^"\']*(?:ammo|rounds|bulk)[^"\']*)["\'][^>]*>([^<]+)</a>',
    ]
    
    # Also look for price and product info patterns
    # Find all links that might be products
    all_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html, re.IGNORECASE | re.DOTALL)
    
    for link, link_text in all_links:
        # Skip non-product links
        if any(skip in link.lower() for skip in ['blog', 'about', 'contact', 'policy', 'cart', 'account', 'login']):
            continue
        
        # Look for ammunition-related keywords
        if not any(keyword in (link + " " + link_text).lower() for keyword in ['ammo', 'rounds', 'bulk', 'cartridge', 'grain', 'gr']):
            continue
        
        # Make full URL
        if link.startswith('/'):
            full_url = base_url + link
        elif not link.startswith('http'):
            full_url = base_url + '/' + link
        else:
            full_url = link
        
        # Skip external links
        if 'bulkammo.com' not in full_url:
            continue
        
        # Extract product info from surrounding HTML
        product_info = extract_product_from_link_context(html, link, link_text)
        if product_info:
            product_info['url'] = full_url
            products.append(product_info)
    
    return products

def extract_product_from_link_context(html, link, link_text):
    """Extract product info from the context around a product link"""
    
    # Find the section of HTML around this link
    # Get a larger context around the link (500 chars before and after)
    pattern = f'(.{{0,500}}href=["\']({re.escape(link)})["\']).{{0,500}}'
    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return None
    
    context = match.group(0)
    
    # Extract title (use link text or nearby heading)
    title = link_text.strip()
    if not title or len(title) < 5:
        # Look for h1, h2, h3, or strong tags near the link
        title_match = re.search(r'<(?:h[1-6]|strong)[^>]*>([^<]+)</(?:h[1-6]|strong)>', context, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
    
    if not title or len(title) < 5:
        return None
    
    # Extract price from context
    price_patterns = [
        r'\$([0-9,]+\.\d{2})',  # $123.45
        r'\$([0-9,]+)',         # $123
        r'price[^>]*>[\s$]*([0-9,]+\.?\d*)',
    ]
    
    price = None
    for pattern in price_patterns:
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            try:
                price_val = float(match.replace(',', ''))
                if 15 <= price_val <= 3000:  # Reasonable ammo price range
                    price = price_val
                    break
            except:
                continue
        if price:
            break
    
    if not price:
        return None
    
    # Extract caliber and quantity
    caliber = extract_caliber(title + " " + context)
    quantity = extract_quantity(title + " " + context)
    
    # Determine stock status from context
    stock_status = "IN STOCK"  # Default assumption for category page listings
    if any(indicator in context.lower() for indicator in ['out of stock', 'sold out', 'unavailable']):
        stock_status = "OUT OF STOCK"
    
    return {
        'title': title,
        'price': price,
        'caliber': caliber,
        'quantity': quantity,
        'price_per_round': round(price / max(quantity, 1), 4),
        'stock_status': stock_status,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

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
        '300 BLK': ['300 BLK', '300 BLACKOUT', '.300 AAC'],
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
    patterns = [
        r'(\d+)\s*ROUNDS?',
        r'(\d+)\s*RDS?',
        r'(\d+)\s*CT',
        r'(\d+)\s*COUNT',
        r'(\d{3,4})\s*PER',
    ]
    
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
    
    # Default estimates
    if 'CASE' in text_upper:
        return 1000
    elif 'BOX' in text_upper:
        return 50
    return 50

def scrape_category_pages():
    """Scrape multiple category pages"""
    print("🎯 Scanning BulkAmmo Category Pages for Products")
    print("="*70)
    
    # Try different category URLs
    category_urls = [
        "https://www.bulkammo.com",  # Homepage might have featured products
        "https://www.bulkammo.com/handgun-ammo",
        "https://www.bulkammo.com/rifle-ammo", 
        "https://www.bulkammo.com/bulk-ammo",
        "https://www.bulkammo.com/cheap-ammo",
        "https://www.bulkammo.com/9mm-ammo",
        "https://www.bulkammo.com/223-ammo",
        "https://www.bulkammo.com/308-ammo",
        "https://www.bulkammo.com/45-acp-ammo",
    ]
    
    all_products = []
    
    for category_url in category_urls:
        print(f"\n📄 Scanning: {category_url}")
        html = make_request(category_url)
        
        if html:
            products = extract_products_from_category(html)
            print(f"✅ Found {len(products)} products")
            all_products.extend(products)
        else:
            print("❌ Failed to load")
        
        time.sleep(2)  # Be respectful
        
        if len(all_products) >= 15:  # Stop when we have enough
            break
    
    # Remove duplicates based on URL
    unique_products = []
    seen_urls = set()
    
    for product in all_products:
        if product['url'] not in seen_urls:
            unique_products.append(product)
            seen_urls.add(product['url'])
    
    return unique_products[:10]  # Return first 10

def display_results(products):
    """Display results for verification"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*100)
    print(f"🔍 FOUND {len(products)} PRODUCTS FROM CATEGORY PAGES")
    print("="*100)
    print("👆 Click each URL to verify the product exists and prices match")
    print("="*100)
    
    for i, product in enumerate(products, 1):
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['title']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {product['stock_status']}
🔗 VERIFY: {product['url']}
{'-'*90}""")
    
    print(f"\n📋 VERIFICATION CHECKLIST:")
    print("For each URL above:")
    print("1. ✅ Click the link - does it work?")
    print("2. ✅ Does the price match?")
    print("3. ✅ Is the caliber correct?")  
    print("4. ✅ Are quantity/rounds accurate?")
    print("5. ✅ Is stock status right?")

def main():
    """Main function"""
    print("🚀 BulkAmmo Category Page Scanner")
    print("🎯 Extracting product URLs without visiting individual pages")
    
    products = scrape_category_pages()
    
    if products:
        display_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products from category pages!")
        print("📊 These URLs were extracted from category listings")
    else:
        print("\n❌ No products found. Category page structure may be different.")

if __name__ == "__main__":
    main() 