import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, parse_qs, unquote
from fake_useragent import UserAgent
import time
import random
 
# All known AliExpress domains -> normalize to www.aliexpress.com
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
                print(f"Resolved short URL: {url} -> {final_url}")
                return final_url
        except Exception as e:
            print(f"Error resolving short URL: {e}")
 
        return url
 
    def normalize_url(self, url):
        """Normalize any AliExpress URL to www.aliexpress.com"""
        url = unquote(url)
 
        if not url.startswith('http'):
            url = 'https://' + url
 
        url = self.resolve_short_url(url)
 
        for domain in ALIEXPRESS_DOMAINS:
            if domain in url:
                url = url.replace(domain, 'www.aliexpress.com')
                break
 
        try:
            parsed = urlparse(url)
            url = f"https://www.aliexpress.com{parsed.path}"
        except Exception:
            pass
 
        return url
 
    def extract_product_id(self, url):
        """Extract product ID from any AliExpress URL format"""
        try:
            url = unquote(url)
 
            patterns = [
                r'/item/(\d+)',
                r'/i/(\d+)',
                r'[?&]productId[=:](\d+)',
                r'[?&]item_id[=:](\d+)',
                r'[?&]product_id[=:](\d+)',
                r'/(\d{10,})',
                r'(\d{10,})\.html',
                r'[?&]id[=:](\d{10,})',
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
            url = self.normalize_url(url)
            print(f"Scraping: {url}")
 
            time.sleep(random.uniform(2, 5))
            self.update_headers()
 
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
 
            soup = BeautifulSoup(response.content, 'html.parser')
 
            product_data = (
                self.extract_from_json_ld(soup) or
                self.extract_from_meta_tags(soup) or
                self.extract_from_scripts(soup) or
                self.extract_from_html_elements(soup)
            )
 
            return product_data or self.create_fallback_data(url)
 
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
 
    # ------------------------------------------------------------------
    # FIX #1: reliable balanced-brace JSON extraction.
    #
    # The previous version used a non-greedy regex like
    #   r'window\.runParams\s*=\s*(\{.+?\});'
    # to capture a JSON object out of inline <script> text. Non-greedy
    # matching stops at the FIRST "};" it finds, which is almost never
    # the real end of a nested JSON object (AliExpress's runParams is
    # deeply nested). That made json.loads() fail silently on nearly
    # every page, so discount/price data extracted from scripts almost
    # never worked. This version finds the opening "{" after a marker
    # string, then walks the text counting brace depth (respecting
    # quoted strings) to find the TRUE matching closing brace.
    # ------------------------------------------------------------------
    def _extract_balanced_json(self, text, start_index):
        """Return the balanced {...} JSON substring starting at start_index."""
        if start_index is None or start_index >= len(text) or text[start_index] != '{':
            return None
 
        depth = 0
        in_string = False
        escape = False
 
        for i in range(start_index, len(text)):
            ch = text[i]
 
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
 
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start_index:i + 1]
 
        return None
 
    def _find_key_recursive(self, data, keys, max_depth=6):
        """
        Search a nested dict/list structure for the first value whose key
        matches any name in `keys`. AliExpress nests pricing info several
        levels deep inside window.runParams (e.g. data -> priceModule),
        and the exact nesting/field names change over time, so a
        recursive search is more resilient than assuming a fixed shape.
        """
        if max_depth < 0:
            return None
 
        if isinstance(data, dict):
            for key in keys:
                if key in data and data[key]:
                    return data[key]
            for value in data.values():
                result = self._find_key_recursive(value, keys, max_depth - 1)
                if result is not None:
                    return result
 
        elif isinstance(data, list):
            for item in data:
                result = self._find_key_recursive(item, keys, max_depth - 1)
                if result is not None:
                    return result
 
        return None
 
    def extract_from_scripts(self, soup):
        """Extract data from inline JavaScript objects (e.g. window.runParams)."""
        try:
            scripts = soup.find_all('script')
            markers = ['window.runParams', 'window.pageData', 'skuModule', 'priceModule']
 
            for script in scripts:
                content = script.string
                if not content:
                    continue
 
                for marker in markers:
                    marker_idx = content.find(marker)
                    if marker_idx == -1:
                        continue
 
                    brace_idx = content.find('{', marker_idx)
                    if brace_idx == -1:
                        continue
 
                    json_str = self._extract_balanced_json(content, brace_idx)
                    if not json_str:
                        continue
 
                    try:
                        data = json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        continue
 
                    result = self.parse_script_data(data)
                    if result:
                        return result
 
            return None
        except Exception as e:
            print(f"Error extracting from scripts: {e}")
            return None
 
    def parse_script_data(self, data):
        """Parse a JavaScript data object pulled from window.runParams / pageData."""
        try:
            if not isinstance(data, dict):
                return None
 
            product_info = {}
 
            title = self._find_key_recursive(
                data, ['subject', 'title', 'productSubject']
            )
            if title:
                product_info['title'] = title
 
            # Try to find a pricing module anywhere in the nested structure.
            price_module = (
                self._find_key_recursive(data, ['priceModule']) or
                self._find_key_recursive(data, ['skuModule'])
            )
 
            prices = {}
 
            if isinstance(price_module, dict):
                # Discounted / current price (several possible field names
                # used across AliExpress page versions).
                current_price = self._find_key_recursive(
                    price_module,
                    ['formatedActivityPrice', 'activityAmount', 'formatedAmount', 'skuVal'],
                    max_depth=3,
                )
                if isinstance(current_price, dict):
                    current_price = current_price.get('formatedAmount') or current_price.get('value')
 
                original_price = self._find_key_recursive(
                    price_module,
                    ['formatedPrice', 'originalPrice', 'minAmount'],
                    max_depth=3,
                )
                if isinstance(original_price, dict):
                    original_price = original_price.get('formatedAmount') or original_price.get('value')
 
                discount_pct = self._find_key_recursive(
                    price_module,
                    ['discount', 'discountRate', 'discountPercent'],
                    max_depth=3,
                )
 
                if current_price:
                    prices['price'] = str(current_price)
                if original_price:
                    prices['original_price'] = str(original_price)
                if discount_pct:
                    prices['discount_percentage'] = str(discount_pct)
 
            if prices:
                product_info['prices'] = prices
 
            return product_info if product_info.get('title') else None
        except Exception as e:
            print(f"Error parsing script data: {e}")
            return None
 
    # ------------------------------------------------------------------
    # FIX #2: the HTML fallback now tries to tell the original price
    # apart from the discounted price (instead of dumping every
    # "price-looking" text into one undifferentiated list that
    # format_product_info could never turn into a discount %).
    # ------------------------------------------------------------------
    def extract_from_html_elements(self, soup):
        """Fallback: extract from visible HTML elements."""
        try:
            product_info = {}
 
            # Title
            for selector in ['h1.product-title-text', 'h1[class*="title"]', 'h1', '.product-title']:
                el = soup.select_one(selector)
                if el and el.text.strip():
                    product_info['title'] = el.text.strip()
                    break
 
            prices = {}
 
            # Original (struck-through) price: usually inside <del>/<s>, or
            # an element whose class hints at "original"/"delete"/"was".
            original_selectors = [
                'del', 's',
                '[class*="origin"]', '[class*="del-price"]', '[class*="was-price"]',
            ]
            for selector in original_selectors:
                el = soup.select_one(selector)
                if el and el.text.strip() and re.search(r'\d', el.text):
                    prices['original_price'] = el.text.strip()
                    break
 
            # Current / sale price: element whose class hints at "sale"/"current"/"activity".
            current_selectors = [
                '[class*="sale-price"]', '[class*="current-price"]',
                '[class*="activity-price"]', '[class*="product-price-value"]',
            ]
            for selector in current_selectors:
                el = soup.select_one(selector)
                if el and el.text.strip() and re.search(r'\d', el.text):
                    prices['price'] = el.text.strip()
                    break
 
            # Explicit discount badge, e.g. "-30%"
            for selector in ['[class*="discount"]']:
                el = soup.select_one(selector)
                if el and el.text.strip():
                    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', el.text)
                    if pct_match:
                        prices['discount_percentage'] = pct_match.group(1)
                        break
 
            # Generic catch-all so we still show *something* even if the
            # more specific selectors above didn't match this page version.
            price_texts = []
            for selector in ['[class*="price"]', '[class*="Price"]', '.uniform-banner-box-price']:
                for el in soup.select(selector):
                    text = el.text.strip()
                    if text and re.search(r'[\d.,]+', text):
                        price_texts.append(text)
 
            if price_texts:
                prices['extracted_prices'] = list(dict.fromkeys(price_texts))[:5]
 
                # If we couldn't identify original/current price via the
                # selectors above but have at least two distinct raw price
                # texts, assume the first is the discounted price and the
                # highest-value one is the original price so a discount %
                # can still be computed.
                if 'price' not in prices or 'original_price' not in prices:
                    numeric_candidates = []
                    for text in prices['extracted_prices']:
                        try:
                            value = float(re.sub(r'[^\d.]', '', text))
                            if value > 0:
                                numeric_candidates.append(value)
                        except ValueError:
                            continue
 
                    if len(numeric_candidates) >= 2:
                        prices.setdefault('price', str(min(numeric_candidates)))
                        prices.setdefault('original_price', str(max(numeric_candidates)))
 
            if prices:
                product_info['prices'] = prices
 
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
            'title': 'منتج AliExpress',
            'status': 'تعذّر استخراج تفاصيل المنتج — قد يكون المنتج محمياً أو الرابط منتهي الصلاحية.',
            'product_id': product_id,
        }
 
    def format_product_info(self, product_data, url):
        """Format product data into a readable Telegram message"""
        if not product_data:
            return f"❌ لم يتم العثور على معلومات للمنتج.\n\n🔗 [فتح الرابط في المتصفح]({url})"
 
        message = "🛍 **معلومات المنتج:**\n\n"
 
        if product_data.get('title'):
            message += f"📦 **الاسم:** {product_data['title']}\n\n"
 
        if 'prices' in product_data:
            prices = product_data['prices']
            currency = prices.get('currency', 'USD')
 
            if prices.get('original_price'):
                message += f"📣 **السعر الأصلي:** {prices['original_price']} {currency}\n"
 
            if prices.get('price'):
                message += f"💵 **سعر التخفيض:** {prices['price']} {currency}\n"
 
            if prices.get('min_price'):
                message += f"💵 **أقل سعر:** {prices['min_price']} {currency}\n"
 
            if prices.get('max_price') and prices['max_price'] != prices.get('min_price'):
                message += f"💵 **أعلى سعر:** {prices['max_price']} {currency}\n"
 
            # Discount percentage: prefer an explicitly-extracted value,
            # otherwise compute it from original vs. current price.
            discount_shown = False
            if prices.get('discount_percentage'):
                try:
                    pct = float(re.sub(r'[^\d.]', '', str(prices['discount_percentage'])))
                    message += f"🛍 **نسبة التخفيض:** {pct:.1f}%\n"
                    discount_shown = True
                except (ValueError, TypeError):
                    pass
 
            if not discount_shown:
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
