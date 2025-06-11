#!/usr/bin/env python3
"""
Targeted BulkAmmo Scraper - Find Fresh Products
Uses multiple discovery methods to find 10 different products
"""

import urllib.request
import re
import time
from datetime import datetime

def make_request(url):
    """Make HTTP request"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=20)
        
        # Handle potential gzip encoding
        content = response.read()
        if response.headers.get('Content-Encoding') == 'gzip':
            import gzip
            content = gzip.decompress(content)
        
        return content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Error accessing {url}: {e}")
        return None

def extract_product_info(html, url):
    """Extract product information from page"""
    if not html:
        return None
    
    # Get title
    title_patterns = [
        r'<title>([^<]+BulkAmmo\.com[^<]*)</title>',
        r'<h1[^>]*>([^<]+)</h1>',
        r'<title>([^<]+)</title>'
    ]
    
    title = None
    for pattern in title_patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'\s*-\s*BulkAmmo\.com.*', '', title)
            break
    
    if not title or len(title) < 10:
        return None
    
    # Get price
    price_patterns = [
        r'\$([0-9,]+\.?\d*)',
        r'price[^>]*>[\s$]*([0-9,]+\.?\d*)',
        r'cost[^>]*>[\s$]*([0-9,]+\.?\d*)'
    ]
    
    price = None
    for pattern in price_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            try:
                price_val = float(match.replace(',', ''))
                if 20 <= price_val <= 2000:  # Reasonable ammo price range
                    price = price_val
                    break
            except:
                continue
        if price:
            break
    
    if not price:
        return None
    
    # Extract caliber
    caliber = extract_caliber(title + " " + html[:2000])
    if caliber == "Unknown":
        return None
    
    # Extract quantity
    quantity = extract_quantity(title + " " + html[:1000])
    
    # Check stock
    stock_status = detect_stock_status(html)
    
    return {
        'title': title,
        'price': price,
        'caliber': caliber,
        'quantity': quantity,
        'price_per_round': round(price / quantity, 4) if quantity > 0 else 0,
        'stock_status': stock_status,
        'url': url,
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
        '.357': ['.357', '357 MAG', '357 MAGNUM'],
        '.38': ['.38', '38 SPECIAL', '.38 SPL'],
        '10MM': ['10MM', '10 MM'],
        '.243': ['.243', '243 WIN'],
        '7MM': ['7MM', '7MM-08', '7MM REM'],
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
        r'BULK\s*(\d+)'
    ]
    
    text_upper = text.upper()
    for pattern in patterns:
        match = re.search(pattern, text_upper)
        if match:
            try:
                qty = int(match.group(1))
                if 10 <= qty <= 5000:  # Reasonable range
                    return qty
            except:
                continue
    
    # Default estimates
    if 'CASE' in text_upper:
        return 1000
    elif 'BOX' in text_upper:
        return 50
    return 50

def detect_stock_status(html):
    """Detect stock status"""
    if not html:
        return "Unknown"
    
    html_lower = html.lower()
    
    # Out of stock indicators (check first)
    out_indicators = [
        'out of stock', 'sold out', 'unavailable', 'backorder',
        'notify when available', 'temporarily unavailable',
        'item not available', 'currently unavailable'
    ]
    
    for indicator in out_indicators:
        if indicator in html_lower:
            return "OUT OF STOCK"
    
    # In stock indicators
    in_indicators = ['add to cart', 'buy now', 'in stock', 'available', 'add to bag']
    for indicator in in_indicators:
        if indicator in html_lower:
            return "IN STOCK"
    
    return "Unknown"

def try_specific_products():
    """Try specific product URLs that are likely to exist"""
    # Common ammunition product patterns on BulkAmmo
    test_urls = [
        # 9mm variations
        "https://www.bulkammo.com/bulk-9mm-luger-ammo-115gr-fmj-by-magtech-1000-rounds",
        "https://www.bulkammo.com/bulk-9mm-luger-ammo-124gr-fmj-by-sellier-bellot-1000-rounds",
        "https://www.bulkammo.com/500-rounds-of-9mm-luger-ammo-by-fiocchi-115gr-fmj",
        
        # .223/5.56 variations
        "https://www.bulkammo.com/bulk-223-rem-ammo-55gr-fmj-by-pmc-1000-rounds",
        "https://www.bulkammo.com/1000-rounds-of-223-rem-ammo-by-wolf-55gr-fmj-steel-case",
        "https://www.bulkammo.com/500-rounds-of-556x45-ammo-by-federal-55gr-fmj-xm193",
        
        # .308 variations
        "https://www.bulkammo.com/bulk-308-win-ammo-150gr-fmj-by-pmc-500-rounds",
        "https://www.bulkammo.com/200-rounds-of-308-winchester-ammo-by-sellier-bellot-150gr-fmj",
        
        # .45 ACP
        "https://www.bulkammo.com/bulk-45-acp-ammo-230gr-fmj-by-magtech-500-rounds",
        "https://www.bulkammo.com/500-rounds-of-45-acp-ammo-by-fiocchi-230gr-fmj",
        
        # .40 S&W
        "https://www.bulkammo.com/500-rounds-of-40-sw-ammo-by-sellier-bellot-180gr-fmj",
        
        # 22LR
        "https://www.bulkammo.com/500-rounds-of-22lr-ammo-by-cci-40gr-lrn",
        "https://www.bulkammo.com/bulk-22-lr-ammo-40gr-lrn-by-remington-500-rounds",
        
        # 7.62x39
        "https://www.bulkammo.com/1000-rounds-of-762x39-ammo-by-wolf-123gr-fmj-steel-case",
        
        # 12 Gauge
        "https://www.bulkammo.com/25-rounds-of-12-gauge-shotgun-shells-by-federal-00-buck-9-pellet",
    ]
    
    products = []
    print("🎯 Testing specific product URLs...")
    
    for url in test_urls:
        if len(products) >= 10:
            break
            
        print(f"🌐 Testing: {url.split('/')[-1][:50]}...")
        html = make_request(url)
        
        if html and "404" not in html and "not found" not in html.lower():
            product = extract_product_info(html, url)
            if product:
                products.append(product)
                print(f"✅ Found: {product['caliber']} - ${product['price']}")
            else:
                print("❌ Could not extract product info")
        else:
            print("❌ Page not found")
        
        time.sleep(1.5)  # Be respectful
    
    return products

def display_verification_results(products):
    """Display results for verification"""
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n" + "="*100)
    print(f"🔍 FOUND {len(products)} FRESH BULKAMMO PRODUCTS FOR VERIFICATION")
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
    
    print(f"\n📋 VERIFICATION INSTRUCTIONS:")
    print("Click each URL above and check:")
    print("1. ✅ Price matches exactly")
    print("2. ✅ Stock status is correct") 
    print("3. ✅ Caliber is right")
    print("4. ✅ Product page loads (no 404)")
    print("5. ✅ Quantities/rounds match")

def main():
    """Main function"""
    print("🚀 Finding Fresh BulkAmmo Products for Verification")
    print("🎯 Targeting specific product URLs...")
    
    products = try_specific_products()
    
    if products:
        display_verification_results(products)
        print(f"\n✅ SUCCESS: Found {len(products)} products for manual verification!")
    else:
        print("\n❌ No products found. Site structure may have changed.")

if __name__ == "__main__":
    main() 