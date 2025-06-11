# Upload Guide for GitHub

## Files to Upload to Your GitHub Repository

### 1. Main Website Files
- `admin_dashboard.html` → Upload to root
- `index.html` → Upload to root (if you want this as main page)

### 2. Python Scraper Files
- `direct_retailer_scraper.py` → Upload to root
- `requirements.txt` → Upload to root
- `config.py` → Upload to root
- `utils.py` → Upload to root
- `database.py` → Upload to root

### 3. Data Files
- `direct_retailer_prices.csv` → Upload to root

### 4. Automation Files (Already created)
- `.github/workflows/scrape.yml` → Upload to `.github/workflows/` folder

### 5. Configuration Files
- `README.md` → Create/update with project description

## Upload Methods

### Method 1: Web Interface (Easiest)
1. Go to your GitHub repository
2. Click "uploading an existing file"
3. Drag and drop files
4. Write commit message: "Initial upload of CheapAmmo files"
5. Click "Commit changes"

### Method 2: GitHub Desktop (Recommended)
1. Download GitHub Desktop
2. Clone your repository
3. Copy files to local folder
4. Commit and push changes

### Method 3: Command Line (Advanced)
```bash
git clone https://github.com/yourusername/cheapammo.git
cd cheapammo
# Copy your files here
git add .
git commit -m "Initial upload of CheapAmmo files"
git push
```

## Repository Structure After Upload
```
cheapammo/
├── admin_dashboard.html      # Your dashboard
├── index.html               # Main website (optional)
├── direct_retailer_scraper.py
├── requirements.txt
├── config.py
├── utils.py
├── database.py
├── direct_retailer_prices.csv
├── .github/
│   └── workflows/
│       └── scrape.yml       # Auto-scraping
└── README.md
```

## Next Steps After Upload
1. Enable GitHub Pages
2. Test automatic scraping
3. Configure custom domain
4. Go live! 