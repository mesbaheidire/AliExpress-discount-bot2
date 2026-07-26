# دليل نشر بوت AliExpress Telegram

## 📋 المتطلبات

### متطلبات النظام
- Python 3.8 أو أحدث
- اتصال بالإنترنت
- خادم أو VPS (للنشر المستمر)

### المكتبات المطلوبة
جميع المكتبات موجودة في `requirements.txt`:
```
python-telegram-bot==22.1
requests==2.32.4
beautifulsoup4==4.13.4
lxml==6.0.0
fake-useragent==2.2.0
python-dotenv==1.1.1
aiohttp==3.12.13
```

## 🚀 التثبيت والإعداد

### 1. تحميل الملفات
```bash
# نسخ جميع ملفات المشروع إلى الخادم
scp -r aliexpress_telegram_bot/ user@server:/path/to/bot/
```

### 2. تثبيت المتطلبات
```bash
cd aliexpress_telegram_bot
pip3 install -r requirements.txt
```

### 3. إعداد متغيرات البيئة
تأكد من أن ملف `.env` يحتوي على:
```env
# Telegram bot token (مطلوب)
TELEGRAM_TOKEN=7599400354:AAF1w0BGLe2cC6XSD7hrFm93QttYVk8CiBU

# AliExpress API credentials (اختياري)
APP_KEY=505684
APP_SECRET=li42sLpysSjGfKEHteMQsrZeJjC05VJa
```

### 4. اختبار البوت
```bash
# اختبار الإعداد
python3 test_bot_startup.py

# اختبار الوظائف
python3 test_enhanced.py
```

## 🏃‍♂️ تشغيل البوت

### التشغيل المباشر
```bash
# الطريقة الأولى (مستحسنة)
python3 start_bot.py

# الطريقة الثانية
python3 telegram_bot_enhanced.py

# الطريقة الثالثة
python3 run.py
```

### التشغيل في الخلفية
```bash
# باستخدام nohup
nohup python3 start_bot.py > bot.log 2>&1 &

# باستخدام screen
screen -S aliexpress_bot
python3 start_bot.py
# اضغط Ctrl+A ثم D للخروج من screen

# للعودة إلى screen
screen -r aliexpress_bot
```

### التشغيل كخدمة (systemd)
إنشاء ملف خدمة:
```bash
sudo nano /etc/systemd/system/aliexpress-bot.service
```

محتوى الملف:
```ini
[Unit]
Description=AliExpress Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/aliexpress_telegram_bot
ExecStart=/usr/bin/python3 start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

تفعيل الخدمة:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aliexpress-bot
sudo systemctl start aliexpress-bot
sudo systemctl status aliexpress-bot
```

## 🔧 إعدادات متقدمة

### تخصيص السلوك
يمكن تعديل الملفات التالية:

**`enhanced_scraper.py`**
- تعديل فترات الانتظار
- إضافة مواقع جديدة
- تحسين استخراج البيانات

**`telegram_bot_enhanced.py`**
- تخصيص الرسائل
- إضافة أوامر جديدة
- تعديل منطق المعالجة

### مراقبة الأداء
```bash
# مراقبة السجلات
tail -f logs/bot_*.log

# مراقبة استخدام الموارد
htop
```

## 🛡️ الأمان

### حماية البيانات الحساسة
- لا تشارك ملف `.env`
- استخدم HTTPS للاتصالات
- قم بتحديث المكتبات بانتظام

### النسخ الاحتياطي
```bash
# نسخ احتياطي للمشروع
tar -czf aliexpress_bot_backup_$(date +%Y%m%d).tar.gz aliexpress_telegram_bot/

# نسخ احتياطي للسجلات
cp -r logs/ backup_logs_$(date +%Y%m%d)/
```

## 🔍 استكشاف الأخطاء

### مشاكل شائعة

**1. خطأ في Token**
```
❌ خطأ في الإعداد: TELEGRAM_TOKEN not found
```
**الحل:** تأكد من وجود `TELEGRAM_TOKEN` في ملف `.env`

**2. خطأ في المكتبات**
```
❌ خطأ في استيراد المكتبات: No module named 'telegram'
```
**الحل:** `pip3 install -r requirements.txt`

**3. خطأ في الشبكة**
```
❌ Error scraping product: HTTPSConnectionPool
```
**الحل:** تحقق من اتصال الإنترنت وإعدادات الجدار الناري

**4. حظر من AliExpress**
```
❌ Access denied (403)
```
**الحل:** انتظر قليلاً وحاول مرة أخرى، البوت يتعامل مع هذا تلقائياً

### فحص الحالة
```bash
# فحص حالة البوت
ps aux | grep python3

# فحص السجلات
tail -n 50 logs/bot_*.log

# فحص استخدام الذاكرة
free -h
```

## 📊 مراقبة الأداء

### إحصائيات الاستخدام
السجلات تحتوي على:
- عدد الطلبات المعالجة
- أوقات الاستجابة
- معدل النجاح/الفشل
- أخطاء النظام

### تحسين الأداء
- استخدم خادم بذاكرة كافية (512MB+)
- تأكد من سرعة الإنترنت الجيدة
- راقب استخدام CPU والذاكرة

## 🔄 التحديثات

### تحديث البوت
```bash
# إيقاف البوت
sudo systemctl stop aliexpress-bot

# نسخ احتياطي
cp -r aliexpress_telegram_bot/ backup_$(date +%Y%m%d)/

# تحديث الملفات
# (نسخ الملفات الجديدة)

# إعادة تشغيل
sudo systemctl start aliexpress-bot
```

### تحديث المكتبات
```bash
pip3 install --upgrade -r requirements.txt
```

## 📞 الدعم

### ملفات مهمة للدعم
- `logs/bot_*.log` - سجلات البوت
- `.env` - إعدادات البيئة (لا تشاركها)
- `requirements.txt` - قائمة المكتبات

### معلومات النظام
```bash
# معلومات Python
python3 --version

# معلومات النظام
uname -a

# مساحة القرص
df -h
```

## ✅ قائمة التحقق للنشر

- [ ] تثبيت Python 3.8+
- [ ] تثبيت المكتبات من requirements.txt
- [ ] إعداد ملف .env بالتوكن الصحيح
- [ ] تشغيل test_bot_startup.py بنجاح
- [ ] اختبار البوت مع رابط تجريبي
- [ ] إعداد التشغيل في الخلفية
- [ ] إعداد مراقبة السجلات
- [ ] إعداد النسخ الاحتياطي
- [ ] اختبار إعادة التشغيل التلقائي

## 🎯 نصائح للنجاح

1. **ابدأ بالاختبار المحلي** قبل النشر على الخادم
2. **راقب السجلات** في الأيام الأولى
3. **اعمل نسخ احتياطية منتظمة**
4. **تابع تحديثات المكتبات** للأمان
5. **اختبر البوت بانتظام** للتأكد من عمله
