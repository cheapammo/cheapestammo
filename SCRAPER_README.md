# Ammunition Price Scraper

A comprehensive web scraping system for aggregating ammunition prices from multiple online retailers.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
Copy `env_example.txt` to `.env` and configure your settings:
```bash
cp env_example.txt .env
```

### 3. Initialize Database
```bash
python scraper_runner.py --setup-db
```

### 4. Test the Scraper
```bash
python test_scraper.py
```

### 5. Run a Test Scrape
```bash
python scraper_runner.py --test sgammo
```

## 📁 Project Structure

```
├── config.py              # Configuration settings
├── database.py             # Database models and management
├── utils.py               # Utility functions for scraping
├── base_scraper.py        # Base scraper class
├── sgammo_scraper.py      # SGAmmo specific scraper
├── scraper_runner.py      # Main runner script
├── test_scraper.py        # Test suite
├── requirements.txt       # Python dependencies
└── SCRAPER_README.md      # This file
```

## 🛠 Usage

### Run All Scrapers
```bash
python scraper_runner.py --all
```

### Run Specific Scraper
```bash
python scraper_runner.py --scraper sgammo
```

### Test Scraper (Limited Pages)
```bash
python scraper_runner.py --test sgammo
```

### Setup Database Only
```bash
python scraper_runner.py --setup-db
```

## 🎯 Current Retailers

### ✅ Implemented
- **SGAmmo** - Fully implemented with product extraction

### 🚧 Planned
- **BulkAmmo** - High priority
- **TargetSportsUSA** - High priority  
- **Brownells** - Medium priority
- **MidwayUSA** - Medium priority

## 📊 Database Schema

### Tables
- **retailers** - Store retailer information
- **products** - Store product details and current prices
- **price_history** - Track price changes over time
- **scraping_logs** - Log scraping sessions and results

### Key Fields
- Product name, caliber, grain weight, bullet type
- Current price and price per round
- Stock status and quantity
- Retailer information and product URLs
- Timestamps for tracking

## ⚙️ Configuration

### Scraping Settings (`config.py`)
```python
SCRAPING_CONFIG = {
    'delay_min': 2,        # Min delay between requests
    'delay_max': 5,        # Max delay between requests  
    'timeout': 30,         # Request timeout
    'retries': 3,          # Retry attempts
    'concurrent_limit': 5, # Max concurrent requests
}
```

### Retailer Settings
```python
RETAILERS = {
    'sgammo': {
        'name': 'SG Ammo',
        'base_url': 'https://www.sgammo.com',
        'enabled': True,
        'priority': 1,
    }
}
```

## 🔧 Adding New Retailers

1. **Create Scraper Class**
   ```python
   from base_scraper import BaseScraper
   
   class NewRetailerScraper(BaseScraper):
       def get_product_urls(self):
           # Implement URL discovery
           pass
       
       def scrape_product_page(self, url):
           # Implement product page scraping
           pass
       
       def _extract_product_details(self, soup, url):
           # Implement data extraction
           pass
   ```

2. **Add to Configuration**
   ```python
   RETAILERS['newretailer'] = {
       'name': 'New Retailer',
       'base_url': 'https://newretailer.com',
       'enabled': True,
       'priority': 2,
   }
   ```

3. **Register in Runner**
   ```python
   # In scraper_runner.py
   if RETAILERS['newretailer']['enabled']:
       self.scrapers['newretailer'] = NewRetailerScraper(RETAILERS['newretailer'])
   ```

## 🛡️ Anti-Detection Features

- **Random User Agents** - Rotates browser user agents
- **Request Delays** - Random delays between requests (2-5 seconds)
- **Session Management** - Maintains sessions with cookies
- **Proxy Support** - Optional proxy rotation (configure in config.py)
- **Error Handling** - Graceful handling of failures and retries
- **Respectful Scraping** - Follows robots.txt and rate limiting

## 📈 Data Processing

### Price Validation
- Validates price ranges (min: $0.10, max: $10.00 per round)
- Calculates price per round automatically
- Handles bulk pricing and case quantities

### Caliber Standardization
- Maps variations to standard caliber names
- Handles common aliases (9mm = 9mm Luger = 9x19)
- Extracts caliber from product names and descriptions

### Stock Status Detection
- Identifies in-stock vs out-of-stock products
- Handles various retailer stock indicators
- Tracks stock changes over time

## 🔍 Monitoring & Logging

### Logging Levels
- **INFO** - General operation info
- **WARNING** - Non-critical issues
- **ERROR** - Scraping failures
- **DEBUG** - Detailed debugging info

### Scraping Logs
- Session start/end times
- Products found/updated/new
- Error messages and failure reasons
- Performance metrics

## 🚨 Legal Considerations

### Best Practices
- ✅ Respect robots.txt files
- ✅ Implement reasonable rate limiting
- ✅ Use proper User-Agent headers
- ✅ Handle errors gracefully
- ✅ Monitor for IP blocks

### Compliance
- Review each retailer's Terms of Service
- Ensure fair use of data
- Respect copyright and trademarks
- Consider reaching out for partnership opportunities

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check database URL in .env file
DATABASE_URL=sqlite:///ammo_prices.db
```

**Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

**Scraping Failures**
```bash
# Test with single retailer first
python scraper_runner.py --test sgammo

# Check logs for specific errors
tail -f scraper.log
```

**No Products Found**
- Check if retailer website structure changed
- Verify CSS selectors in scraper code
- Test with browser developer tools

## 📊 Performance Tips

### Optimization
- Use SQLite for development, PostgreSQL for production
- Implement database indexing for large datasets
- Consider caching frequently accessed data
- Monitor memory usage with large product catalogs

### Scaling
- Run scrapers on separate schedules
- Implement distributed scraping with multiple servers
- Use message queues for processing large datasets
- Consider cloud hosting for better IP rotation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement new retailer scrapers
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is for educational and research purposes. Ensure compliance with all applicable laws and website terms of service. 