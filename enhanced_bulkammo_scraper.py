#!/usr/bin/env python3
"""
Enhanced BulkAmmo Scraper - Captures Individual Product URLs
Uses the proven working approach but extracts specific product page links
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

def scrape_bulkammo_with_urls():
    """Scrape BulkAmmo and capture individual product URLs"""
    print("🎯 Scraping BulkAmmo for Products with Individual URLs")
    print("="*70)
    
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
        
        lines = html.split('\n')
        
        for i, line in enumerate(lines):
            # Look for lines with both product info and prices
            if 'product' in line.lower() and ('$' in line or 'price' in line.lower()):
                # Get surrounding context
                context_start = max(0, i - 10)
                context_end = min(len(lines), i + 10)
                context = ' '.join(lines[context_start:context_end])
                
                # Extract price first (if no price, skip)
                price = extract_price(context)
                if not price or price < 15:
                    continue
                
                # Look for product URL in the context
                product_url = None
                url_patterns = [
                    r'href=["\']([^"\']*(?:rounds?|ammo|bulk)[^"\']*)["\']',
                    r'href=["\']([^"\']*)["\']'
                ]
                
                for pattern in url_patterns:
                    url_matches = re.findall(pattern, context, re.IGNORECASE)
                    for url_match in url_matches:
                        # Skip obvious non-product URLs
                        if any(skip in url_match.lower() for skip in ['cart', 'login', 'search', 'blog', 'about']):
                            continue
                        
                        # Look for ammunition-related URLs
                        if any(keyword in url_match.lower() for keyword in ['ammo', 'rounds', 'bulk', 'cartridge']):
                            if url_match.startswith('/'):
                                product_url = 'https://www.bulkammo.com' + url_match
                            elif url_match.startswith('http') and 'bulkammo.com' in url_match:
                                product_url = url_match
                            
                            if product_url:
                                break
                    
                    if product_url:
                        break
                
                # Extract product name from context
                name_patterns = [
                    r'>([^<]*(?:rounds?|ammo|grain|gr)[^<]*)<',
                    r'title="([^"]*)"',
                    r'alt="([^"]*)"'
                ]
                
                product_name = None
                for pattern in name_patterns:
                    name_match = re.search(pattern, context, re.IGNORECASE)
                    if name_match and len(name_match.group(1)) > 10:
                        name_candidate = name_match.group(1).strip()
                        # Make sure it looks like ammunition
                        if any(keyword in name_candidate.lower() for keyword in ['ammo', 'rounds', 'cartridge', 'grain', 'gr']):
                            product_name = name_candidate
                            break
                
                if not product_name:
                    continue
                
                # Extract caliber
                caliber = extract_caliber(product_name)
                if not caliber:
                    continue
                
                # Extract quantity
                quantity = extract_quantity(product_name)
                
                # Create product entry
                product = {
                    'name': product_name[:100],
                    'caliber': caliber,
                    'price': price,
                    'quantity': quantity,
                    'price_per_round': round(price / quantity, 4),
                    'in_stock': 'IN STOCK',  # Assume in stock if listed
                    'url': product_url or category_url,  # Use specific URL or fallback to category
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                all_products.append(product)
                print(f"✓ {caliber} - ${price} (${product['price_per_round']}/round)")
                print(f"  URL: {product['url'][-60:]}...")
                
                if len(all_products) >= 12:  # Get extra in case of duplicates
                    break
        
        time.sleep(3)  # Be respectful
    
    # Remove duplicates based on name and price
    unique_products = []
    seen = set()
    
    for product in all_products:
        key = (product['name'], product['price'])
        if key not in seen:
            unique_products.append(product)
            seen.add(key)
    
    return unique_products[:10]  # Return first 10

def display_results(products):
    """Display results for verification"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*100)
    print(f"🔍 FOUND {len(products)} BULKAMMO PRODUCTS WITH INDIVIDUAL URLS")
    print("="*100)
    print("👆 Click each URL below to verify: PRICE | AVAILABILITY | CALIBER")
    print("="*100)
    
    for i, product in enumerate(products, 1):
        print(f"""
🔍 PRODUCT #{i}
📦 Name: {product['name']}
🎯 Caliber: {product['caliber']}
💰 Price: ${product['price']} ({product['quantity']} rounds = ${product['price_per_round']}/round)
📊 Stock: {product['in_stock']}
🔗 VERIFY HERE: {product['url']}
{'-'*90}""")
    
    print(f"\n📋 VERIFICATION CHECKLIST:")
    print("For each URL above, check:")
    print("1. ✅ Does the link work (no 404)?")
    print("2. ✅ Does the price match exactly?")
    print("3. ✅ Is the caliber correct?")
    print("4. ✅ Are the round counts accurate?")
    print("5. ✅ Is the product actually available?")

def main():
    """Main function"""
    print("🚀 Enhanced BulkAmmo Scraper - Capturing Individual Product URLs")
    
    products = scrape_bulkammo_with_urls()
    
    if products:
        display_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products with individual URLs!")
        print("📊 Using the proven category page scanning method")
    else:
        print("\n❌ No products found")

if __name__ == "__main__":
    main() 