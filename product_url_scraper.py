#!/usr/bin/env python3
"""
Product URL Scraper - Gets Individual Product Links
Extracts specific product page URLs for direct click-through
"""

import urllib.request
import csv
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
        print(f"❌ Error fetching {url}: {e}")
        return None

def extract_price(text):
    """Extract price from text"""
    matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', text)
    for match in matches:
        try:
            price = float(match.replace(',', ''))
            if 10 <= price <= 5000:  # Reasonable range
                return price
        except ValueError:
            continue
    return None

def extract_caliber(text):
    """Extract caliber"""
    text = text.upper()
    calibers = {
        '9MM': ['9MM', '9 MM', '9X19'],
        '.223': ['.223', '223 REM'],
        '5.56': ['5.56', '5.56X45'],
        '.308': ['.308', '308 WIN'],
        '.45 ACP': ['.45 ACP', '45 ACP'],
        '22LR': ['22LR', '.22 LR'],
    }
    
    for standard, variations in calibers.items():
        for variation in variations:
            if variation in text:
                return standard
    return None

def extract_quantity(text):
    """Extract quantity"""
    patterns = [r'(\d+)\s*ROUNDS?', r'(\d+)\s*CT', r'(\d+)\s*COUNT']
    text_upper = text.upper()
    
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
    return 50

def scrape_bulkammo_products():
    """Scrape BulkAmmo and get individual product URLs"""
    print("🎯 Scraping BulkAmmo for Individual Product URLs...")
    
    products = []
    
    # Start with handgun category
    category_url = 'https://www.bulkammo.com/handgun'
    html = make_request(category_url)
    
    if not html:
        print("❌ Failed to get category page")
        return products
    
    print("📄 Extracting product links from category page...")
    
    # Find all links that look like product pages
    # BulkAmmo uses paths like /bulk-winchester-9mm-nato-ammo-1000-rounds
    product_patterns = [
        r'href="(/bulk-[^"]+)"',
        r'href="(/[^"]*-ammo-[^"]*)"',
        r'href="(/[^"]*rounds[^"]*)"'
    ]
    
    product_links = set()
    for pattern in product_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            if any(word in match.lower() for word in ['ammo', 'rounds', 'bulk']):
                full_url = 'https://www.bulkammo.com' + match
                product_links.add(full_url)
    
    print(f"🔗 Found {len(product_links)} potential product links")
    
    # Visit each product page
    for i, product_url in enumerate(list(product_links)[:15], 1):  # Limit to 15
        print(f"🌐 Checking product {i}: {product_url}")
        
        product_html = make_request(product_url)
        if not product_html:
            continue
        
        # Extract product name from title or h1
        name_match = re.search(r'<title>([^<]+)</title>', product_html, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', product_html, re.IGNORECASE)
        
        if not name_match:
            continue
        
        name = name_match.group(1).strip()
        
        # Skip if not ammunition
        if not any(word in name.lower() for word in ['ammo', 'ammunition', 'rounds', 'cartridge']):
            continue
        
        # Extract price from product page
        price = extract_price(product_html)
        if not price:
            continue
        
        # Extract caliber
        caliber = extract_caliber(name + " " + product_html[:1000])
        if not caliber:
            continue
        
        # Extract quantity
        quantity = extract_quantity(name + " " + product_html[:1000])
        
        # Check stock status
        in_stock = 'add to cart' in product_html.lower() or 'buy now' in product_html.lower()
        
        product = {
            'name': name[:100],
            'caliber': caliber,
            'price': price,
            'quantity': quantity,
            'price_per_round': round(price / quantity, 4),
            'retailer': 'Bulk Ammo',
            'in_stock': in_stock,
            'product_url': product_url,  # INDIVIDUAL PRODUCT URL!
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        products.append(product)
        print(f"✅ Product {i}: {caliber} - ${price} (${product['price_per_round']}/round)")
        print(f"   🔗 URL: {product_url}")
        
        # Be respectful - delay between requests
        time.sleep(2)
    
    return products

def save_products_with_urls(products, filename='products_with_urls.csv'):
    """Save products with individual URLs to CSV"""
    if not products:
        print("❌ No products to save")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'caliber', 'price', 'quantity', 'price_per_round', 'retailer', 'in_stock', 'product_url', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in products:
                writer.writerow(product)
        
        print(f"✅ Saved {len(products)} products with individual URLs to {filename}")
        print("\n📋 CSV Format Preview:")
        print("Each row has: name, caliber, price, quantity, price_per_round, retailer, in_stock, **product_url**, scraped_at")
        print("\n🎯 Business Value:")
        print("- Users can click directly from your site to the product page")
        print("- Each URL goes to specific product, not category page")
        print("- Users can immediately add to cart at retailer")
        print("- Perfect for affiliate tracking and commissions")
        
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")

def display_products_with_urls(products):
    """Display products with clickable URLs"""
    if not products:
        print("❌ No products found")
        return
    
    print("\n" + "="*90)
    print("AMMUNITION PRODUCTS WITH INDIVIDUAL URLS")
    print("="*90)
    
    # Sort by price per round
    sorted_products = sorted(products, key=lambda x: x['price_per_round'])
    
    for i, product in enumerate(sorted_products, 1):
        stock_status = "✅ IN STOCK" if product['in_stock'] else "❌ OUT OF STOCK"
        print(f"""
#{i} DEAL: {product['name']}
• Caliber: {product['caliber']}
• Price: ${product['price']} ({product['quantity']} rounds)
• Price/Round: ${product['price_per_round']}
• Retailer: {product['retailer']}
• Status: {stock_status}
• 🛒 DIRECT PURCHASE LINK: {product['product_url']}
{'-'*70}""")

def main():
    """Main function"""
    print("🚀 Product URL Scraper - Individual Product Links")
    print("="*60)
    
    # Scrape products with individual URLs
    products = scrape_bulkammo_products()
    
    if products:
        print(f"\n📊 Successfully found {len(products)} products with direct URLs!")
        
        # Display results
        display_products_with_urls(products)
        
        # Save to CSV
        save_products_with_urls(products)
        
        print(f"\n🎉 SUCCESS! Your users can now click directly to purchase!")
        print("💡 Each product has its own URL for immediate add-to-cart")
        
    else:
        print("\n❌ No products found")

if __name__ == "__main__":
    main() 