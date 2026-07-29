import os
import re
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from enhanced_scraper import EnhancedAliExpressScraper, ALIEXPRESS_URL_PATTERN
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

        self.scraper = EnhancedAliExpressScraper()
        self.api = AliExpressAPI(self.app_key, self.app_secret) if self.app_key and self.app_secret else None

        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = """
🤖 **مرحباً بك في بوت AliExpress المطور!**

أرسل لي رابط منتج من AliExpress وسأقوم بتحليله وإرسال معلومات مفصلة عن:

📣 سعر المنتج بدون تخفيض
💵 سعر التخفيض بالعملات
🛍 نسبة التخفيض
🏪 إسم المتجر
🌟 التقييم الإيجابي للمتجر
✈️ شركة الشحن وتكلفتها

**الروابط المدعومة:**
✅ www.aliexpress.com
✅ ar / fr / de / es / ru / tr / m.aliexpress.com
✅ aliexpress.us / aliexpress.ru
✅ روابط التتبع القصيرة (s.click.aliexpress.com)

فقط أرسل الرابط وسأقوم بالباقي! 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = """
📖 **دليل استخدام البوت:**

**🔗 جميع الروابط المدعومة:**
• https://www.aliexpress.com/item/123456.html
• https://ar.aliexpress.com/item/123456.html
• https://m.aliexpress.com/item/123456.html
• https://fr.aliexpress.com/item/123456.html
• https://de.aliexpress.com/item/123456.html
• https://aliexpress.us/item/123456.html
• https://aliexpress.ru/item/123456.html
• https://s.click.aliexpress.com/e/xxxx (روابط التتبع)
• https://a.aliexpress.com/xxxx (روابط قصيرة)

**📱 كيفية الاستخدام:**
1️⃣ انسخ رابط أي منتج من AliExpress
2️⃣ أرسل الرابط في رسالة للبوت
3️⃣ انتظر قليلاً (5-15 ثانية)
4️⃣ ستحصل على معلومات مفصلة عن المنتج

**⚙️ الأوامر المتاحة:**
• /start - رسالة الترحيب
• /help - هذا الدليل
• /test - اختبار البوت
        """
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        test_message = """
🧪 **اختبار البوت:**

جاري اختبار الاتصال... ✅
جاري اختبار استخراج البيانات... ✅
جاري اختبار التنسيق... ✅

البوت يعمل بشكل طبيعي! 🎉

جرب إرسال رابط منتج من AliExpress لاختبار الوظائف الكاملة.
        """
        await update.message.reply_text(test_message, parse_mode=ParseMode.MARKDOWN)

    def extract_url_from_message(self, text):
        """
        Extract an AliExpress URL from any message text.
        Handles all known domains and short/tracking links.
        """
        match = ALIEXPRESS_URL_PATTERN.search(text)
        if match:
            return match.group(0).rstrip('.,;!?)')
        return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle any text message — look for an AliExpress link inside it"""
        message_text = update.message.text.strip()

        # Extract URL from the message (works even if the link is mixed with text)
        url = self.extract_url_from_message(message_text)

        if not url:
            await update.message.reply_text(
                "⚠️ لم أجد رابط AliExpress في رسالتك.\n\n"
                "أرسل رابط منتج مثل:\n"
                "`https://www.aliexpress.com/item/123456.html`\n\n"
                "تشمل الروابط المدعومة:\n"
                "• جميع نطاقات aliexpress.com الإقليمية\n"
                "• aliexpress.us / aliexpress.ru\n"
                "• روابط التتبع القصيرة (s.click.aliexpress.com)\n\n"
                "استخدم /help لمزيد من المعلومات.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        processing_msg = await update.message.reply_text(
            "🔄 **جاري تحليل المنتج...**\n\n"
            "📡 جاري الاتصال بالخادم...\n"
            "🔍 جاري استخراج البيانات...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Method 1: Enhanced web scraping (supports all URL types)
            product_info = await asyncio.to_thread(self.scraper.get_product_details, url)

            if product_info and any(k in product_info for k in ['title', 'prices', 'store']):
                formatted_message = self.scraper.format_product_info(product_info, url)
                await processing_msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN)
                return

            # Method 2: Try API if available and scraping failed
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

            # Fallback: show partial info if available
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
                "• حماية مؤقتة من موقع AliExpress\n\n"
                "**جرب:**\n"
                "• إعادة المحاولة بعد دقيقة\n"
                "• التأكد من صحة الرابط\n\n"
                f"🔗 [فتح الرابط في المتصفح]({url})",
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await processing_msg.edit_text(
                "❌ حدث خطأ أثناء معالجة الرابط.\n\n"
                "يرجى المحاولة مرة أخرى.\n\n"
                "إذا استمرت المشكلة، تأكد من صحة الرابط.\n\n"
                f"🔗 [فتح الرابط في المتصفح]({url})",
                parse_mode=ParseMode.MARKDOWN
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        self.application.add_error_handler(self.error_handler)
        logger.info("Starting Enhanced AliExpress Telegram Bot...")
        print("🚀 بدء تشغيل بوت AliExpress المطور...")
        print("📱 البوت جاهز لاستقبال الروابط!")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


def main():
    try:
        bot = EnhancedAliExpressTelegramBot()
        bot.run()
    except ValueError as e:
        print(f"❌ خطأ في الإعداد: {e}")
        print("تأكد من وجود TELEGRAM_TOKEN في ملف .env أو في إعدادات Render")
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        logger.error(f"Bot startup error: {e}")


if __name__ == '__main__':
    main()

