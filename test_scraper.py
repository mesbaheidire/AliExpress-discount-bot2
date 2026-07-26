#!/usr/bin/env python3
"""
Test script for AliExpress scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aliexpress_scraper import AliExpressScraper
from aliexpress_api import AliExpressAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_scraper():
    """Test the AliExpress scraper"""
    print("🧪 Testing AliExpress Scraper...")
    
    # Test URL
    test_url = "https://www.aliexpress.com/item/1005007354532583.html"
    
    scraper = AliExpressScraper()
    
    print(f"📦 Testing URL: {test_url}")
    
    # Test product ID extraction
    product_id = scraper.extract_product_id(test_url)
    print(f"🆔 Product ID: {product_id}")
    
    # Test product details scraping
    print("🔄 Scraping product details...")
    product_data = scraper.get_product_details(test_url)
    
    if product_data:
        print("✅ Scraping successful!")
        print("📊 Product data:")
        for key, value in product_data.items():
            print(f"  {key}: {value}")
        
        # Test formatting
        print("\n📝 Formatted message:")
        formatted = scraper.format_product_info(product_data, test_url)
        print(formatted)
    else:
        print("❌ Scraping failed")

def test_api():
    """Test the AliExpress API"""
    print("\n🧪 Testing AliExpress API...")
    
    app_key = os.getenv('APP_KEY')
    app_secret = os.getenv('APP_SECRET')
    
    if not app_key or not app_secret:
        print("❌ API credentials not found in .env file")
        return
    
    api = AliExpressAPI(app_key, app_secret)
    
    # Test product search
    print("🔍 Testing product search...")
    search_result = api.search_products("phone case", page_size=5)
    
    if search_result:
        print("✅ API search successful!")
        print("📊 Search result structure:")
        print(f"  Keys: {list(search_result.keys())}")
    else:
        print("❌ API search failed")

if __name__ == '__main__':
    print("🚀 Starting AliExpress Bot Tests\n")
    
    try:
        test_scraper()
        test_api()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
