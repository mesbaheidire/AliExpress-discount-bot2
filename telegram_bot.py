import os
import re
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from aliexpress_scraper import AliExpressScraper
from aliexpress_api import AliExpressAPI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AliExpressTelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.app_key = os.getenv('APP_KEY')
        self.app_secret = os.getenv('APP_SECRET')
        
        # Initialize AliExpress integrations
        self.scraper = AliExpressScraper()
        self.api = AliExpressAPI(self.app_key, self.app_secret)
        
        # Initialize Telegram application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup bot command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handler for AliExpress links
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **مرحباً بك في بوت AliExpress!**

أرسل لي رابط منتج من AliExpress وسأقوم بتحليله وإرسال معلومات مفصلة عن:

📣 سعر المنتج بدون تخفيض
💵 سعر التخفيض بالعملات
💵 سعر السوبر ديلز
💵 سعر العرض المحدود
💵 سعر التخفيض المحتمل
🛍 نسبة التخفيض بالعملات
🏪 إسم المتجر
🌟 التقييم الإيجابي للمتجر
✈️ شركة الشحن
✈️ عمولة الشحن

فقط أرسل رابط المنتج وسأقوم بالباقي! 🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 **كيفية استخدام البوت:**

1️⃣ انسخ رابط أي منتج من AliExpress
2️⃣ أرسل الرابط في رسالة
3️⃣ انتظر قليلاً حتى أحلل المنتج
4️⃣ ستحصل على معلومات مفصلة عن المنتج

**أمثلة على الروابط المدعومة:**
• https://www.aliexpress.com/item/1005007354532583.html
• https://ar.aliexpress.com/item/1005007354532583.html
• https://m.aliexpress.com/item/1005007354532583.html

**ملاحظة:** البوت يدعم جميع روابط AliExpress بأشكالها المختلفة.

إذا واجهت أي مشكلة، تأكد من أن الرابط صحيح ومن موقع AliExpress.
        """
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

    def is_aliexpress_url(self, text):
        """Check if the text contains an AliExpress URL"""
        aliexpress_patterns = [
            r'https?://(?:www\.|m\.|ar\.)?aliexpress\.com/item/\d+',
            r'https?://(?:www\.|m\.|ar\.)?aliexpress\.com/.*item.*\d+',
            r'https?://(?:www\.|m\.|ar\.)?aliexpress\.us/item/\d+',
            r'https?://(?:www\.|m\.|ar\.)?aliexpress\.ru/item/\d+'
        ]
        
        for pattern in aliexpress_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_url_from_text(self, text):
        """Extract AliExpress URL from text"""
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            if self.is_aliexpress_url(url):
                return url
        return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message_text = update.message.text
        
        # Check if message contains AliExpress URL
        if self.is_aliexpress_url(message_text):
            url = self.extract_url_from_text(message_text)
            if url:
                await self.process_aliexpress_url(update, url)
            else:
                await update.message.reply_text("❌ لم أتمكن من العثور على رابط AliExpress صحيح في رسالتك.")
        else:
            await update.message.reply_text(
                "🔗 يرجى إرسال رابط منتج من AliExpress لتحليله.\n\n"
                "استخدم /help للحصول على مزيد من المعلومات."
            )

    async def process_aliexpress_url(self, update: Update, url):
        """Process AliExpress URL and send product information"""
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 جاري تحليل المنتج، يرجى الانتظار...")
        
        try:
            # Method 1: Try web scraping first
            product_info = await asyncio.to_thread(self.scraper.get_product_details, url)
            
            if product_info:
                formatted_message = self.scraper.format_product_info(product_info, url)
                await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Method 2: Try API if scraping fails
            product_id = self.scraper.extract_product_id(url)
            if product_id:
                api_result = await asyncio.to_thread(self.api.get_product_detail, product_id)
                if api_result:
                    formatted_message = self.api.format_api_product_info(api_result)
                    if formatted_message:
                        await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                        return
            
            # If both methods fail
            await processing_msg.edit_text(
                "❌ عذراً، لم أتمكن من الحصول على معلومات هذا المنتج.\n\n"
                "الأسباب المحتملة:\n"
                "• المنتج غير متوفر\n"
                "• رابط غير صحيح\n"
                "• مشكلة مؤقتة في الخدمة\n\n"
                "يرجى المحاولة مرة أخرى أو التأكد من صحة الرابط."
            )
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await processing_msg.edit_text(
                "❌ حدث خطأ أثناء معالجة الرابط.\n"
                "يرجى المحاولة مرة أخرى لاحقاً."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Start the bot"""
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Starting AliExpress Telegram Bot...")
        
        # Start the bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    bot = AliExpressTelegramBot()
    bot.run()

if __name__ == '__main__':
    main()
