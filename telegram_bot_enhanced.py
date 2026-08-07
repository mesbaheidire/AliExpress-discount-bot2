import os
import re
import asyncio
import logging
 
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
 
from enhanced_scraper import (
    EnhancedAliExpressScraper,
    ALIEXPRESS_URL_PATTERN,
)
from aliexpress_api import AliExpressAPI
 
 
# تحميل متغيرات البيئة
load_dotenv()
 
 
# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
 
logger = logging.getLogger(__name__)
 
 
class EnhancedAliExpressTelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.app_key = os.getenv("APP_KEY")
        self.app_secret = os.getenv("APP_SECRET")
 
        if not self.token:
            raise ValueError(
                "TELEGRAM_TOKEN not found in environment variables"
            )
 
        self.scraper = EnhancedAliExpressScraper()
 
        # تشغيل API فقط إذا كانت المفاتيح موجودة
        self.api = None
        if self.app_key and self.app_secret:
            self.api = AliExpressAPI(
                self.app_key,
                self.app_secret,
            )
            logger.info("AliExpress API is configured")
        else:
            logger.warning(
                "APP_KEY or APP_SECRET not found. "
                "API fallback is disabled."
            )
 
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )
 
        self.setup_handlers()
 
    def setup_handlers(self):
        self.application.add_handler(
            CommandHandler("start", self.start_command)
        )
 
        self.application.add_handler(
            CommandHandler("help", self.help_command)
        )
 
        self.application.add_handler(
            CommandHandler("test", self.test_command)
        )
 
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message,
            )
        )
 
    async def start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        welcome_message = """
🤖 **مرحباً بك في بوت AliExpress المطور!**
 
أرسل لي رابط منتج من AliExpress وسأقوم بتحليله وإرسال معلومات مفصلة عن:
 
📣 سعر المنتج بدون تخفيض
💵 سعر التخفيض بالعملات
🛍 نسبة التخفيض
🏪 اسم المتجر
🌟 تقييم المتجر
✈️ معلومات الشحن
 
**الروابط المدعومة:**
 
✅ www.aliexpress.com
✅ ar / fr / de / es / ru / tr / m.aliexpress.com
✅ aliexpress.us / aliexpress.ru
✅ روابط التتبع القصيرة
 
أرسل الرابط وسأقوم بالباقي.
        """
 
        if update.message:
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
            )
 
    async def help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        help_message = """
📖 **دليل استخدام البوت:**
 
**الروابط المدعومة:**
 
• https://www.aliexpress.com/item/123456.html
• https://ar.aliexpress.com/item/123456.html
• https://m.aliexpress.com/item/123456.html
• https://fr.aliexpress.com/item/123456.html
• https://de.aliexpress.com/item/123456.html
• https://aliexpress.us/item/123456.html
• https://aliexpress.ru/item/123456.html
• https://s.click.aliexpress.com/e/xxxx
• https://a.aliexpress.com/xxxx
 
**كيفية الاستخدام:**
 
1. انسخ رابط أي منتج من AliExpress.
2. أرسل الرابط في رسالة للبوت.
3. انتظر قليلًا.
4. ستحصل على معلومات المنتج والتخفيض.
 
**الأوامر المتاحة:**
 
• /start - رسالة الترحيب
• /help - دليل استخدام البوت
• /test - اختبار البوت
        """
 
        if update.message:
            await update.message.reply_text(
                help_message,
                parse_mode=ParseMode.MARKDOWN,
            )
 
    async def test_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        test_message = """
🧪 **اختبار البوت**
 
✅ البوت يعمل ويستقبل الرسائل.
✅ اتصال Telegram يعمل.
✅ نظام تحليل الروابط جاهز.
 
أرسل رابط منتج من AliExpress لاختبار جلب السعر والتخفيض.
        """
 
        if update.message:
            await update.message.reply_text(
                test_message,
                parse_mode=ParseMode.MARKDOWN,
            )
 
    def extract_url_from_message(self, text: str):
        """
        استخراج رابط AliExpress من أي رسالة نصية.
        """
        match = ALIEXPRESS_URL_PATTERN.search(text)
 
        if match:
            return match.group(0).rstrip(".,;!?)")
 
        return None
 
    def has_real_scraped_data(self, product_info) -> bool:
        """
        التأكد من أن البيانات المستخرجة حقيقية وليست
        البيانات الاحتياطية التي يتم إرجاعها عند الحظر.
        """
        if not product_info:
            return False
 
        title = product_info.get("title")
 
        # البيانات الاحتياطية تستخدم هذا العنوان
        if not title or title == "منتج AliExpress":
            return False
 
        # يجب أن توجد معلومة إضافية حقيقية
        has_details = any(
            key in product_info
            for key in [
                "prices",
                "store",
                "rating",
                "shipping",
                "image",
            ]
        )
 
        return has_details
 
    def has_discount_data(self, product_info) -> bool:
        """
        التحقق تحديدًا من وجود بيانات تخفيض حقيقية
        (وليس فقط وجود مفتاح "prices" فارغ أو غير مكتمل).
 
        ملاحظة: هذه الدالة تفترض أن قاموس "prices" قد يحتوي
        على أحد هذه المفاتيح الشائعة. إذا كانت أسماء المفاتيح
        في enhanced_scraper.py مختلفة، أخبرني بها لأضبط الأسماء
        هنا بدقة.
        """
        if not product_info:
            return False
 
        prices = product_info.get("prices")
 
        if not prices or not isinstance(prices, dict):
            return False
 
        possible_original_keys = [
            "original_price",
            "orig_price",
            "list_price",
            "before_discount",
        ]
        possible_discount_keys = [
            "discount_price",
            "sale_price",
            "current_price",
            "after_discount",
        ]
        possible_percentage_keys = [
            "discount_percentage",
            "discount_percent",
            "discount",
        ]
 
        has_original = any(
            prices.get(key) for key in possible_original_keys
        )
        has_discount_price = any(
            prices.get(key) for key in possible_discount_keys
        )
        has_percentage = any(
            prices.get(key) for key in possible_percentage_keys
        )
 
        return has_original and (has_discount_price or has_percentage)
 
    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """
        معالجة الرسائل التي تحتوي على روابط AliExpress.
        """
        if not update.message or not update.message.text:
            return
 
        message_text = update.message.text.strip()
 
        # استخراج الرابط من الرسالة
        url = self.extract_url_from_message(message_text)
 
        if not url:
            await update.message.reply_text(
                "⚠️ لم أجد رابط AliExpress في رسالتك.\n\n"
                "أرسل رابط منتج مثل:\n"
                "`https://www.aliexpress.com/item/123456.html`\n\n"
                "استخدم /help لمشاهدة الروابط المدعومة.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
 
        processing_message = await update.message.reply_text(
            "🔄 **جاري تحليل المنتج...**\n\n"
            "📡 جاري الاتصال بالخادم...\n"
            "🔍 جاري استخراج بيانات المنتج...",
            parse_mode=ParseMode.MARKDOWN,
        )
 
        try:
            # المحاولة الأولى: قراءة صفحة المنتج
            product_info = await asyncio.to_thread(
                self.scraper.get_product_details,
                url,
            )
 
            # تسجيل تشخيصي: أي مفاتيح تم استخراجها فعليًا
            if product_info:
                logger.info(
                    "Scraped keys for %s: %s",
                    url,
                    list(product_info.keys()),
                )
            else:
                logger.warning(
                    "Scraper returned no data at all for %s",
                    url,
                )
 
            # لا نعتبر البيانات الاحتياطية نجاحًا
            if self.has_real_scraped_data(product_info):
                if not self.has_discount_data(product_info):
                    logger.warning(
                        "Product data looks real but no discount "
                        "fields found for %s. prices=%s",
                        url,
                        product_info.get("prices"),
                    )
 
                formatted_message = (
                    self.scraper.format_product_info(
                        product_info,
                        url,
                    )
                )
 
                await processing_message.edit_text(
                    formatted_message,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
 
            # المحاولة الثانية: استخدام AliExpress API
            if self.api:
                await processing_message.edit_text(
                    "🔄 **تعذر قراءة صفحة AliExpress مباشرة.**\n\n"
                    "جاري المحاولة عبر AliExpress API...\n"
                    "⏳ يرجى الانتظار.",
                    parse_mode=ParseMode.MARKDOWN,
                )
 
                product_id = self.scraper.extract_product_id(url)
 
                if product_id:
                    logger.info(
                        "Trying AliExpress API for product ID: %s",
                        product_id,
                    )
 
                    api_result = await asyncio.to_thread(
                        self.api.get_product_detail,
                        product_id,
                    )
 
                    if api_result:
                        formatted_api_message = (
                            self.api.format_api_product_info(
                                api_result
                            )
                        )
 
                        if formatted_api_message:
                            await processing_message.edit_text(
                                formatted_api_message,
                                parse_mode=ParseMode.MARKDOWN,
                            )
                            return
 
                        logger.warning(
                            "AliExpress API returned no usable product data"
                        )
                else:
                    logger.warning(
                        "Could not extract product ID from URL: %s",
                        url,
                    )
 
            # إذا كانت هناك بيانات جزئية، نعرضها للمستخدم
            if product_info:
                formatted_message = (
                    self.scraper.format_product_info(
                        product_info,
                        url,
                    )
                )
 
                await processing_message.edit_text(
                    formatted_message,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
 
            # فشل كامل
            await processing_message.edit_text(
                "❌ **عذرًا، لم أتمكن من الحصول على معلومات المنتج.**\n\n"
                "**الأسباب المحتملة:**\n"
                "• حماية مؤقتة من موقع AliExpress\n"
                "• ظهور CAPTCHA أو حظر للخادم\n"
                "• المنتج غير متوفر أو محذوف\n"
                "• الرابط غير صحيح أو منتهي الصلاحية\n\n"
                "**جرب:**\n"
                "• إرسال رابط المنتج مرة أخرى بعد دقيقة\n"
                "• التأكد من أن الرابط يفتح في المتصفح\n"
                "• استخدام رابط المنتج الكامل بدل الرابط المختصر\n\n"
                f"🔗 [فتح المنتج في AliExpress]({url})",
                parse_mode=ParseMode.MARKDOWN,
            )
 
        except Exception as error:
            logger.exception(
                "Error processing AliExpress URL: %s",
                url,
            )
 
            await processing_message.edit_text(
                "❌ حدث خطأ أثناء معالجة الرابط.\n\n"
                "يرجى المحاولة مرة أخرى بعد قليل.\n\n"
                f"🔗 [فتح المنتج في AliExpress]({url})",
                parse_mode=ParseMode.MARKDOWN,
            )
 
    async def error_handler(
        self,
        update: object,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """
        معالج الأخطاء العامة في Telegram.
        """
        logger.error(
            "Update caused error: %s",
            context.error,
        )
 
        if isinstance(update, Update) and update.message:
            try:
                await update.message.reply_text(
                    "❌ حدث خطأ غير متوقع.\n\n"
                    "يرجى المحاولة مرة أخرى."
                )
            except Exception as error:
                logger.error(
                    "Failed to send error message: %s",
                    error,
                )
 
    def run(self):
        """
        تشغيل البوت باستخدام long polling.
        """
        self.application.add_error_handler(
            self.error_handler
        )
 
        logger.info(
            "Starting Enhanced AliExpress Telegram Bot..."
        )
 
        print("🚀 بدء تشغيل بوت AliExpress المطور...")
        print("📱 البوت جاهز لاستقبال الروابط!")
 
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
 
 
def main():
    try:
        bot = EnhancedAliExpressTelegramBot()
        bot.run()
 
    except ValueError as error:
        print(f"❌ خطأ في الإعداد: {error}")
        print(
            "تأكد من وجود TELEGRAM_TOKEN "
            "في إعدادات Render."
        )
 
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت")
 
    except Exception as error:
        print(f"❌ خطأ في تشغيل البوت: {error}")
        logger.exception("Bot startup error")
 
 
if __name__ == "__main__":
    main()
