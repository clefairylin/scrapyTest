# -*- coding: utf-8 -*-
import json
import re

import scrapy
import time

from datetime import datetime

from scrapy.loader import ItemLoader
from selenium import webdriver

from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem
from ArticleSpider.utils import zhihu_login


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_clos' \
                       'ed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_r' \
                       'eason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ce' \
                       'ditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cup' \
                       'dated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%' \
                       '2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%' \
                       '5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics' \
                       '&offset={1}&limit={2}&sort_by=default'

    headers = {
        "Host": "www.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
                      "/63.0.3239.84 Safari/537.36",
        "Referer": "https://www.zhihu.com"
    }

    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = list(filter(lambda x: True if x.startswith("https") else False, map(response.urljoin, all_urls)))
        for url in all_urls:
            match = re.match("(.*/question/(\d+))($|/.*)", url)
            if match:
                question_url = match.group(1)
                question_id = match.group(2)
                yield scrapy.Request(question_url, headers=self.headers, callback=self.parse_question,
                                     meta={"question_id": question_id, "question_url": question_url})
            # else:
            #     yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        question_item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        question_item_loader.add_value("table_name", "zhihu_question")
        question_item_loader.add_value("zhihu_id", int(response.meta.get("question_id")))
        question_item_loader.add_value("url", response.meta.get("question_url"))
        question_item_loader.add_css("topics", ".Tag-content a div div::text")
        question_item_loader.add_css("title", ".QuestionHeader-title::text")
        question_item_loader.add_css("content", ".QuestionHeader-detail")
        question_item_loader.add_css("answer_num", ".List-headerText span::text")
        question_item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        question_item_loader.add_css("click_num", ".QuestionFollowStatus .NumberBoard-item:last-child"
                                                  " .NumberBoard-itemValue::text")
        question_item_loader.add_css("watch_user_num", ".QuestionFollowStatus .NumberBoard-item:first-child"
                                                       " .NumberBoard-itemValue::text")
        question_item_loader.add_value("crawl_time", datetime.now())

        question_item = question_item_loader.load_item()
        yield scrapy.Request(self.start_answer_url.format(response.meta.get("question_id"), 0, 10),
                             headers=self.headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        answer_json = json.loads(response.text)
        is_end = answer_json["paging"]["is_end"]
        next_url = answer_json["paging"]["next"]
        # 解析answer
        for answer in answer_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["table_name"] = "zhihu_answer"
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"]
            answer_item["content"] = answer["content"]
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = datetime.fromtimestamp(answer["created_time"])
            answer_item["update_time"] = datetime.fromtimestamp(answer["updated_time"])
            answer_item["crawl_time"] = datetime.now()

            yield answer_item

        # 还有answer则继续提取
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        cookie_dict = zhihu_login.get_login_cookies()
        return [scrapy.Request(self.start_urls[0], dont_filter=True, headers=self.headers, cookies=cookie_dict)]

    def login_by_selenium(self, response):
        browser = webdriver.Chrome(executable_path="C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
        browser.get("https://www.zhihu.com/signup?next=%2F")
        browser.find_element_by_xpath("//*[@id='root']/div/main/div/div/div/div[2]/div[2]/span").click()
        browser.find_element_by_xpath("//*[@class='SignFlow-account']/div/div/input").send_keys(18650337481)
        browser.find_element_by_xpath("//*[@class='SignFlow-password']/div/div/input").send_keys("knmdmm0.")
        browser.find_element_by_xpath("//*[@class='Button SignFlow-submitButton Button--primary Button--blue']").click()
        time.sleep(5)
        cookies = browser.get_cookies()
        browser.close()
        cookie_dict = dict()
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']

        return [scrapy.Request(self.start_urls[0], dont_filter=True, cookies=cookie_dict)]
