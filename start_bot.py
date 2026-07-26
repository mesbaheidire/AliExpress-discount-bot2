#!/usr/bin/env python3
import sys
import os
import asyncio
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    os.makedirs('logs', exist_ok=True)
    log_filename = f"logs/bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(level=logging.INFO, format=log_format,
        handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    return logging.getLogger(__name__)

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Bot is running')
    def log_message(self, format, *args): pass

def start_ping_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), PingHandler)
    server.serve_forever()

def check_environment():
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv('TELEGRAM_TOKEN'):
        print("❌ TELEGRAM_TOKEN not found")
        return False
    return True

def main():
    logger = setup_logging()
    print("🚀 AliExpress Telegram Bot"); print("=" * 50)
    if not check_environment(): sys.exit(1)

    threading.Thread(target=start_ping_server, daemon=True).start()
    print("🌐 Ping server started")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        from telegram_bot_enhanced import EnhancedAliExpressTelegramBot
        logger.info("Starting bot...")
        print("📱 البوت جاهز!"); print("-" * 50)
        bot = EnhancedAliExpressTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        import traceback
        logger.error(f"Error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        loop.close()

if __name__ == '__main__':
    main()
