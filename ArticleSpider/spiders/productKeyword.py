# -*- coding: utf-8 -*-
import json
from datetime import datetime

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ArticleSpider.items import TakeFirstItemLoader, ProductKeywordItem
from ArticleSpider.utils.common import get_md5, get_string_between


class ProductkeywordSpider(CrawlSpider):
    name = 'productKeyword'
    allowed_domains = ['en.alibaba.com']
    start_urls = ['https://newestmachinery.en.alibaba.com/productlist.html']
    custom_settings = {
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 0.25,
    }

    rules = (
        Rule(LinkExtractor(allow=r'/product/\d+-\d+/.*.html'), callback='parse_keyword'),
        Rule(LinkExtractor(allow=r'/productlist-\d+.html'), follow=True),
    )

    def parse_keyword(self, response):
        item_loader = TakeFirstItemLoader(item=ProductKeywordItem(), response=response)
        start = response.url.find("//")
        end = response.url.find("/", start+2)
        item_loader.add_value("id", get_string_between(response.url, "product/", ("-", "/")))
        item_loader.add_value("shop_url", response.url[:end])
        item_loader.add_value("product_url", response.url)
        item_loader.add_value("product_url_object_id", get_md5(response.url))
        item_loader.add_value("crawl_time", datetime.now())
        if 'related-keywords-box' in response.text:
            item_loader.add_css("keywords", ".related-keywords-box ul li a::text")
            item_loader.add_css("product_name", ".title-text::text")
        else:
            item_loader.add_css("product_name", ".ma-title::text")
            data_json = get_string_between(response.text, "window._PAGE_SCHEMA_ =", "</script>")
            if data_json:
                data = json.loads(data_json)
                keywords = data["children"][3]["children"][1]["children"][3]["attributes"]["productKeywords"]["value"]
                item_loader.add_value("keywords", keywords)
        item_loader.add_css("product_group", ".ui-breadcrumb a::text")

        product_keyword_item = item_loader.load_item()
        yield product_keyword_item
