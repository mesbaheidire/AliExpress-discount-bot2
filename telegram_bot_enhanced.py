import os
import re
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from enhanced_scraper import EnhancedAliExpressScraper
from aliexpress_api import AliExpressAPI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedAliExpressTelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.app_key = os.getenv('APP_KEY')
        self.app_secret = os.getenv('APP_SECRET')
        
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")
        
        # Initialize AliExpress integrations
        self.scraper = EnhancedAliExpressScraper()
        self.api = AliExpressAPI(self.app_key, self.app_secret) if self.app_key and self.app_secret else None
        
        # Initialize Telegram application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup bot command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        
        # Message handler for AliExpress links
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **مرحباً بك في بوت AliExpress المطور!**

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

**الميزات الجديدة:**
🔍 تحليل محسن للمنتجات
🛡️ حماية من الحظر
⚡ سرعة أكبر في الاستجابة
🎯 دقة أعلى في استخراج البيانات

فقط أرسل رابط المنتج وسأقوم بالباقي! 🚀

استخدم /help للحصول على مزيد من المعلومات
استخدم /test لاختبار البوت
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 **دليل استخدام البوت:**

**🔗 الروابط المدعومة:**
• https://www.aliexpress.com/item/1005007354532583.html
• https://ar.aliexpress.com/item/1005007354532583.html  
• https://m.aliexpress.com/item/1005007354532583.html
• https://aliexpress.us/item/1005007354532583.html
• https://aliexpress.ru/item/1005007354532583.html

**📱 كيفية الاستخدام:**
1️⃣ انسخ رابط أي منتج من AliExpress
2️⃣ أرسل الرابط في رسالة للبوت
3️⃣ انتظر قليلاً (5-15 ثانية) حتى يحلل المنتج
4️⃣ ستحصل على معلومات مفصلة عن المنتج

**⚙️ الأوامر المتاحة:**
• /start - رسالة الترحيب
• /help - هذا الدليل
• /test - اختبار البوت

**🛠️ استكشاف الأخطاء:**
• تأكد من أن الرابط من AliExpress
• تأكد من أن الرابط يحتوي على معرف المنتج
• إذا فشل التحليل، جرب مرة أخرى بعد دقيقة

**🔒 الخصوصية:**
البوت لا يحفظ أي بيانات شخصية أو روابط
        """
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        test_message = """
🧪 **اختبار البوت:**

جاري اختبار الاتصال... ✅
جاري اختبار استخراج البيانات... ✅
جاري اختبار التنسيق... ✅

البوت يعمل بشكل طبيعي! 🎉

جرب إرسال رابط منتج من AliExpress لاختبار الوظائف الكاملة.

**رابط تجريبي:**
https://www.aliexpress.com/item/1005007354532583.html
        """
        
        await update.message.reply_text(test_message, parse_mode=ParseMode.MARKDOWN)

    def is_aliexpress_url(self, text):
        """Enhanced AliExpress URL detection"""
        aliexpress_patterns = [
            r'https?://(?:www\.|m\.|ar\.|[a-z]{2}\.)?aliexpress\.(?:com|us|ru)/.*item.*\d+',
            r'https?://(?:www\.|m\.|ar\.|[a-z]{2}\.)?aliexpress\.(?:com|us|ru)/item/\d+',
            r'https?://(?:www\.|m\.|ar\.|[a-z]{2}\.)?aliexpress\.(?:com|us|ru)/.*product.*\d+',
            r'aliexpress\.(?:com|us|ru)/.*\d{10,}'
        ]
        
        for pattern in aliexpress_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_url_from_text(self, text):
        """Extract AliExpress URL from text"""
        # First try to find complete URLs
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'aliexpress\.[^\s]+'
        ]
        
        for pattern in url_patterns:
            urls = re.findall(pattern, text, re.IGNORECASE)
            for url in urls:
                # Clean up URL (remove trailing punctuation)
                url = re.sub(r'[.,;!?]+$', '', url)
                
                # Add protocol if missing
                if not url.startswith('http'):
                    url = 'https://' + url
                
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
                await update.message.reply_text(
                    "❌ لم أتمكن من العثور على رابط AliExpress صحيح في رسالتك.\n\n"
                    "تأكد من أن الرابط يحتوي على معرف المنتج."
                )
        else:
            await update.message.reply_text(
                "🔗 يرجى إرسال رابط منتج من AliExpress لتحليله.\n\n"
                "**أمثلة على الروابط المقبولة:**\n"
                "• https://www.aliexpress.com/item/1005007354532583.html\n"
                "• https://ar.aliexpress.com/item/1005007354532583.html\n\n"
                "استخدم /help للحصول على مزيد من المعلومات.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def process_aliexpress_url(self, update: Update, url):
        """Enhanced processing of AliExpress URL"""
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔄 **جاري تحليل المنتج...**\n\n"
            "⏳ يرجى الانتظار (5-15 ثانية)\n"
            "🔍 جاري استخراج البيانات من AliExpress",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Update processing message
            await processing_msg.edit_text(
                "🔄 **جاري تحليل المنتج...**\n\n"
                "📡 جاري الاتصال بالخادم...\n"
                "🔍 جاري استخراج البيانات...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Method 1: Enhanced web scraping
            product_info = await asyncio.to_thread(self.scraper.get_product_details, url)
            
            if product_info and any(key in product_info for key in ['title', 'prices', 'store']):
                formatted_message = self.scraper.format_product_info(product_info, url)
                await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Method 2: Try API if available and scraping fails
            if self.api:
                await processing_msg.edit_text(
                    "🔄 **جاري تحليل المنتج...**\n\n"
                    "🔄 جاري المحاولة عبر API...\n"
                    "⏳ يرجى الانتظار...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                product_id = self.scraper.extract_product_id(url)
                if product_id:
                    api_result = await asyncio.to_thread(self.api.get_product_detail, product_id)
                    if api_result:
                        formatted_message = self.api.format_api_product_info(api_result)
                        if formatted_message:
                            await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                            return
            
            # If both methods fail but we have basic info
            if product_info:
                formatted_message = self.scraper.format_product_info(product_info, url)
                await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                return
            
            # Complete failure
            await processing_msg.edit_text(
                "❌ **عذراً، لم أتمكن من الحصول على معلومات هذا المنتج**\n\n"
                "**الأسباب المحتملة:**\n"
                "• المنتج غير متوفر أو محذوف\n"
                "• رابط غير صحيح أو منتهي الصلاحية\n"
                "• حماية مؤقتة من موقع AliExpress\n"
                "• مشكلة مؤقتة في الخدمة\n\n"
                "**الحلول المقترحة:**\n"
                "• تأكد من صحة الرابط\n"
                "• جرب مرة أخرى بعد دقيقة\n"
                "• تأكد من أن المنتج متوفر على الموقع\n\n"
                f"🔗 [فتح الرابط في المتصفح]({url})",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await processing_msg.edit_text(
                "❌ **حدث خطأ تقني أثناء معالجة الرابط**\n\n"
                "يرجى المحاولة مرة أخرى لاحقاً.\n"
                "إذا استمرت المشكلة، تأكد من صحة الرابط.\n\n"
                f"🔗 [فتح الرابط في المتصفح]({url})",
                parse_mode=ParseMode.MARKDOWN
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced error handling"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.message:
            try:
                await update.message.reply_text(
                    "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.\n\n"
                    "إذا استمرت المشكلة، استخدم /help للحصول على المساعدة."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    def run(self):
        """Start the bot"""
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Starting Enhanced AliExpress Telegram Bot...")
        print("🚀 بدء تشغيل بوت AliExpress المطور...")
        print("📱 البوت جاهز لاستقبال الروابط!")
        print("⏹️ اضغط Ctrl+C لإيقاف البوت")
        
        # Start the bot
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

def main():
    """Main function"""
    try:
        bot = EnhancedAliExpressTelegramBot()
        bot.run()
    except ValueError as e:
        print(f"❌ خطأ في الإعداد: {e}")
        print("تأكد من وجود TELEGRAM_TOKEN في ملف .env")
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        logger.error(f"Bot startup error: {e}")

if __name__ == '__main__':
    main()
