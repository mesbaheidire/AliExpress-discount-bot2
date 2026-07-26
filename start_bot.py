#!/usr/bin/env python3
"""
AliExpress Telegram Bot - Final Version
Start script with enhanced error handling and logging
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup enhanced logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Setup file logging
    log_filename = f"logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['TELEGRAM_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    
    return True

def main():
    """Main function with enhanced error handling"""
    logger = setup_logging()
    
    print("🚀 AliExpress Telegram Bot - Enhanced Version")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    try:
        # Import and start the bot
        from telegram_bot_enhanced import EnhancedAliExpressTelegramBot
        
        logger.info("Starting AliExpress Telegram Bot...")
        print("📱 البوت جاهز لاستقبال الروابط!")
        print("🔗 أرسل رابط منتج من AliExpress للبوت")
        print("⏹️ اضغط Ctrl+C لإيقاف البوت")
        print("-" * 50)
        
        bot = EnhancedAliExpressTelegramBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت بواسطة المستخدم")
        logger.info("Bot stopped by user")
    except ImportError as e:
        print(f"❌ خطأ في استيراد المكتبات: {e}")
        print("تأكد من تثبيت جميع المتطلبات: pip install -r requirements.txt")
        logger.error(f"Import error: {e}")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        logger.error(f"Bot startup error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        print("🔚 انتهى تشغيل البوت")
        logger.info("Bot execution finished")

if __name__ == '__main__':
    main()
