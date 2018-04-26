# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from urllib import parse

from ArticleSpider.items import JobboleArticleItem, TakeFirstItemLoader
from ArticleSpider.utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):

        # 解析列表页所有文章的url，下载后解析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").get("")
            post_url = post_node.css("::attr(href)").get("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url},
                          callback=self.parse_detail)
        # 提取下一页的url进行下载
        # next_url = response.css(".next.page-numbers::attr(href)").get()
        # if next_url:
        #     yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        # 通过item loader加载item
        item_loader = TakeFirstItemLoader(item=JobboleArticleItem(), response=response)
        item_loader.add_value("table_name", "jobbole_article")
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [response.meta.get("front_image_url", "")])
        item_loader.add_css("create_date", ".entry-meta-hide-on-mobile::text")
        item_loader.add_css("praise_nums", "span.vote-post-up h10::text")
        item_loader.add_css("fav_nums", "span.bookmark-btn::text")
        item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
        item_loader.add_css("tag", ".entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", ".entry")

        article_item = item_loader.load_item()
        yield article_item
