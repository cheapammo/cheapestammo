#!/usr/bin/env python3
"""
Simple test script with minimal dependencies
"""

import sys
import os

def test_basic_python():
    """Test basic Python functionality"""
    print("✓ Python is working")
    print(f"✓ Python version: {sys.version}")
    return True

def test_basic_imports():
    """Test basic imports that should be available"""
    try:
        import json
        print("✓ json module")
        
        import urllib.request
        print("✓ urllib module")
        
        import re
        print("✓ regex module")
        
        import sqlite3
        print("✓ sqlite3 module")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_simple_web_request():
    """Test a simple web request"""
    try:
        import urllib.request
        import urllib.error
        
        # Test a simple request to a reliable site
        url = "https://httpbin.org/get"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("✓ Web request successful")
                return True
            else:
                print(f"⚠ Web request returned status: {response.status}")
                return False
                
    except Exception as e:
        print(f"✗ Web request failed: {e}")
        return False

def test_file_operations():
    """Test file operations"""
    try:
        # Test writing and reading a file
        test_file = "test_temp.txt"
        
        with open(test_file, 'w') as f:
            f.write("test data")
        
        with open(test_file, 'r') as f:
            data = f.read()
        
        os.remove(test_file)
        
        if data == "test data":
            print("✓ File operations working")
            return True
        else:
            print("✗ File operations failed")
            return False
            
    except Exception as e:
        print(f"✗ File operations failed: {e}")
        return False

def test_sqlite():
    """Test SQLite database"""
    try:
        import sqlite3
        
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO test (name) VALUES (?)", ("test_product",))
        
        # Query data
        cursor.execute("SELECT name FROM test WHERE id = 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result[0] == "test_product":
            print("✓ SQLite database working")
            return True
        else:
            print("✗ SQLite test failed")
            return False
            
    except Exception as e:
        print(f"✗ SQLite test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("=" * 50)
    print("BASIC SCRAPER FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Basic Python", test_basic_python),
        ("Basic Imports", test_basic_imports),
        ("File Operations", test_file_operations),
        ("SQLite Database", test_sqlite),
        ("Web Request", test_simple_web_request),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 Basic functionality is working!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install requests beautifulsoup4")
        print("2. Run full test: python test_scraper.py")
    else:
        print("❌ Some basic tests failed. Check your Python installation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 