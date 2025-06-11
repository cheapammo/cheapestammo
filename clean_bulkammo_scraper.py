#!/usr/bin/env python3
"""
Clean BulkAmmo Scraper - Original Working Method + Filter Reviews URLs
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
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Cache-Control', 'no-cache')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                content = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    import gzip
                    content = gzip.decompress(content)
                return content.decode('utf-8', errors='ignore')
        return None
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def extract_price(text):
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
                if 0.1 <= price <= 10000:
                    return price
            except ValueError:
                continue
    return None

def extract_caliber(text):
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

def extract_quantity(text):
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

def extract_product_url(context):
    """Extract product URL from context, avoiding #reviews links"""
    # Look for product URLs
    url_patterns = [
        r'href=["\']([^"\']*(?:rounds?|ammo|bulk)[^"\']*)["\']',
        r'href=["\']([^"\']*)["\']'
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            # Skip fragments like #reviews
            if '#' in match:
                continue
            
            # Skip obvious non-product URLs
            if any(skip in match.lower() for skip in ['cart', 'login', 'search', 'blog', 'about', 'contact']):
                continue
            
            # Prefer URLs with ammunition keywords
            if any(keyword in match.lower() for keyword in ['ammo', 'rounds', 'bulk', 'cartridge']):
                return match
    
    return None

def scrape_bulkammo():
    """Scrape Bulk Ammo using original working method"""
    print("🎯 BulkAmmo Scraper - Original Working Method (No #reviews)")
    print("="*70)
    
    urls = [
        'https://www.bulkammo.com/handgun',
        'https://www.bulkammo.com/rifle'
    ]
    
    products = []
    
    for url in urls:
        print(f"\n📄 Scanning: {url}")
        html = make_request(url)
        if not html:
            continue
        
        # Use the original working approach: scan line by line
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            if 'product' in line.lower() and ('$' in line or 'price' in line.lower()):
                context_start = max(0, i - 8)
                context_end = min(len(lines), i + 8)
                context = ' '.join(lines[context_start:context_end])
                
                price = extract_price(context)
                if price and price > 5:
                    # Look for product name in context
                    name_match = re.search(r'>([^<]*(?:mm|caliber|grain|gr)[^<]*)<', context, re.IGNORECASE)
                    if not name_match:
                        name_match = re.search(r'title="([^"]*)"', context)
                    
                    if name_match:
                        name = name_match.group(1).strip()
                        caliber = extract_caliber(name)
                        
                        if caliber and len(name) > 5:
                            quantity = extract_quantity(name)
                            
                            # Extract product URL (avoid #reviews)
                            product_url = extract_product_url(context)
                            if product_url:
                                if product_url.startswith('/'):
                                    product_url = 'https://www.bulkammo.com' + product_url
                                elif not product_url.startswith('http'):
                                    product_url = 'https://www.bulkammo.com/' + product_url
                            else:
                                product_url = url  # Fallback to category page
                            
                            product = {
                                'name': name[:100],
                                'caliber': caliber,
                                'price': price,
                                'quantity': quantity,
                                'price_per_round': round(price / quantity, 4),
                                'url': product_url,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            products.append(product)
                            print(f"✓ {caliber} - ${price} (${product['price_per_round']}/round)")
                            print(f"  URL: {product_url[-50:]}...")
                            
                            if len(products) >= 8:
                                break
        
        time.sleep(3)
    
    return products

def display_results(products):
    """Display results"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*90)
    print(f"🎯 FOUND {len(products)} PRODUCTS WITH CLEAN URLS")
    print("="*90)
    print("👆 These should be main product pages (no #reviews)")
    print("="*90)
    
    for i, product in enumerate(products, 1):
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['name']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
🔗 VERIFY: {product['url']}
{'-'*80}""")
    
    print(f"\n📋 VERIFICATION:")
    print("Click each URL to verify it goes to the main product page")

def main():
    """Main function"""
    products = scrape_bulkammo()
    
    if products:
        display_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products with clean URLs!")
    else:
        print("\n❌ No products found")

if __name__ == "__main__":
    main() 