import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, parse_qs, unquote
from fake_useragent import UserAgent
import time
import random

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

    def extract_product_id(self, url):
        """Extract product ID from AliExpress URL"""
        try:
            # Clean the URL
            url = unquote(url)
            
            # Different patterns for product ID extraction
            patterns = [
                r'/item/(\d+)',
                r'productId[=:](\d+)',
                r'/(\d+)\.html',
                r'item_id[=:](\d+)',
                r'product[_-]?id[=:](\d+)'
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
        """Enhanced product details scraping"""
        try:
            # Clean and normalize URL
            url = self.normalize_url(url)
            
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            # Update headers
            self.update_headers()
            
            # Make request with retries
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

    def normalize_url(self, url):
        """Normalize AliExpress URL"""
        # Convert mobile URLs to desktop
        url = url.replace('m.aliexpress.com', 'www.aliexpress.com')
        url = url.replace('ar.aliexpress.com', 'www.aliexpress.com')
        
        # Ensure https
        if not url.startswith('http'):
            url = 'https://' + url
        
        return url

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
            
            # Basic info
            product_info['title'] = data.get('name', '')
            product_info['description'] = data.get('description', '')
            
            # Price info
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            
            if offers:
                product_info['prices'] = {
                    'price': offers.get('price', ''),
                    'currency': offers.get('priceCurrency', 'USD'),
                    'availability': offers.get('availability', '')
                }
            
            # Brand/Store info
            brand = data.get('brand', {})
            if isinstance(brand, dict):
                product_info['store'] = {'name': brand.get('name', '')}
            
            return product_info
        except Exception as e:
            print(f"Error parsing JSON-LD product: {e}")
            return None

    def extract_from_meta_tags(self, soup):
        """Extract data from meta tags"""
        try:
            product_info = {}
            
            # Title from meta tags
            title_meta = soup.find('meta', property='og:title') or soup.find('meta', {'name': 'title'})
            if title_meta:
                product_info['title'] = title_meta.get('content', '')
            
            # Price from meta tags
            price_meta = soup.find('meta', property='product:price:amount')
            if price_meta:
                currency_meta = soup.find('meta', property='product:price:currency')
                product_info['prices'] = {
                    'price': price_meta.get('content', ''),
                    'currency': currency_meta.get('content', 'USD') if currency_meta else 'USD'
                }
            
            return product_info if product_info else None
        except Exception as e:
            print(f"Error extracting meta tags: {e}")
            return None

    def extract_from_scripts(self, soup):
        """Extract data from script tags"""
        try:
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                # Look for various data patterns
                patterns = [
                    r'window\.runParams\s*=\s*({.*?});',
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.pageData\s*=\s*({.*?});',
                    r'var\s+pageData\s*=\s*({.*?});'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            parsed = self.parse_script_data(data)
                            if parsed:
                                return parsed
                        except json.JSONDecodeError:
                            continue
            
            return None
        except Exception as e:
            print(f"Error extracting from scripts: {e}")
            return None

    def parse_script_data(self, data):
        """Parse data from script variables"""
        try:
            product_info = {}
            
            # Navigate through different data structures
            if 'data' in data:
                data = data['data']
            
            # Extract title
            title_sources = [
                data.get('titleModule', {}).get('subject'),
                data.get('title'),
                data.get('productTitle'),
                data.get('name')
            ]
            
            for title in title_sources:
                if title:
                    product_info['title'] = title
                    break
            
            # Extract prices
            price_module = data.get('priceModule', {})
            if price_module:
                product_info['prices'] = {
                    'min_price': self.extract_price_value(price_module.get('minActivityAmount')),
                    'max_price': self.extract_price_value(price_module.get('maxActivityAmount')),
                    'original_price': self.extract_price_value(price_module.get('minAmount')),
                    'currency': self.extract_currency(price_module.get('minAmount'))
                }
            
            # Extract store info
            store_module = data.get('storeModule', {})
            if store_module:
                product_info['store'] = {
                    'name': store_module.get('storeName', ''),
                    'rating': store_module.get('positiveRate', ''),
                    'id': store_module.get('storeNum', '')
                }
            
            # Extract shipping info
            shipping_module = data.get('shippingModule', {})
            if shipping_module:
                freight_info = shipping_module.get('generalFreightInfo', {})
                if freight_info and 'originalLayoutResultList' in freight_info:
                    shipping_data = freight_info['originalLayoutResultList']
                    if shipping_data and len(shipping_data) > 0:
                        biz_data = shipping_data[0].get('bizData', {})
                        product_info['shipping'] = {
                            'company': biz_data.get('deliveryOptionCode', ''),
                            'cost': biz_data.get('formattedAmount', '')
                        }
            
            return product_info if product_info else None
        except Exception as e:
            print(f"Error parsing script data: {e}")
            return None

    def extract_price_value(self, price_obj):
        """Extract price value from price object"""
        if isinstance(price_obj, dict):
            return price_obj.get('value', '')
        return str(price_obj) if price_obj else ''

    def extract_currency(self, price_obj):
        """Extract currency from price object"""
        if isinstance(price_obj, dict):
            return price_obj.get('currency', 'USD')
        return 'USD'

    def extract_from_html_elements(self, soup):
        """Fallback: extract from HTML elements"""
        try:
            product_info = {}
            
            # Extract title
            title_selectors = [
                'h1[data-pl="product-title"]',
                'h1.product-title-text',
                '.product-title',
                'h1',
                '.pdp-product-name'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_info['title'] = title_elem.get_text(strip=True)
                    break
            
            # Extract prices
            price_selectors = [
                '.notranslate',
                '[class*="price"]',
                '[class*="amount"]',
                '[data-spm-anchor-id*="price"]'
            ]
            
            prices = []
            for selector in price_selectors:
                price_elems = soup.select(selector)
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    # Look for price patterns
                    price_matches = re.findall(r'[\$€£¥₹]\s*[\d,]+\.?\d*', text)
                    prices.extend(price_matches)
            
            if prices:
                # Remove duplicates and keep unique prices
                unique_prices = list(set(prices))
                product_info['prices'] = {'extracted_prices': unique_prices}
            
            # Extract store name
            store_selectors = [
                '.shop-name',
                '.store-name',
                '[class*="store"]',
                '[class*="shop"]'
            ]
            
            for selector in store_selectors:
                store_elem = soup.select_one(selector)
                if store_elem:
                    product_info['store'] = {'name': store_elem.get_text(strip=True)}
                    break
            
            return product_info if product_info else None
            
        except Exception as e:
            print(f"Error extracting from HTML: {e}")
            return None

    def create_fallback_data(self, url):
        """Create fallback data when scraping fails"""
        product_id = self.extract_product_id(url)
        return {
            'title': f'منتج AliExpress - {product_id}' if product_id else 'منتج AliExpress',
            'url': url,
            'status': 'تم العثور على الرابط ولكن لم يتم الحصول على تفاصيل كاملة'
        }

    def is_aliexpress_url(self, text):
        """Check if the text contains an AliExpress URL"""
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

    def format_product_info(self, product_data, url):
        """Enhanced formatting for product information"""
        if not product_data:
            return "❌ لم أتمكن من الحصول على معلومات المنتج"
        
        message = "🛍 **معلومات المنتج من AliExpress**\n\n"
        
        # Product title
        if 'title' in product_data and product_data['title']:
            title = product_data['title'][:200] + "..." if len(product_data['title']) > 200 else product_data['title']
            message += f"📦 **اسم المنتج:** {title}\n\n"
        
        # Prices
        if 'prices' in product_data:
            prices = product_data['prices']
            
            if isinstance(prices, dict):
                currency = prices.get('currency', 'USD')
                
                # Original price
                if 'original_price' in prices and prices['original_price']:
                    message += f"📣 سعر المنتج بدون تخفيض: {prices['original_price']} {currency}\n"
                
                # Sale prices
                if 'min_price' in prices and prices['min_price']:
                    message += f"💵 سعر التخفيض: {prices['min_price']} {currency}\n"
                
                if 'max_price' in prices and prices['max_price'] and prices['max_price'] != prices.get('min_price'):
                    message += f"💵 السعر الأقصى: {prices['max_price']} {currency}\n"
                
                # Single price
                if 'price' in prices and prices['price']:
                    message += f"💵 السعر: {prices['price']} {currency}\n"
                
                # Calculate discount percentage
                if 'original_price' in prices and 'min_price' in prices:
                    try:
                        original = float(re.sub(r'[^\d.]', '', str(prices['original_price'])))
                        discounted = float(re.sub(r'[^\d.]', '', str(prices['min_price'])))
                        if original > 0 and discounted > 0:
                            discount_percent = ((original - discounted) / original) * 100
                            message += f"🛍 نسبة التخفيض: {discount_percent:.1f}%\n"
                    except (ValueError, TypeError):
                        pass
                
                # Extracted prices (fallback)
                if 'extracted_prices' in prices:
                    message += "💵 الأسعار المتاحة:\n"
                    for i, price in enumerate(prices['extracted_prices'][:3]):
                        message += f"   • {price}\n"
        
        # Store information
        if 'store' in product_data:
            store = product_data['store']
            if 'name' in store and store['name']:
                message += f"🏪 إسم المتجر: {store['name']}\n"
            if 'rating' in store and store['rating']:
                message += f"🌟 التقييم الإيجابي للمتجر: {store['rating']}%\n"
            if 'id' in store and store['id']:
                message += f"🆔 معرف المتجر: {store['id']}\n"
        
        # Shipping information
        if 'shipping' in product_data:
            shipping = product_data['shipping']
            if 'company' in shipping and shipping['company']:
                message += f"✈️ شركة الشحن: {shipping['company']}\n"
            if 'cost' in shipping and shipping['cost']:
                message += f"✈️ عمولة الشحن: {shipping['cost']}\n"
        
        # Status message for partial data
        if 'status' in product_data:
            message += f"\n⚠️ {product_data['status']}\n"
        
        message += f"\n🔗 [رابط المنتج]({url})"
        
        return message
