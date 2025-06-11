# CheapAmmo GitHub Deployment Guide

## Why GitHub is Perfect for Your Project

### Advantages
✅ **FREE hosting** for static sites (GitHub Pages)
✅ **FREE automation** (GitHub Actions - 2000 minutes/month)
✅ **Version control** - track all changes
✅ **Collaboration** - easy to work with developers
✅ **Professional** - used by millions of developers
✅ **Custom domain** support (cheapestammoonline.com)
✅ **SSL certificates** included
✅ **Global CDN** for fast loading

### Total Cost
- **GitHub**: FREE (or $4/month for private repos)
- **Domain**: $12/year
- **Total**: ~$12/year (vs $200+/year for other solutions!)

## Architecture

```
GitHub Repository
├── 📁 Website Files (HTML, CSS, JS)
├── 🐍 Python Scrapers
├── 📊 Data Files (CSV)
├── ⚙️ GitHub Actions (automation)
└── 📋 Documentation
```

## Setup Steps

### 1. Create GitHub Repository
```bash
# Your repository structure
cheapammo/
├── index.html              # Main website
├── admin_dashboard.html    # Your existing dashboard
├── scrapers/
│   ├── direct_retailer_scraper.py
│   └── requirements.txt
├── data/
│   └── direct_retailer_prices.csv
├── .github/
│   └── workflows/
│       └── scrape.yml      # Automation
└── README.md
```

### 2. GitHub Actions for Automatic Scraping
```yaml
# .github/workflows/scrape.yml
name: Scrape Ammo Prices
on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:        # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r scrapers/requirements.txt
    
    - name: Run scraper
      run: |
        cd scrapers
        python direct_retailer_scraper.py
    
    - name: Commit and push changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add data/direct_retailer_prices.csv
        git commit -m "Update ammo prices $(date)" || exit 0
        git push
```

### 3. GitHub Pages Setup
1. Go to repository Settings
2. Scroll to "Pages" section
3. Select "Deploy from a branch"
4. Choose "main" branch
5. Your site will be live at: `https://yourusername.github.io/cheapammo`

### 4. Custom Domain Setup
1. Add file `CNAME` with content: `cheapestammoonline.com`
2. Configure DNS at your domain registrar:
   - CNAME record: `www` → `yourusername.github.io`
   - A records for apex domain to GitHub's IPs

## Benefits of GitHub Approach

### For Development
- **Version Control**: Every change is tracked
- **Rollback**: Easy to undo changes
- **Collaboration**: Easy to add developers later
- **Issues/Projects**: Built-in project management

### For Business
- **Professional**: Serious developers use GitHub
- **Scalable**: Can handle millions of visitors
- **Reliable**: 99.9% uptime
- **Fast**: Global CDN included

### For Cost
- **FREE**: No monthly hosting fees
- **Transparent**: No surprise charges
- **Predictable**: Only domain cost

## Limitations to Consider
- Static sites only (no server-side processing)
- 2000 Action minutes/month (usually enough)
- Public repositories (or $4/month for private)
- 1GB storage limit (plenty for your data)

## Migration from Your Current Setup
1. **Upload existing files** to GitHub repository
2. **Convert dashboard** to work with GitHub Pages
3. **Set up Actions** for automatic scraping
4. **Configure domain** to point to GitHub
5. **Test everything** before going live

## Next Steps
1. Create GitHub account (if needed)
2. Create new repository: "cheapammo"
3. Upload your current files
4. Set up GitHub Actions
5. Enable GitHub Pages
6. Configure custom domain 