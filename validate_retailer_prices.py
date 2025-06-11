#!/usr/bin/env python3
"""
Validate scraped ammunition prices by comparing them with live retailer pages.
This uses only built-in Python libraries for HTTP requests and simple regex price extraction.
"""

import csv
import random
import re
import time
import urllib.request
from datetime import datetime

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
]

PRICE_PATTERN = re.compile(r'\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)')

def extract_price(html_text):
    """Extract the first price found in the HTML text"""
    match = PRICE_PATTERN.search(html_text)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except ValueError:
            return None
    return None

def fetch_page(url):
    """Fetch page content with random user agent"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', random.choice(USER_AGENTS))
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        req.add_header('Accept-Encoding', 'gzip, deflate')
        req.add_header('Connection', 'keep-alive')
        req.add_header('Upgrade-Insecure-Requests', '1')

        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                import gzip
                content = gzip.decompress(content)
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None

def validate_prices(csv_file='real_ammo_prices.csv', sample_size=5):
    """Validate prices for a sample of products"""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            products = list(csv.DictReader(f))
    except FileNotFoundError:
        print("CSV file not found. Run the scraper first.")
        return

    if not products:
        print("CSV file is empty.")
        return

    # Random sample of products
    sample = random.sample(products, min(sample_size, len(products)))

    print(f"🕵️‍♂️ Validating {len(sample)} random products (out of {len(products)})...")

    results = []

    for idx, prod in enumerate(sample, 1):
        url = prod.get('url', '').strip()
        if not url or not url.startswith('http'):
            print(f"{idx}. Skipping product without valid URL: {prod['name'][:60]}...")
            continue

        print(f"{idx}. Fetching: {url[:80]}...")
        html = fetch_page(url)
        if not html:
            results.append({**prod, 'live_price': 'N/A', 'status': 'Fetch Failed'})
            continue

        live_price = extract_price(html)
        scraped_price = float(prod['price'])

        if live_price is None:
            status = 'Price Not Found'
        else:
            # Compare within tolerance of $0.02
            if abs(live_price - scraped_price) <= 0.02:
                status = 'Match'
            else:
                status = f"Mismatch (Live ${live_price:.2f})"

        results.append({**prod, 'live_price': live_price, 'status': status})
        print(f"   → Scraped: ${scraped_price} | Live: {live_price} | {status}")

        # polite delay to avoid hammering servers
        time.sleep(2)

    # Summary
    print("\n✅ Validation Results Summary")
    matches = sum(1 for r in results if r['status'] == 'Match')
    mismatches = sum(1 for r in results if r['status'].startswith('Mismatch'))
    not_found = sum(1 for r in results if 'Not Found' in r['status'] or 'Fetch Failed' in r['status'])

    print(f"Matches       : {matches}")
    print(f"Mismatches    : {mismatches}")
    print(f"Not Found/Err : {not_found}")

if __name__ == '__main__':
    validate_prices() 