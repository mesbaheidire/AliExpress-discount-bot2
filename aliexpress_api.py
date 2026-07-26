import requests
import hashlib
import time
import json
from urllib.parse import quote
import os

class AliExpressAPI:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.listPromotionProduct/505684"
        self.detail_url = "https://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionProductDetail/505684"

    def generate_signature(self, params):
        """Generate signature for API request"""
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Create query string
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # Add secret
        sign_string = self.app_secret + query_string + self.app_secret
        
        # Generate MD5 hash
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
        
        return signature

    def search_products(self, keywords, page_no=1, page_size=20):
        """Search for products using AliExpress API"""
        try:
            params = {
                'app_key': self.app_key,
                'timestamp': str(int(time.time() * 1000)),
                'keywords': keywords,
                'page_no': str(page_no),
                'page_size': str(page_size),
                'target_currency': 'USD',
                'target_language': 'EN',
                'tracking_id': 'default'
            }
            
            # Generate signature
            params['sign'] = self.generate_signature(params)
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error searching products: {e}")
            return None

    def get_product_detail(self, product_id):
        """Get detailed product information"""
        try:
            params = {
                'app_key': self.app_key,
                'timestamp': str(int(time.time() * 1000)),
                'product_ids': str(product_id),
                'target_currency': 'USD',
                'target_language': 'EN',
                'tracking_id': 'default'
            }
            
            # Generate signature
            params['sign'] = self.generate_signature(params)
            
            response = requests.get(self.detail_url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error getting product detail: {e}")
            return None

    def extract_product_id_from_url(self, url):
        """Extract product ID from AliExpress URL"""
        import re
        
        # Pattern for product ID in URL
        patterns = [
            r'/item/(\d+)',
            r'productId=(\d+)',
            r'/(\d+)\.html'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def format_api_product_info(self, product_data):
        """Format API product information for Telegram message"""
        if not product_data or 'resp_result' not in product_data:
            return None
        
        try:
            result = product_data['resp_result']
            if 'result' not in result or not result['result']:
                return None
            
            products = result['result']['products']
            if not products:
                return None
            
            product = products[0]  # Get first product
            
            message = "🛍 **معلومات المنتج من AliExpress API**\n\n"
            
            # Product title
            if 'product_title' in product:
                message += f"📦 **اسم المنتج:** {product['product_title']}\n\n"
            
            # Prices
            if 'target_sale_price' in product:
                message += f"💵 سعر البيع: {product['target_sale_price']} {product.get('target_sale_price_currency', 'USD')}\n"
            
            if 'target_original_price' in product:
                message += f"📣 السعر الأصلي: {product['target_original_price']} {product.get('target_original_price_currency', 'USD')}\n"
            
            # Calculate discount
            if 'target_sale_price' in product and 'target_original_price' in product:
                try:
                    sale_price = float(product['target_sale_price'])
                    original_price = float(product['target_original_price'])
                    if original_price > 0:
                        discount = ((original_price - sale_price) / original_price) * 100
                        message += f"🛍 نسبة التخفيض: {discount:.1f}%\n"
                except (ValueError, TypeError):
                    pass
            
            # Store information
            if 'shop_id' in product:
                message += f"🏪 معرف المتجر: {product['shop_id']}\n"
            
            # Product URL
            if 'product_detail_url' in product:
                message += f"\n🔗 [رابط المنتج]({product['product_detail_url']})"
            
            return message
            
        except Exception as e:
            print(f"Error formatting API product info: {e}")
            return None
