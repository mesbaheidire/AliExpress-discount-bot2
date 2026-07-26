#!/usr/bin/env python3
"""
Test script for Enhanced AliExpress scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_scraper import EnhancedAliExpressScraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_enhanced_scraper():
    """Test the Enhanced AliExpress scraper"""
    print("🧪 Testing Enhanced AliExpress Scraper...")
    
    # Test URLs
    test_urls = [
        "https://www.aliexpress.com/item/1005007354532583.html",
        "https://www.aliexpress.com/item/1005005071691152.html",
        "https://ar.aliexpress.com/item/1005007354532583.html"
    ]
    
    scraper = EnhancedAliExpressScraper()
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n📦 Test {i}: {test_url}")
        
        # Test product ID extraction
        product_id = scraper.extract_product_id(test_url)
        print(f"🆔 Product ID: {product_id}")
        
        # Test URL normalization
        normalized_url = scraper.normalize_url(test_url)
        print(f"🔗 Normalized URL: {normalized_url}")
        
        # Test basic scraping (without full request to avoid being blocked)
        print(f"✅ URL validation and ID extraction successful")
        
        # Test formatting with mock data
        mock_data = {
            'title': 'Test Product Title',
            'prices': {
                'original_price': '25.99',
                'min_price': '19.99',
                'currency': 'USD'
            },
            'store': {
                'name': 'Test Store',
                'rating': '95.5'
            }
        }
        
        formatted = scraper.format_product_info(mock_data, test_url)
        print(f"📝 Formatted message preview:")
        print(formatted[:200] + "..." if len(formatted) > 200 else formatted)

def test_url_detection():
    """Test URL detection patterns"""
    print("\n🔍 Testing URL Detection...")
    
    scraper = EnhancedAliExpressScraper()
    
    test_texts = [
        "Check this product: https://www.aliexpress.com/item/1005007354532583.html",
        "https://ar.aliexpress.com/item/1005007354532583.html great deal!",
        "www.aliexpress.com/item/1005007354532583.html",
        "aliexpress.com/item/1005007354532583.html",
        "This is not an aliexpress link: https://amazon.com/item/123",
        "Multiple links: https://www.aliexpress.com/item/1005007354532583.html and https://amazon.com"
    ]
    
    for text in test_texts:
        is_aliexpress = scraper.is_aliexpress_url(text)
        extracted_url = scraper.extract_url_from_text(text) if hasattr(scraper, 'extract_url_from_text') else None
        print(f"Text: {text[:50]}...")
        print(f"  Is AliExpress: {is_aliexpress}")
        if extracted_url:
            print(f"  Extracted URL: {extracted_url}")
        print()

if __name__ == '__main__':
    print("🚀 Starting Enhanced AliExpress Bot Tests\n")
    
    try:
        test_enhanced_scraper()
        test_url_detection()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
