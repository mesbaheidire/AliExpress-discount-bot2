import requests
import hashlib
import hmac
import time
import json
import re
from datetime import datetime
from urllib.parse import unquote

# Correct AliExpress Affiliate Open Platform endpoint
API_URL = "https://api-sg.aliexpress.com/sync"


class AliExpressAPI:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret

    # ── Signature ────────────────────────────────────────────────────────────

    def _sign(self, params: dict) -> str:
        """
        AliExpress Open Platform signature (MD5).
        Formula: MD5( APP_SECRET + key1val1key2val2... + APP_SECRET ).upper()
        Keys sorted alphabetically, 'sign' excluded.
        """
        filtered = {k: v for k, v in params.items() if k != 'sign' and v is not None}
        sorted_pairs = sorted(filtered.items())
        concat = ''.join(f"{k}{v}" for k, v in sorted_pairs)
        sign_str = self.app_secret + concat + self.app_secret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _build_params(self, method: str, extra: dict) -> dict:
        """Build the base parameter dict required by every API call."""
        params = {
            'app_key':     self.app_key,
            'method':      method,
            'sign_method': 'md5',
            'timestamp':   datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'v':           '2.0',
        }
        params.update(extra)
        params['sign'] = self._sign(params)
        return params

    # ── API calls ─────────────────────────────────────────────────────────────

    def get_product_detail(self, product_id: str) -> dict | None:
        """
        aliexpress.affiliate.productdetail.get
        Returns raw API response dict, or None on failure.
        """
        try:
            params = self._build_params(
                method='aliexpress.affiliate.productdetail.get',
                extra={
                    'product_ids':       str(product_id),
                    'target_currency':   'USD',
                    'target_language':   'EN',
                    'tracking_id':       'default',
                    'fields':            'product_id,product_title,target_sale_price,'
                                         'target_original_price,target_sale_price_currency,'
                                         'discount,evaluate_rate,product_detail_url,'
                                         'shop_id,shop_url,first_level_category_name,'
                                         'second_level_category_name',
                }
            )
            response = requests.post(API_URL, data=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[AliExpressAPI] get_product_detail error: {e}")
            return None

    def search_products(self, keywords: str, page_no: int = 1, page_size: int = 20) -> dict | None:
        """
        aliexpress.affiliate.product.query
        Returns raw API response dict, or None on failure.
        """
        try:
            params = self._build_params(
                method='aliexpress.affiliate.product.query',
                extra={
                    'keywords':        keywords,
                    'page_no':         str(page_no),
                    'page_size':       str(page_size),
                    'target_currency': 'USD',
                    'target_language': 'EN',
                    'tracking_id':     'default',
                    'sort':            'SALE_PRICE_ASC',
                }
            )
            response = requests.post(API_URL, data=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[AliExpressAPI] search_products error: {e}")
            return None

    # ── Response parsers ──────────────────────────────────────────────────────

    def _extract_product(self, raw: dict) -> dict | None:
        """
        Navigate the nested response envelope and return the first product dict,
        or None if the response is empty / error.
        """
        try:
            # New envelope: aliexpress_affiliate_productdetail_get_response
            for key in raw:
                if 'response' in key.lower():
                    inner = raw[key]
                    # success check
                    if inner.get('resp_code') not in (None, 200, '200', '0', 0):
                        print(f"[AliExpressAPI] API error code {inner.get('resp_code')}: {inner.get('resp_msg')}")
                        return None
                    result = inner.get('result') or inner.get('resp_result', {}).get('result')
                    if not result:
                        return None
                    products = result.get('products', {})
                    if isinstance(products, dict):
                        products = products.get('product', [])
                    if products:
                        return products[0]
        except Exception as e:
            print(f"[AliExpressAPI] _extract_product error: {e}")
        return None

    def format_api_product_info(self, raw: dict) -> str | None:
        """Format API response into a Telegram-ready message."""
        product = self._extract_product(raw)
        if not product:
            return None

        try:
            msg = "🛍 **معلومات المنتج (AliExpress API)**\n\n"

            title = product.get('product_title', '')
            if title:
                msg += f"📦 **الاسم:** {title}\n\n"

            currency = product.get('target_sale_price_currency', 'USD')
            sale_price = product.get('target_sale_price', '')
            orig_price = product.get('target_original_price', '')

            if orig_price and orig_price != sale_price:
                msg += f"📣 **السعر الأصلي:** {orig_price} {currency}\n"

            if sale_price:
                msg += f"💵 **سعر التخفيض:** {sale_price} {currency}\n"

            # Discount percentage
            discount = product.get('discount', '')
            if discount:
                msg += f"🛍 **نسبة التخفيض:** {discount}%\n"
            else:
                try:
                    o = float(re.sub(r'[^\d.]', '', str(orig_price)))
                    s = float(re.sub(r'[^\d.]', '', str(sale_price)))
                    if o > 0 and s > 0 and o > s:
                        msg += f"🛍 **نسبة التخفيض:** {((o - s) / o * 100):.1f}%\n"
                except (ValueError, TypeError):
                    pass

            # Rating
            rate = product.get('evaluate_rate', '')
            if rate:
                msg += f"🌟 **التقييم:** {rate}\n"

            # Store
            shop_id = product.get('shop_id', '')
            if shop_id:
                msg += f"🏪 **معرف المتجر:** {shop_id}\n"

            # Category
            cat = product.get('first_level_category_name', '')
            if cat:
                msg += f"🗂 **الفئة:** {cat}\n"

            # Link
            url = product.get('product_detail_url', '')
            if url:
                msg += f"\n🔗 [فتح المنتج على AliExpress]({url})"

            return msg

        except Exception as e:
            print(f"[AliExpressAPI] format_api_product_info error: {e}")
            return None

    # ── Utility ───────────────────────────────────────────────────────────────

    def extract_product_id_from_url(self, url: str) -> str | None:
        """Extract numeric product ID from any AliExpress URL."""
        url = unquote(url)
        patterns = [
            r'/item/(\d+)',
            r'/i/(\d+)',
            r'[?&]productId[=:](\d+)',
            r'[?&]item_id[=:](\d+)',
            r'/(\d{10,})',
            r'(\d{10,})\.html',
        ]
        for pattern in patterns:
            m = re.search(pattern, url, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

