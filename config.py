import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/ammo_db')

# Scraping Configuration
SCRAPING_CONFIG = {
    'delay_min': 2,  # Minimum delay between requests (seconds)
    'delay_max': 5,  # Maximum delay between requests (seconds)
    'timeout': 30,   # Request timeout (seconds)
    'retries': 3,    # Number of retries for failed requests
    'concurrent_limit': 5,  # Max concurrent requests
}

# Proxy Configuration (optional - add your proxy service details)
PROXY_CONFIG = {
    'enabled': False,  # Set to True when you have proxy service
    'proxy_list': [],  # Add your proxy URLs here
    'rotation_enabled': True,
}

# Retailer Configurations
RETAILERS = {
    'sgammo': {
        'name': 'SG Ammo',
        'base_url': 'https://www.sgammo.com',
        'search_url': 'https://www.sgammo.com/catalog/rifle-ammo',
        'enabled': True,
        'priority': 1,
    },
    'bulkammo': {
        'name': 'Bulk Ammo',
        'base_url': 'https://www.bulkammo.com',
        'search_url': 'https://www.bulkammo.com/rifle',
        'enabled': True,
        'priority': 2,
    },
    'targetsportsusa': {
        'name': 'Target Sports USA',
        'base_url': 'https://www.targetsportsusa.com',
        'search_url': 'https://www.targetsportsusa.com/ammo-c-49.aspx',
        'enabled': True,
        'priority': 3,
    },
    'brownells': {
        'name': 'Brownells',
        'base_url': 'https://www.brownells.com',
        'search_url': 'https://www.brownells.com/ammunition/',
        'enabled': False,  # Start with simpler sites first
        'priority': 4,
    }
}

# Data Processing Configuration
DATA_CONFIG = {
    'price_validation': {
        'min_price': 0.10,  # Minimum price per round
        'max_price': 10.00,  # Maximum price per round
    },
    'caliber_mapping': {
        # Standardize caliber names
        '9mm': ['9mm', '9mm Luger', '9x19', '9mm Para'],
        '.223': ['.223', '.223 Rem', '.223 Remington'],
        '5.56': ['5.56', '5.56x45', '5.56 NATO'],
        '.308': ['.308', '.308 Win', '.308 Winchester'],
        '.45 ACP': ['.45 ACP', '.45 Auto', '45 ACP'],
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'scraper.log',
}

# Email Monitoring Configuration
EMAIL_CONFIG = {
    'imap_server': os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com'),
    'imap_port': int(os.getenv('EMAIL_IMAP_PORT', '993')),
    'email_address': os.getenv('EMAIL_ADDRESS', ''),
    'email_password': os.getenv('EMAIL_PASSWORD', ''),  # Use app-specific password for Gmail
    'check_interval': 300,  # Check every 5 minutes
    'folders_to_monitor': ['INBOX'],  # Can add specific folders
    'mark_as_read': True,  # Mark processed emails as read
    'move_to_folder': 'Processed',  # Move processed emails to this folder (optional)
}

# Deal Detection Configuration
DEAL_CONFIG = {
    'keywords': [
        'sale', 'deal', 'special', 'discount', 'save', 'off', 
        'clearance', 'blowout', 'limited time', 'flash sale',
        'free shipping', 'bulk discount', 'weekend sale'
    ],
    'minimum_discount_percent': 10,  # Minimum discount to consider a deal
    'retailer_domains': {
        'sgammo.com': 'SG Ammo',
        'bulkammo.com': 'Bulk Ammo',
        'targetsportsusa.com': 'Target Sports USA',
        'brownells.com': 'Brownells',
        'palmettostatearmory.com': 'Palmetto State Armory',
        'midwayusa.com': 'MidwayUSA',
        'ammoman.com': 'AmmoMan',
        'luckygunner.com': 'Lucky Gunner',
        'cheaperthandirt.com': 'Cheaper Than Dirt',
        'velocityammosales.com': 'Velocity Ammo'
    },
    'parse_patterns': {
        'price': [
            r'\$([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.?[0-9]*)\s*(?:dollars|USD)',
        ],
        'discount': [
            r'([0-9]+)%\s*off',
            r'save\s*([0-9]+)%',
            r'([0-9]+)\s*percent\s*off',
        ],
        'quantity': [
            r'(\d+)\s*(?:rounds?|rds?)',
            r'(\d+)\s*(?:count|ct)',
            r'box\s*of\s*(\d+)',
        ]
    }
} 