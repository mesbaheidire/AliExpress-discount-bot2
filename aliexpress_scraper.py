import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, parse_qs
from fake_useragent import UserAgent
import time
import random

class AliExpressScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def extract_product_id(self, url):
        """Extract product ID from AliExpress URL"""
        try:
            # Handle different URL formats
            if '/item/' in url:
                # Format: https://www.aliexpress.com/item/1005007354532583.html
                match = re.search(r'/item/(\d+)', url)
                if match:
                    return match.group(1)
            
            # Handle other formats
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Check for productId in query parameters
            if 'productId' in query_params:
                return query_params['productId'][0]
            
            return None
        except Exception as e:
            print(f"Error extracting product ID: {e}")
            return None

    def get_product_details(self, url):
        """Scrape product details from AliExpress URL"""
        try:
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            # Update headers for each request
            self.session.headers.update({'User-Agent': self.ua.random})
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product data from script tags
            product_data = self.extract_product_data_from_scripts(soup)
            
            if not product_data:
                # Fallback to HTML parsing
                product_data = self.extract_product_data_from_html(soup)
            
            return product_data
            
        except Exception as e:
            print(f"Error scraping product: {e}")
            return None

    def extract_product_data_from_scripts(self, soup):
        """Extract product data from JavaScript variables"""
        try:
            # Look for window.runParams or similar data
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'window.runParams' in script.string:
                    # Extract JSON data
                    match = re.search(r'window\.runParams\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            return self.parse_run_params(data)
                        except json.JSONDecodeError:
                            continue
                
                # Look for other data patterns
                if script.string and 'data' in script.string and 'price' in script.string:
                    # Try to extract price information
                    price_matches = re.findall(r'"price":\s*"([^"]+)"', script.string)
                    if price_matches:
                        return {'prices': price_matches}
            
            return None
        except Exception as e:
            print(f"Error extracting from scripts: {e}")
            return None

    def parse_run_params(self, data):
        """Parse runParams data structure"""
        try:
            product_info = {}
            
            # Navigate through the data structure
            if 'data' in data:
                product_data = data['data']
                
                # Extract basic info
                if 'titleModule' in product_data:
                    title_module = product_data['titleModule']
                    product_info['title'] = title_module.get('subject', '')
                
                # Extract price info
                if 'priceModule' in product_data:
                    price_module = product_data['priceModule']
                    product_info['prices'] = {
                        'min_price': price_module.get('minActivityAmount', {}).get('value', ''),
                        'max_price': price_module.get('maxActivityAmount', {}).get('value', ''),
                        'original_price': price_module.get('minAmount', {}).get('value', ''),
                        'currency': price_module.get('minAmount', {}).get('currency', 'USD')
                    }
                
                # Extract store info
                if 'storeModule' in product_data:
                    store_module = product_data['storeModule']
                    product_info['store'] = {
                        'name': store_module.get('storeName', ''),
                        'rating': store_module.get('positiveRate', ''),
                        'id': store_module.get('storeNum', '')
                    }
                
                # Extract shipping info
                if 'shippingModule' in product_data:
                    shipping_module = product_data['shippingModule']
                    product_info['shipping'] = {
                        'company': shipping_module.get('generalFreightInfo', {}).get('originalLayoutResultList', [{}])[0].get('bizData', {}).get('deliveryOptionCode', ''),
                        'cost': shipping_module.get('generalFreightInfo', {}).get('originalLayoutResultList', [{}])[0].get('bizData', {}).get('formattedAmount', '')
                    }
            
            return product_info
        except Exception as e:
            print(f"Error parsing runParams: {e}")
            return None

    def extract_product_data_from_html(self, soup):
        """Fallback method to extract data from HTML elements"""
        try:
            product_info = {}
            
            # Extract title
            title_elem = soup.find('h1', {'data-pl': 'product-title'}) or soup.find('h1', class_='product-title-text')
            if title_elem:
                product_info['title'] = title_elem.get_text(strip=True)
            
            # Extract prices from various possible locations
            price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'price|amount'))
            prices = []
            for elem in price_elements:
                text = elem.get_text(strip=True)
                # Look for price patterns
                price_match = re.search(r'[\$€£¥₹]\s*[\d,]+\.?\d*', text)
                if price_match:
                    prices.append(price_match.group())
            
            if prices:
                product_info['prices'] = {'extracted_prices': prices}
            
            # Extract store name
            store_elem = soup.find(['span', 'div', 'a'], class_=re.compile(r'store|shop'))
            if store_elem:
                product_info['store'] = {'name': store_elem.get_text(strip=True)}
            
            return product_info if product_info else None
            
        except Exception as e:
            print(f"Error extracting from HTML: {e}")
            return None

    def format_product_info(self, product_data, url):
        """Format product information for Telegram message"""
        if not product_data:
            return "❌ لم أتمكن من الحصول على معلومات المنتج"
        
        message = "🛍 **معلومات المنتج من AliExpress**\n\n"
        
        # Product title
        if 'title' in product_data:
            message += f"📦 **اسم المنتج:** {product_data['title']}\n\n"
        
        # Prices
        if 'prices' in product_data:
            prices = product_data['prices']
            if isinstance(prices, dict):
                if 'original_price' in prices and prices['original_price']:
                    message += f"📣 سعر المنتج بدون تخفيض: {prices['original_price']} {prices.get('currency', 'USD')}\n"
                if 'min_price' in prices and prices['min_price']:
                    message += f"💵 سعر التخفيض: {prices['min_price']} {prices.get('currency', 'USD')}\n"
                if 'max_price' in prices and prices['max_price']:
                    message += f"💵 السعر الأقصى: {prices['max_price']} {prices.get('currency', 'USD')}\n"
                
                # Calculate discount percentage
                if 'original_price' in prices and 'min_price' in prices:
                    try:
                        original = float(prices['original_price'])
                        discounted = float(prices['min_price'])
                        if original > 0:
                            discount_percent = ((original - discounted) / original) * 100
                            message += f"🛍 نسبة التخفيض: {discount_percent:.1f}%\n"
                    except (ValueError, TypeError):
                        pass
            elif isinstance(prices, list):
                for i, price in enumerate(prices[:3]):  # Show max 3 prices
                    message += f"💵 السعر {i+1}: {price}\n"
        
        # Store information
        if 'store' in product_data:
            store = product_data['store']
            if 'name' in store and store['name']:
                message += f"🏪 إسم المتجر: {store['name']}\n"
            if 'rating' in store and store['rating']:
                message += f"🌟 التقييم الإيجابي للمتجر: {store['rating']}%\n"
        
        # Shipping information
        if 'shipping' in product_data:
            shipping = product_data['shipping']
            if 'company' in shipping and shipping['company']:
                message += f"✈️ شركة الشحن: {shipping['company']}\n"
            if 'cost' in shipping and shipping['cost']:
                message += f"✈️ عمولة الشحن: {shipping['cost']}\n"
        
        message += f"\n🔗 [رابط المنتج]({url})"
        
        return message
