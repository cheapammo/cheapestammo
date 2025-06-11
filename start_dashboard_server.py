#!/usr/bin/env python3
"""
Simple HTTP server for CheapAmmo Admin Dashboard
Serves the dashboard and CSV data locally
"""

import http.server
import socketserver
import webbrowser
import os
import time
from threading import Timer

def start_server():
    """Start the HTTP server and open the dashboard"""
    
    # Change to the correct directory
    os.chdir(r'C:\Users\tcons\Cheapammo')
    
    # Set up server
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    print("🚀 Starting CheapAmmo Admin Dashboard Server...")
    print(f"📂 Serving files from: {os.getcwd()}")
    print(f"🌐 Server will run on: http://localhost:{PORT}")
    print("="*60)
    
    # Check if CSV file exists
    if os.path.exists('direct_retailer_prices.csv'):
        print("✅ Found CSV data file")
        
        # Get file size and modification time
        file_stats = os.stat('direct_retailer_prices.csv')
        file_size = file_stats.st_size
        mod_time = time.ctime(file_stats.st_mtime)
        
        print(f"📊 CSV file: {file_size} bytes, last modified: {mod_time}")
    else:
        print("⚠️  CSV file not found - run the scraper first!")
        print("   Command: python direct_retailer_scraper.py")
    
    if os.path.exists('admin_dashboard.html'):
        print("✅ Found admin dashboard")
    else:
        print("❌ admin_dashboard.html not found!")
        return
    
    print("="*60)
    
    try:
        # Start server
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            
            def open_browser():
                """Open browser after a short delay"""
                print(f"🌐 Opening dashboard at http://localhost:{PORT}/admin_dashboard.html")
                webbrowser.open(f'http://localhost:{PORT}/admin_dashboard.html')
            
            # Open browser after 1 second delay
            Timer(1.0, open_browser).start()
            
            print(f"✅ Server started successfully on port {PORT}")
            print("\n📋 Dashboard Features:")
            print("   • Live ammunition pricing data")
            print("   • Search and filter products")
            print("   • Sort by price, caliber, retailer")
            print("   • Direct links to buy products")
            print("\n🔄 To update data:")
            print("   1. Press Ctrl+C to stop server")
            print("   2. Run: python direct_retailer_scraper.py")
            print("   3. Run this server script again")
            print("\n" + "="*60)
            print("🛑 Press Ctrl+C to stop the server")
            print("="*60)
            
            # Serve forever
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use!")
            print("Try one of these solutions:")
            print(f"   • Open http://localhost:{PORT}/admin_dashboard.html directly")
            print("   • Use a different port")
            print("   • Stop other servers running on this port")
        else:
            print(f"❌ Error starting server: {e}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("✅ Dashboard server shut down successfully")

if __name__ == "__main__":
    start_server() 