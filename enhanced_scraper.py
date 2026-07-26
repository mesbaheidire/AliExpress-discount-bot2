import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, parse_qs, unquote
from fake_useragent import UserAgent
import time
import random

# All known AliExpress domains → normalize to www.aliexpress.com
ALIEXPRESS_DOMAINS = [
    'm.aliexpress.com',
    'ar.aliexpress.com',
    'fr.aliexpress.com',
    'de.aliexpress.com',
    'es.aliexpress.com',
    'pt.aliexpress.com',
    'ru.aliexpress.com',
    'tr.aliexpress.com',
    'pl.aliexpress.com',
    'nl.aliexpress.com',
    'it.aliexpress.com',
    'ja.aliexpress.com',
    'ko.aliexpress.com',
    'he.aliexpress.com',
    'id.aliexpress.com',
    'th.aliexpress.com',
    'vi.aliexpress.com',
    'aliexpress.us',
    'aliexpress.ru',
    'best.aliexpress.com',
]

# Short/tracking link domains that need redirect resolution
SHORT_LINK_DOMAINS = [
    's.click.aliexpress.com',
    'click.aliexpress.com',
    'a.aliexpress.com',
    'uae.aliexpress.com',
]

# Full regex pattern covering all AliExpress link types
ALIEXPRESS_URL_PATTERN = re.compile(
    r'https?://'
    r'(?:(?:www|m|ar|fr|de|es|pt|ru|tr|pl|nl|it|ja|ko|he|id|th|vi|best|uae)\.)?' 
    r'(?:aliexpress\.com|aliexpress\.us|aliexpress\.ru)'
    r'[^\s<>"\']*'
    r'|https?://(?:s\.click|click|a)\.aliexpress\.com[^\s<>"\']*',
    re.IGNORECASE
)


class EnhancedAliExpressScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()

    def update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

    def is_aliexpress_url(self, url):
        """Check if a URL is any valid AliExpress link"""
        return bool(ALIEXPRESS_URL_PATTERN.search(url))

    def resolve_short_url(self, url):
        """Follow redirects for short/tracking links to get the real product URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if any(short in domain for short in SHORT_LINK_DOMAINS):
                self.update_headers()
                response = self.session.head(url, timeout=15, allow_redirects=True)
                final_url = response.url
                print(f"Resolved short URL: {url} → {final_url}")
                return final_url
        except Exception as e:
            print(f"Error resolving short URL: {e}")
        return url

    def normalize_url(self, url):
        """Normalize any AliExpress URL to www.aliexpress.com"""
        # Decode percent-encoded characters
        url = unquote(url)

        # Ensure scheme
        if not url.startswith('http'):
            url = 'https://' + url

        # Resolve short/tracking links first
        url = self.resolve_short_url(url)

        # Replace all known regional/mobile domains with www
        for domain in ALIEXPRESS_DOMAINS:
            if domain in url:
                url = url.replace(domain, 'www.aliexpress.com')
                break

        # Strip unnecessary query parameters (keep only essential ones)
        try:
            parsed = urlparse(url)
            # Keep the path clean
            url = f"https://www.aliexpress.com{parsed.path}"
        except Exception:
            pass

        return url

    def extract_product_id(self, url):
        """Extract product ID from any AliExpress URL format"""
        try:
            url = unquote(url)

            patterns = [
                r'/item/(\d+)',                  # standard: /item/123456.html
                r'/i/(\d+)',                     # short: /i/123456.html
                r'[?&]productId[=:](\d+)',       # query param
                r'[?&]item_id[=:](\d+)',         # query param variant
                r'[?&]product_id[=:](\d+)',      # query param variant
                r'/(\d{10,})',                   # any 10+ digit number in path
                r'(\d{10,})\.html',              # number before .html
                r'[?&]id[=:](\d{10,})',          # id= param with long number
            ]

            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    return match.group(1)

            return None
        except Exception as e:
            print(f"Error extracting product ID: {e}")
            return None

    def get_product_details(self, url):
        """Enhanced product details scraping with full URL support"""
        try:
            # Normalize URL (follows redirects, fixes domain)
            url = self.normalize_url(url)
            print(f"Scraping: {url}")

            # Add random delay
            time.sleep(random.uniform(2, 5))

            # Update headers for each request
            self.update_headers()

            # Make request with retries
            response = None
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=30, allow_redirects=True)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 403:
                        print(f"Access denied (403), attempt {attempt + 1}")
                        time.sleep(random.uniform(5, 10))
                        self.update_headers()
                    else:
                        print(f"HTTP {response.status_code}, attempt {attempt + 1}")
                        time.sleep(random.uniform(3, 7))
                except requests.RequestException as e:
                    print(f"Request error on attempt {attempt + 1}: {e}")
                    if attempt < 2:
                        time.sleep(random.uniform(5, 10))
                    else:
                        raise

            if response is None:
                return self.create_fallback_data(url)

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try multiple extraction methods
            product_data = (
                self.extract_from_json_ld(soup) or
                self.extract_from_meta_tags(soup) or
                self.extract_from_scripts(soup) or
                self.extract_from_html_elements(soup)
            )

            return product_data

        except Exception as e:
            print(f"Error scraping product: {e}")
            return self.create_fallback_data(url)

    def extract_from_json_ld(self, soup):
        """Extract data from JSON-LD structured data"""
        try:
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return self.parse_json_ld_product(data)
            return None
        except Exception as e:
            print(f"Error extracting JSON-LD: {e}")
            return None

    def parse_json_ld_product(self, data):
        """Parse JSON-LD product data"""
        try:
            product_info = {}
            product_info['title'] = data.get('name', '')
            product_info['description'] = data.get('description', '')

            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            if offers:
                product_info['prices'] = {
                    'price': offers.get('price', ''),
                    'currency': offers.get('priceCurrency', 'USD'),
                }

            rating_data = data.get('aggregateRating', {})
            if rating_data:
                product_info['rating'] = {
                    'value': rating_data.get('ratingValue', ''),
                    'count': rating_data.get('reviewCount', ''),
                }

            return product_info if product_info.get('title') else None
        except Exception as e:
            print(f"Error parsing JSON-LD product: {e}")
            return None

    def extract_from_meta_tags(self, soup):
        """Extract data from Open Graph / meta tags"""
        try:
            product_info = {}

            og_title = soup.find('meta', property='og:title')
            if og_title:
                product_info['title'] = og_title.get('content', '')

            og_price = soup.find('meta', property='product:price:amount')
            og_currency = soup.find('meta', property='product:price:currency')
            if og_price:
                product_info['prices'] = {
                    'price': og_price.get('content', ''),
                    'currency': og_currency.get('content', 'USD') if og_currency else 'USD',
                }

            og_image = soup.find('meta', property='og:image')
            if og_image:
                product_info['image'] = og_image.get('content', '')

            return product_info if product_info.get('title') else None
        except Exception as e:
            print(f"Error extracting meta tags: {e}")
            return None

    def extract_from_scripts(self, soup):
        """Extract data from inline JavaScript objects"""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                content = script.string

                # Look for window.runParams or pageData patterns
                patterns = [
                    r'window\.runParams\s*=\s*(\{.+?\});',
                    r'"data"\s*:\s*(\{.+?"productId".+?\})',
                    r'skuModule\s*:\s*(\{.+?\})',
                ]
                for pattern in patterns:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            result = self.parse_script_data(data)
                            if result:
                                return result
                        except Exception:
                            continue

            return None
        except Exception as e:
            print(f"Error extracting from scripts: {e}")
            return None

    def parse_script_data(self, data):
        """Parse JavaScript data object"""
        try:
            product_info = {}
            if isinstance(data, dict):
                title = (
                    data.get('subject') or
                    data.get('title') or
                    data.get('productSubject') or
                    ''
                )
                if title:
                    product_info['title'] = title

                price_data = data.get('skuModule', {}) or data.get('priceModule', {})
                if price_data:
                    product_info['prices'] = {
                        'price': str(price_data.get('formatedActivityPrice', '')),
                        'original_price': str(price_data.get('formatedPrice', '')),
                    }

            return product_info if product_info.get('title') else None
        except Exception:
            return None

    def extract_from_html_elements(self, soup):
        """Fallback: extract from visible HTML elements"""
        try:
            product_info = {}

            # Title
            for selector in ['h1.product-title-text', 'h1[class*="title"]', 'h1', '.product-title']:
                el = soup.select_one(selector)
                if el and el.text.strip():
                    product_info['title'] = el.text.strip()
                    break

            # Prices
            price_texts = []
            for selector in [
                '[class*="price"]',
                '[class*="Price"]',
                '.uniform-banner-box-price',
            ]:
                for el in soup.select(selector):
                    text = el.text.strip()
                    if text and re.search(r'[\d.,]+', text):
                        price_texts.append(text)

            if price_texts:
                product_info['prices'] = {'extracted_prices': list(dict.fromkeys(price_texts))[:5]}

            # Store
            for selector in ['[class*="store-name"]', '[class*="shop-name"]', 'a[href*="store/"]']:
                el = soup.select_one(selector)
                if el and el.text.strip():
                    product_info['store'] = {'name': el.text.strip()}
                    break

            return product_info if product_info.get('title') else None
        except Exception as e:
            print(f"Error extracting HTML elements: {e}")
            return None

    def create_fallback_data(self, url):
        """Create minimal fallback data when scraping fails"""
        product_id = self.extract_product_id(url)
        return {
            'title': f'منتج AliExpress',
            'status': 'تعذّر استخراج تفاصيل المنتج — قد يكون المنتج محمياً أو الرابط منتهي الصلاحية.',
            'product_id': product_id,
        }

    def format_product_info(self, product_data, url):
        """Format product data into a readable Telegram message"""
        if not product_data:
            return f"❌ لم يتم العثور على معلومات للمنتج.\n\n🔗 [فتح الرابط في المتصفح]({url})"

        message = "🛍 **معلومات المنتج:**\n\n"

        if 'title' in product_data and product_data['title']:
            message += f"📦 **الاسم:** {product_data['title']}\n\n"

        if 'prices' in product_data:
            prices = product_data['prices']
            currency = prices.get('currency', 'USD')

            if 'original_price' in prices and prices['original_price']:
                message += f"📣 **السعر الأصلي:** {prices['original_price']} {currency}\n"

            if 'price' in prices and prices['price']:
                message += f"💵 **سعر التخفيض:** {prices['price']} {currency}\n"

            if 'min_price' in prices and prices['min_price']:
                message += f"💵 **أقل سعر:** {prices['min_price']} {currency}\n"

            if 'max_price' in prices and prices['max_price'] and prices['max_price'] != prices.get('min_price'):
                message += f"💵 **أعلى سعر:** {prices['max_price']} {currency}\n"

            # Calculate discount
            try:
                orig = float(re.sub(r'[^\d.]', '', str(prices.get('original_price', ''))))
                disc = float(re.sub(r'[^\d.]', '', str(prices.get('price', '') or prices.get('min_price', ''))))
                if orig > 0 and disc > 0 and orig > disc:
                    pct = ((orig - disc) / orig) * 100
                    message += f"🛍 **نسبة التخفيض:** {pct:.1f}%\n"
            except (ValueError, TypeError):
                pass

            if 'extracted_prices' in prices:
                message += "💵 **الأسعار المتاحة:**\n"
                for p in prices['extracted_prices'][:3]:
                    message += f"  • {p}\n"

        if 'store' in product_data:
            store = product_data['store']
            if store.get('name'):
                message += f"🏪 **المتجر:** {store['name']}\n"
            if store.get('rating'):
                message += f"🌟 **تقييم المتجر:** {store['rating']}%\n"

        if 'shipping' in product_data:
            shipping = product_data['shipping']
            if shipping.get('company'):
                message += f"✈️ **شركة الشحن:** {shipping['company']}\n"
            if shipping.get('cost'):
                message += f"✈️ **تكلفة الشحن:** {shipping['cost']}\n"

        if 'rating' in product_data:
            rating = product_data['rating']
            if rating.get('value'):
                message += f"⭐ **التقييم:** {rating['value']}"
                if rating.get('count'):
                    message += f" ({rating['count']} تقييم)"
                message += "\n"

        if 'status' in product_data:
            message += f"\n⚠️ {product_data['status']}\n"

        message += f"\n🔗 [فتح المنتج على AliExpress]({url})"
        return message

