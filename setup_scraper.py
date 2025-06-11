#!/usr/bin/env python3
"""
Setup script for the ammunition scraper
"""

import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        logger.error("Python 3.7 or higher is required")
        return False
    logger.info(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    logger.info("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    env_file = ".env"
    example_file = "env_example.txt"
    
    if os.path.exists(env_file):
        logger.info("✓ .env file already exists")
        return True
    
    if os.path.exists(example_file):
        try:
            with open(example_file, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            logger.info("✓ Created .env file from example")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create .env file: {e}")
            return False
    else:
        logger.warning("⚠ No env_example.txt found, creating basic .env file")
        try:
            with open(env_file, 'w') as f:
                f.write("DATABASE_URL=sqlite:///ammo_prices.db\n")
                f.write("LOG_LEVEL=INFO\n")
            logger.info("✓ Created basic .env file")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create .env file: {e}")
            return False

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    required_modules = [
        'requests', 'beautifulsoup4', 'sqlalchemy', 
        'fake_useragent', 'python-dotenv'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            if module == 'beautifulsoup4':
                import bs4
            elif module == 'python-dotenv':
                import dotenv
            elif module == 'fake_useragent':
                import fake_useragent
            else:
                __import__(module)
            logger.info(f"✓ {module}")
        except ImportError:
            logger.error(f"✗ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"Failed to import: {', '.join(failed_imports)}")
        return False
    
    logger.info("✓ All required modules imported successfully")
    return True

def run_basic_test():
    """Run basic functionality test"""
    logger.info("Running basic functionality test...")
    
    try:
        # Test database setup
        from database import db_manager
        db_manager.create_tables()
        logger.info("✓ Database setup successful")
        
        # Test configuration loading
        from config import RETAILERS, SCRAPING_CONFIG
        logger.info(f"✓ Configuration loaded - {len(RETAILERS)} retailers configured")
        
        # Test utils
        from utils import scraping_utils
        test_price = scraping_utils.clean_price("$24.99")
        if test_price == 24.99:
            logger.info("✓ Utils functions working")
        else:
            logger.warning("⚠ Utils functions may have issues")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("=" * 50)
    logger.info("AMMUNITION SCRAPER SETUP")
    logger.info("=" * 50)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Setup Environment", setup_environment),
        ("Test Imports", test_imports),
        ("Basic Functionality Test", run_basic_test),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n--- {step_name} ---")
        if not step_func():
            logger.error(f"Setup failed at: {step_name}")
            sys.exit(1)
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 SETUP COMPLETED SUCCESSFULLY!")
    logger.info("=" * 50)
    logger.info("\nNext steps:")
    logger.info("1. Run test: python test_scraper.py")
    logger.info("2. Test scraper: python scraper_runner.py --test sgammo")
    logger.info("3. Run full scrape: python scraper_runner.py --all")
    logger.info("\nFor help: python scraper_runner.py --help")

if __name__ == "__main__":
    main() 