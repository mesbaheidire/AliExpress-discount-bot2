"""
AliExpress API — Portal (Publisher) API via gw.api.alibaba.com
Signature: MD5( APP_SECRET + key1val1key2val2... + APP_SECRET ).upper()
"""
import hashlib
import re
import time
import requests
from urllib.parse import unquote


class AliExpressAPI:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = str(app_key)
        self.app_secret = str(app_secret)

    # ── Signature ─────────────────────────────────────────────────────────────

    def _sign(self, params: dict) -> str:
        """
        Alibaba Open API v2 signature.
        Formula: MD5( SECRET + key1val1key2val2... + SECRET ).upper()
        'sign' key is excluded before sorting.
        """
        filtered = {k: str(v) for k, v in params.items() if k != 'sign'}
        sorted_pairs = sorted(filtered.items())
        concat = ''.join(f"{k}{v}" for k, v in sorted_pairs)
        sign_str = self.app_secret + concat + self.app_secret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _base_params(self) -> dict:
        return {
            'app_key':   self.app_key,
            'timestamp': str(int(time.time() * 1000)),
        }

    # ── API calls ─────────────────────────────────────────────────────────────

    def get_product_detail(self, product_id: str) -> dict | None:
        """
        portals.open / api.getPromotionProductDetail
        Returns the raw JSON response or None on error.
        """
        url = (
            f"https://gw.api.alibaba.com/openapi/param2/2/portals.open/"
            f"api.getPromotionProductDetail/{self.app_key}"
        )
        params = self._base_params()
        params.update({
            'product_ids':     str(product_id),
            'target_currency': 'USD',
            'target_language': 'EN',
            'tracking_id':     'default',
            'fields': (
                'product_id,product_title,target_sale_price,'
                'target_original_price,target_sale_price_currency,'
                'discount,evaluate_rate,product_detail_url,'
                'shop_id,shop_url,hot_product_commission_rate,'
                'commission_rate,sale_price,original_price,'
                'sale_price_currency,promo_code_info'
            ),
        })
        params['sign'] = self._sign(params)

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            print(f"[API] Portal response: {str(data)[:300]}")
            return data
        except Exception as e:
            print(f"[API] get_product_detail error: {e}")
            return None

    def get_promotion_links(self, product_id: str) -> dict | None:
        """
        portals.open / api.getPromotionLinks — get affiliate links with
        the actual discounted price embedded.
        """
        url = (
            f"https://gw.api.alibaba.com/openapi/param2/2/portals.open/"
            f"api.getPromotionLinks/{self.app_key}"
        )
        params = self._base_params()
        params.update({
            'urls': f"https://www.aliexpress.com/item/{product_id}.html",
            'tracking_id': 'default',
        })
        params['sign'] = self._sign(params)

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            print(f"[API] Promo links response: {str(data)[:300]}")
            return data
        except Exception as e:
            print(f"[API] get_promotion_links error: {e}")
            return None

    # ── Response parsers ──────────────────────────────────────────────────────

    def _find_products(self, raw: dict) -> list:
        """Navigate the response envelope and return a list of product dicts."""
        if not isinstance(raw, dict):
            return []
        # Portal API wraps in resp_result → result → products → product
        for outer in raw.values():
            if not isinstance(outer, dict):
                continue
            result = outer.get('result') or {}
            products = result.get('products') or {}
            if isinstance(products, dict):
                items = products.get('product', [])
                if items:
                    return items if isinstance(items, list) else [items]
            # Some responses put products directly
            if isinstance(products, list) and products:
                return products
        return []

    def format_api_product_info(self, raw: dict) -> str | None:
        """Format Portal API response into a Telegram-ready message."""
        products = self._find_products(raw)
        if not products:
            print(f"[API] No products found in response: {str(raw)[:400]}")
            return None

        p = products[0]
        print(f"[API] Product fields: {list(p.keys())}")

        try:
            msg = "🛍 **معلومات المنتج:**\n\n"

            title = p.get('product_title', '')
            if title:
                msg += f"📦 **الاسم:** {title}\n\n"

            currency = (
                p.get('target_sale_price_currency')
                or p.get('sale_price_currency')
                or 'USD'
            )

            orig = (
                p.get('target_original_price')
                or p.get('original_price')
                or ''
            )
            sale = (
                p.get('target_sale_price')
                or p.get('sale_price')
                or ''
            )

            if orig and orig != sale:
                msg += f"📣 **السعر الأصلي:** {orig} {currency}\n"
            if sale:
                msg += f"💵 **سعر التخفيض:** {sale} {currency}\n"

            # Discount percent
            discount = p.get('discount', '')
            if discount:
                msg += f"🛍 **نسبة التخفيض:** {discount}%\n"
            else:
                try:
                    o = float(re.sub(r'[^\d.]', '', str(orig)))
                    s = float(re.sub(r'[^\d.]', '', str(sale)))
                    if o > 0 and s > 0 and o > s:
                        msg += f"🛍 **نسبة التخفيض:** {(o - s) / o * 100:.1f}%\n"
                except (ValueError, TypeError):
                    pass

            # Commission
            comm = p.get('hot_product_commission_rate') or p.get('commission_rate', '')
            if comm:
                msg += f"💰 **عمولة الأفيليت:** {comm}%\n"

            # Rating
            rate = p.get('evaluate_rate', '')
            if rate:
                msg += f"🌟 **تقييم المنتج:** {rate}\n"

            # Store
            shop = p.get('shop_id', '')
            if shop:
                msg += f"🏪 **معرف المتجر:** {shop}\n"

            # Link
            link = p.get('product_detail_url', '')
            if link:
                msg += f"\n🔗 [فتح المنتج على AliExpress]({link})"

            return msg if title or sale else None

        except Exception as e:
            print(f"[API] format error: {e}")
            return None

    # ── Utility ───────────────────────────────────────────────────────────────

    def extract_product_id_from_url(self, url: str) -> str | None:
        url = unquote(url)
        for pat in [r'/item/(\d+)', r'/i/(\d+)', r'[?&]productId=(\d+)',
                    r'(\d{10,})\.html', r'/(\d{10,})']:
            m = re.search(pat, url, re.IGNORECASE)
            if m:
                return m.group(1)
        return None


