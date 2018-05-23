# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json

import pymysql
from scrapy import signals
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
from pymysql import cursors
from w3lib.html import remove_tags
from scrapy.xlib.pydispatch import dispatcher
from elasticsearch_dsl.connections import connections

from ArticleSpider.models.es_types import ArticleType


es = connections.create_connection(ArticleType._doc_type.using)


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 通过json exporter导出json文件
    def __init__(self):
        self.file = open('articleExporter.json', "wb")
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()


class MysqlPipeline(object):
    def __init__(self):
        self.conn = pymysql.connect('192.168.1.160', 'root', 'root', 'scrapy_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path,
            comment_nums, fav_nums, praise_nums, tag, content) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item["title"], item["create_date"], item["url"], item["url_object_id"],
                                         item["front_image_url"], item["front_image_path"], item["comment_nums"],
                                         item["fav_nums"], item["praise_nums"], item["tag"], item["content"]))
        self.conn.commit()
        return item


class MysqlTwistedPipeline(object):
    """
        Twisted 异步存储
    """
    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.data = []
        self.count = 0
        self.last_sql = None
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    @classmethod
    def from_settings(cls, settings):
        daparams = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset="utf8",
            cursorclass=cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("pymysql", **daparams)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用 twisted 异步执行 mysql 插入
        query = self.dbpool.runInteraction(self.do_insert, item)
        # 处理异常
        query.addErrback(self.handle_error)

    def spider_closed(self):
        query = self.dbpool.runInteraction(self.insert_all)
        query.addErrback(self.handle_error)

    def handle_error(self, failure):
        print(failure)

    def do_insert(self, cursor, item):
        self.count += 1
        sql, params = item.get_insert_sql()
        self.last_sql = sql
        self.data.append(params)
        if self.count > 500:
            self.count = 0
            cursor.executemany(sql, self.data)
            self.data.clear()
        return item

    def insert_all(self, cursor):
        cursor.executemany(self.last_sql, self.data)


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            for ok, value in results:
                item['front_image_path'] = value['path']
        return item


class ElasticSearchPipeline(object):
    def get_suggest(self, index, info):
        used_set, suggests = set(), []
        for text, weight in info:
            if text:
                words = es.indices.analyze(index=index, params={"analyzer": "ik_max_word", "filter": ["lowercase"]},
                                           body=text)
                analyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
                analyzed_words -= used_set
            else:
                analyzed_words = set()
            if analyzed_words:
                suggests.append({"input": list(analyzed_words), "weight": weight})
        return suggests

    def process_item(self, item, spider):
        article = ArticleType()
        article.title = item["title"]
        article.url = item["url"]
        article.front_image_path = item.get("front_image_path")
        article.front_image_url = item["front_image_url"]
        article.create_date = item["create_date"]
        article.praise_nums = item["praise_nums"]
        article.fav_nums = item["fav_nums"]
        article.comment_nums = item["comment_nums"]
        article.tag = item["tag"]
        article.content = remove_tags(item["content"])
        article.meta.id = item["url_object_id"]

        article.suggest = self.get_suggest(ArticleType._doc_type.index, ((article.title, 10), (article.tag, 7)))
        article.save()
        return item
