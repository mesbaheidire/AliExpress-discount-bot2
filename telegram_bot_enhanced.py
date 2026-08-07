is_real_data = (
    product_info
    and product_info.get("title")
    and product_info.get("title") != "منتج AliExpress"
    and any(k in product_info for k in ["prices", "store", "rating"])
)

if is_real_data:
    formatted_message = self.scraper.format_product_info(product_info, url)
    await processing_msg.edit_text(
        formatted_message,
        parse_mode=ParseMode.MARKDOWN
    )
    return
