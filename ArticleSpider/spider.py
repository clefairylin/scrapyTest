import requests

from ArticleSpider.utils import zhihu_login


class Spider(object):
    def __init__(self):
        self.headers = {
            "Host": "www.zhihu.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
                          "/63.0.3239.84 Safari/537.36",
            "Referer": "https://www.zhihu.com"
        }
        self.cookie_dict = zhihu_login.get_login_cookies()  # 模拟登陆知乎
        self.start_url = "http://www.zhihu.com/"
        self.filter_set = (self.start_url,)

    def start_spider(self):
        response = requests.get(self.start_url, headers=self.headers, cookie_dict=self.cookie_dict)
        self.parse(response)

    def parse(self, response):
        # 数据解析入库, url提取去重等
        pass

        for url in ["more_urls"]:
            response = requests.get(url, headers=self.headers, cookie_dict=self.cookie_dict)
            self.parse(response)


if __name__ == '__main__':
    Spider().start_spider()


