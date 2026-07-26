#!/usr/bin/env python3
"""
Test bot startup without actually running the polling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import telegram
        print("✅ python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import telegram: {e}")
        return False
    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import requests: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import BeautifulSoup: {e}")
        return False
    
    try:
        from fake_useragent import UserAgent
        print("✅ fake-useragent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import fake-useragent: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment...")
    
    load_dotenv()
    
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    app_key = os.getenv('APP_KEY')
    app_secret = os.getenv('APP_SECRET')
    
    if telegram_token:
        print(f"✅ TELEGRAM_TOKEN found (length: {len(telegram_token)})")
    else:
        print("❌ TELEGRAM_TOKEN not found")
        return False
    
    if app_key:
        print(f"✅ APP_KEY found: {app_key}")
    else:
        print("⚠️ APP_KEY not found (optional)")
    
    if app_secret:
        print(f"✅ APP_SECRET found (length: {len(app_secret)})")
    else:
        print("⚠️ APP_SECRET not found (optional)")
    
    return True

def test_bot_initialization():
    """Test bot initialization without starting polling"""
    print("\n🤖 Testing bot initialization...")
    
    try:
        from telegram_bot_enhanced import EnhancedAliExpressTelegramBot
        
        # Initialize bot (this will test token validity)
        bot = EnhancedAliExpressTelegramBot()
        print("✅ Bot initialized successfully")
        
        # Test scraper
        if bot.scraper:
            print("✅ Enhanced scraper initialized")
        else:
            print("❌ Scraper not initialized")
            return False
        
        # Test API (optional)
        if bot.api:
            print("✅ AliExpress API initialized")
        else:
            print("⚠️ AliExpress API not initialized (credentials missing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

def test_scraper_functionality():
    """Test scraper basic functionality"""
    print("\n🔍 Testing scraper functionality...")
    
    try:
        from enhanced_scraper import EnhancedAliExpressScraper
        
        scraper = EnhancedAliExpressScraper()
        
        # Test URL detection
        test_url = "https://www.aliexpress.com/item/1005007354532583.html"
        
        if scraper.is_aliexpress_url(test_url):
            print("✅ URL detection working")
        else:
            print("❌ URL detection failed")
            return False
        
        # Test product ID extraction
        product_id = scraper.extract_product_id(test_url)
        if product_id == "1005007354532583":
            print("✅ Product ID extraction working")
        else:
            print(f"❌ Product ID extraction failed: {product_id}")
            return False
        
        # Test URL normalization
        normalized = scraper.normalize_url("m.aliexpress.com/item/123.html")
        if "www.aliexpress.com" in normalized:
            print("✅ URL normalization working")
        else:
            print(f"❌ URL normalization failed: {normalized}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AliExpress Telegram Bot - Startup Tests")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment),
        ("Bot Initialization Test", test_bot_initialization),
        ("Scraper Functionality Test", test_scraper_functionality)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if not test_func():
            all_tests_passed = False
            print(f"❌ {test_name} FAILED")
        else:
            print(f"✅ {test_name} PASSED")
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! Bot is ready to run.")
        print("\nTo start the bot, run:")
        print("python3 start_bot.py")
        print("\nOr:")
        print("python3 telegram_bot_enhanced.py")
    else:
        print("❌ Some tests failed. Please fix the issues before running the bot.")
    
    return all_tests_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
