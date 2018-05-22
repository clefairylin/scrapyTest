# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import re
from w3lib.html import remove_tags

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

from ArticleSpider.utils.common import date_convert, get_number_value, remove_splash


class TakeFirstItemLoader(ItemLoader):
    # 自定义ItemLoader
    default_output_processor = TakeFirst()


def return_value(value):
    return value


def remove_comment_tag(value):
    # 去掉 tag 中的评论
    if "评论" in value:
        return ""
    else:
        return value


def filter_group(value):
    if value not in ['Home', 'Product Categories']:
        return value


class MyItem(scrapy.Item):
    def get_insert_sql(self):
        column_name = []
        params = []
        for key in self.keys():
            if key == "table_name":
                continue
            column_name.append(key)
            if isinstance(self[key], list):
                params.append(self[key][0])
            else:
                params.append(self[key])

        insert_sql = "INSERT INTO {0}({1}) VALUES ({2})"\
            .format(self["table_name"], ", ".join(column_name), ", ".join(["%s"]*len(column_name)))
        return insert_sql, params


class JobboleArticleItem(MyItem):

    table_name = scrapy.Field()
    title = scrapy.Field()
    front_image_url = scrapy.Field(output_processor=MapCompose(return_value))
    front_image_path = scrapy.Field()
    create_date = scrapy.Field(input_processor=MapCompose(date_convert))
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    praise_nums = scrapy.Field(input_processor=MapCompose(get_number_value))
    fav_nums = scrapy.Field(input_processor=MapCompose(get_number_value))
    comment_nums = scrapy.Field(input_processor=MapCompose(get_number_value))
    tag = scrapy.Field(input_processor=MapCompose(remove_comment_tag), output_processor=Join(" * "))
    content = scrapy.Field(input_processor=MapCompose(remove_tags))


class ZhihuQuestionItem(MyItem):
    table_name = scrapy.Field(output_processor=TakeFirst())
    zhihu_id = scrapy.Field(output_processor=TakeFirst())    # 知乎id
    topics = scrapy.Field(output_processor=Join(","))     # 主题
    url = scrapy.Field(output_processor=TakeFirst())    # 问题url
    title = scrapy.Field(output_processor=TakeFirst())    # 标题
    content = scrapy.Field(output_processor=TakeFirst())    # 问题内容
    create_time = scrapy.Field()    # 创建时间
    update_time = scrapy.Field()    # 更新时间
    # 回答数
    answer_num = scrapy.Field(input_processor=MapCompose(get_number_value), output_processor=TakeFirst())
    # 评论数
    comments_num = scrapy.Field(input_processor=MapCompose(get_number_value), output_processor=TakeFirst())
    # 关注该问题人数
    watch_user_num = scrapy.Field(input_processor=MapCompose(get_number_value), output_processor=TakeFirst())
    # 点击数
    click_num = scrapy.Field(input_processor=MapCompose(get_number_value), output_processor=TakeFirst())
    crawl_time = scrapy.Field()    # 爬取时间
    crawl_update_time = scrapy.Field()    # 爬取更新时间


class ZhihuAnswerItem(MyItem):
    table_name = scrapy.Field()
    zhihu_id = scrapy.Field()    # 知乎id
    url = scrapy.Field()    # 回答url
    question_id = scrapy.Field()    # 问题id
    author_id = scrapy.Field()    # 答者用户id
    content = scrapy.Field()    # 回答内容
    praise_num = scrapy.Field()    # 点赞数
    comments_num = scrapy.Field()    # 评论数
    create_time = scrapy.Field()    # 创建时间
    update_time = scrapy.Field()    # 更新时间
    crawl_time = scrapy.Field()    # 爬取时间


class ProductKeywordItem(scrapy.Item):

    id = scrapy.Field()
    shop_url = scrapy.Field()
    product_url = scrapy.Field()
    product_url_object_id = scrapy.Field()
    product_name = scrapy.Field()
    keywords = scrapy.Field(
        output_processor=Join(",")
    )
    product_group = scrapy.Field(
        input_processor=MapCompose(filter_group),
        output_processor=Join(">")
    )
    crawl_time = scrapy.Field()    # 爬取时间

    def get_insert_sql(self):
        insert_sql = "INSERT INTO product_keyword (id, shop_url, product_url, product_url_object_id, product_name," \
                     " keywords, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE product_url=" \
                     " VALUES(product_url), product_url_object_id =VALUES(product_url_object_id), product_name=" \
                     "VALUES (product_name), keywords=VALUES(keywords), crawl_time=VALUES(crawl_time)"
        params = [int(self["id"]), self["shop_url"], self["product_url"], self["product_url_object_id"],
                  self["product_name"], self["keywords"], self["crawl_time"]]
        return insert_sql, params
