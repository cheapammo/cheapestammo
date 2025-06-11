#!/usr/bin/env python3
"""
Analyze scraped ammunition pricing results
"""

import csv

def analyze_results():
    """Analyze the scraped ammunition data"""
    
    try:
        with open('real_ammo_prices.csv', 'r', encoding='utf-8') as f:
            data = list(csv.DictReader(f))
        
        if not data:
            print("No data found in CSV file")
            return
        
        print("🎯 AMMUNITION DEAL ANALYSIS")
        print("=" * 60)
        
        # Sort by price per round
        sorted_data = sorted(data, key=lambda x: float(x['price_per_round']))
        
        print(f"\n📊 Found {len(data)} total deals")
        
        # Count by caliber
        caliber_counts = {}
        for row in data:
            caliber = row['caliber']
            caliber_counts[caliber] = caliber_counts.get(caliber, 0) + 1
        
        print(f"\n📈 Deals by Caliber:")
        for caliber, count in sorted(caliber_counts.items()):
            print(f"  {caliber}: {count} deals")
        
        print(f"\n🏆 TOP 10 BEST DEALS (by price per round):")
        print("-" * 60)
        
        for i, row in enumerate(sorted_data[:10], 1):
            price_per_round = float(row['price_per_round'])
            retailer = row['retailer'].replace('Reddit: ', '')
            
            print(f"{i:2d}. {row['caliber']:8s} - ${price_per_round:6.4f}/round - {retailer}")
        
        print(f"\n💰 PRICE RANGES:")
        print("-" * 40)
        
        # Group by caliber and show price ranges
        caliber_prices = {}
        for row in data:
            caliber = row['caliber']
            price = float(row['price_per_round'])
            
            if caliber not in caliber_prices:
                caliber_prices[caliber] = []
            caliber_prices[caliber].append(price)
        
        for caliber in sorted(caliber_prices.keys()):
            prices = caliber_prices[caliber]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            print(f"{caliber:8s}: ${min_price:6.4f} - ${max_price:6.4f} (avg: ${avg_price:6.4f})")
        
        print(f"\n🛒 RETAILERS FOUND:")
        print("-" * 40)
        
        retailers = {}
        for row in data:
            retailer = row['retailer'].replace('Reddit: ', '')
            retailers[retailer] = retailers.get(retailer, 0) + 1
        
        for retailer, count in sorted(retailers.items(), key=lambda x: x[1], reverse=True):
            print(f"{retailer}: {count} deals")
        
        print(f"\n✅ Analysis complete! Data saved in 'real_ammo_prices.csv'")
        
    except FileNotFoundError:
        print("❌ real_ammo_prices.csv not found. Run the scraper first!")
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_results() 