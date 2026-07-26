#!/usr/bin/env python3
"""
AliExpress Telegram Bot Runner
"""

import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import main

if __name__ == '__main__':
    try:
        print("🚀 Starting AliExpress Telegram Bot...")
        print("Press Ctrl+C to stop the bot")
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)
