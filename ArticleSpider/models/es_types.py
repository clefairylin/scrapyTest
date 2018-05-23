#!/user/bin/env python
# -*- coding:utf-8 -*-
# @File  : es_types.py
# @Author: lxy
# @Date  : 2018/5/17 9:34
# @Desc  :


from elasticsearch_dsl import DocType, Text, Keyword, Date, Integer, Completion
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer


connections.create_connection(host="localhost")


class MyCustomAnalysis(CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = MyCustomAnalysis("ik_max_word", filters=["lowercase"])


class ArticleType(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer="ik_max_word")
    front_image_url = Keyword()
    front_image_path = Keyword()
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    praise_nums = Integer()
    fav_nums = Integer()
    comment_nums = Integer()
    tag = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"
        doc_type = "article"


if __name__ == '__main__':
    ArticleType.init()
    # article = ArticleType()
