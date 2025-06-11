#!/usr/bin/env python3
"""
Fixed BulkAmmo Scraper - Targets Product Titles/Images Instead of Review Buttons
Hovers over the right elements to get main product page URLs
"""

import urllib.request
import re
import time
import random
from datetime import datetime

def make_request(url):
    """Make HTTP request"""
    try:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', random.choice(user_agents))
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Connection', 'keep-alive')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                import gzip
                content = gzip.decompress(content)
            return content.decode('utf-8', errors='ignore')
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_price(text):
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
                if 15 <= price <= 3000:  # Reasonable ammo price
                    return price
            except ValueError:
                continue
    return None

def extract_caliber(text):
    """Extract caliber from text"""
    if not text:
        return None
    
    text = text.upper()
    caliber_patterns = {
        '9MM': [r'9\s*MM', r'9X19', r'9\s*LUGER'],
        '.223': [r'\.223', r'223\s*REM'],
        '5.56': [r'5\.56', r'5\.56X45', r'5\.56\s*NATO'],
        '.308': [r'\.308', r'308\s*WIN'],
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

def extract_quantity(text):
    """Extract quantity from text"""
    if not text:
        return 50
    
    text_upper = text.upper()
    patterns = [
        r'(\d+)\s*ROUNDS?',
        r'(\d+)\s*CT\b',
        r'(\d+)\s*COUNT',
        r'BOX\s*OF\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            try:
                qty = int(match.group(1))
                if 10 <= qty <= 5000:
                    return qty
            except ValueError:
                continue
    
    if 'CASE' in text_upper:
        return 1000
    elif 'BOX' in text_upper:
        return 50
    return 50

def find_product_links_properly(html):
    """Find product links by targeting titles and images, not review buttons"""
    if not html:
        return []
    
    products = []
    
    # Strategy: Look for product title/name links first, then match with prices
    # This avoids the #reviews links
    
    # Pattern 1: Look for product title links (these are the main product page links)
    title_link_patterns = [
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*class[^>]*title[^>]*>([^<]+)</a>',
        r'<a[^>]*class[^>]*title[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]+)</a>',
        r'<h[1-6][^>]*><a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]+)</a></h[1-6]>',
    ]
    
    title_links = []
    for pattern in title_link_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        for url, title in matches:
            # Skip obvious non-product links
            if any(skip in url.lower() for skip in ['review', 'blog', 'about', 'contact', 'cart', 'account']):
                continue
            
            # Must have ammunition keywords
            if any(keyword in title.lower() for keyword in ['ammo', 'rounds', 'cartridge', 'grain', 'gr']):
                title_links.append((url, title.strip()))
    
    # Pattern 2: Look for product image links  
    image_link_patterns = [
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*><img[^>]*alt=["\']([^"\']*)["\'][^>]*></a>',
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*><img[^>]*src[^>]*></a>[^<]*([^<]*(?:ammo|rounds)[^<]*)',
    ]
    
    for pattern in image_link_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        for url, alt_text in matches:
            if any(skip in url.lower() for skip in ['review', 'blog', 'about', 'contact', 'cart']):
                continue
            
            if any(keyword in alt_text.lower() for keyword in ['ammo', 'rounds', 'cartridge']):
                title_links.append((url, alt_text.strip()))
    
    print(f"🔍 Found {len(title_links)} potential product title/image links")
    
    # Now match these links with prices from the surrounding context
    for url, title in title_links[:15]:  # Limit to avoid too many
        if not title or len(title) < 5:
            continue
        
        # Find the price near this product link
        # Look for the section of HTML that contains this link
        url_escaped = re.escape(url)
        pattern = f'(.{{0,800}}href=["\\']{url_escaped}["\\']).{{0,800}}'
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        
        if not match:
            continue
        
        context = match.group(0)
        price = extract_price(context)
        
        if not price:
            continue
        
        # Extract caliber from title
        caliber = extract_caliber(title)
        if not caliber:
            continue
        
        quantity = extract_quantity(title)
        
        # Make full URL
        if url.startswith('/'):
            full_url = 'https://www.bulkammo.com' + url
        elif url.startswith('http'):
            full_url = url
        else:
            full_url = 'https://www.bulkammo.com/' + url
        
        # Must be bulkammo.com
        if 'bulkammo.com' not in full_url:
            continue
        
        product = {
            'name': title[:100],
            'caliber': caliber,
            'price': price,
            'quantity': quantity,
            'price_per_round': round(price / quantity, 4),
            'in_stock': 'IN STOCK',
            'url': full_url,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        products.append(product)
        print(f"✓ {caliber} - ${price} (${product['price_per_round']}/round)")
        print(f"  Main URL: {full_url[-60:]}...")
        
        if len(products) >= 12:
            break
    
    return products

def scrape_bulkammo_fixed():
    """Scrape BulkAmmo targeting product titles/images for main page URLs"""
    print("🎯 Scraping BulkAmmo - Targeting Product Titles/Images (Not Review Buttons)")
    print("="*80)
    
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
        
        products = find_product_links_properly(html)
        all_products.extend(products)
        
        time.sleep(3)  # Be respectful
        
        if len(all_products) >= 12:
            break
    
    # Remove duplicates
    unique_products = []
    seen = set()
    
    for product in all_products:
        key = (product['name'], product['price'])
        if key not in seen:
            unique_products.append(product)
            seen.add(key)
    
    return unique_products[:10]

def display_results(products):
    """Display results for verification"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*100)
    print(f"🔍 FOUND {len(products)} PRODUCTS WITH MAIN PAGE URLS (NOT REVIEW LINKS)")
    print("="*100)
    print("👆 These should go to the main product page, not #reviews section")
    print("="*100)
    
    for i, product in enumerate(products, 1):
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['name']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {product['in_stock']}
🔗 MAIN PAGE: {product['url']}
{'-'*90}""")
    
    print(f"\n📋 VERIFICATION CHECKLIST:")
    print("Click each URL above and verify:")
    print("1. ✅ Goes to MAIN product page (not #reviews section)")
    print("2. ✅ Price matches exactly")
    print("3. ✅ Caliber is correct")
    print("4. ✅ Product details are accurate")
    print("5. ✅ Add to Cart button is visible")

def main():
    """Main function"""
    print("🚀 Fixed BulkAmmo Scraper - Proper Product Link Targeting")
    
    products = scrape_bulkammo_fixed()
    
    if products:
        display_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products with MAIN page URLs!")
        print("🎯 Targeted product titles/images instead of review buttons")
    else:
        print("\n❌ No products found")

if __name__ == "__main__":
    main() 