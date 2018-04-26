#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : zhihu_login.py
# @Author: lxy
# @Date  : 2017/12/8
# @Desc  :
import json
import re
import time
import hmac
from hashlib import sha1

from parsel import Selector
import requests
from http.cookiejar import LWPCookieJar

headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'zh-CN,zh;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome'
                  '/63.0.3239.132 Safari/537.36',
    'referer': 'https://www.zhihu.com',
}


def get_signal(time_stamp, client_id):
    """
    传入一个时间戳
    :param client_id:
    :param time_stamp:
    :return: signature
    """
    a = hmac.new("d1b964811afb40118a12068ff74a12f4".encode('utf8'), digestmod=sha1)  # HMAC key
    a.update("password".encode('utf8'))  # 固定字符串
    a.update(client_id.encode('utf8'))
    a.update("com.zhihu.web".encode('utf8'))  # 固定字符串
    a.update(str(time_stamp).encode('utf8'))
    return a.hexdigest()


def check_login(session):
    inbox_url = "https://www.zhihu.com/inbox"
    response = session.get(inbox_url, headers=headers, allow_redirects=False)
    return response.status_code == 200


def get_login_cookies():
    s = requests.session()
    s.cookies = LWPCookieJar(filename=r"C:\Users\Administrator\PycharmProjects\ArticleSpider\cookie.txt")
    s.cookies.load(ignore_discard=True, ignore_expires=True)
    if not check_login(s):
        s.cookies = None
        # 获取 x-UDID
        selector = Selector(s.get("https://www.zhihu.com/signup?next=%2F", headers=headers).text)
        jsdata = json.loads(selector.css('div#data::attr(data-state)').extract_first())
        headers['X-UDID'] = jsdata['token']['xUDID']

        # 获取 oauth
        js = s.get('https://static.zhihu.com/heifetz/main.app.55320feac869a92d02d5.js',
                   headers=headers).content.decode("utf8")
        time_stamp = int(time.time() * 1000)
        oauth = re.search('authorization:"oauth (.*?)"}', js).group(1)
        headers['authorization'] = 'oauth ' + oauth

        # 验证码请求及form表单
        s.get("https://www.zhihu.com/api/v3/oauth/captcha?lang=cn", headers=headers)
        files = {
            'client_id': (None, oauth),
            'grant_type': (None, 'password'),
            'timestamp': (None, str(time_stamp)),
            'source': (None, 'com.zhihu.web'),
            'signature': (None, get_signal(time_stamp, oauth)),
            'username': (None, '18650337481'),
            'password': (None, 'knmdmm0.'),
            'captcha': (None, ''),
            'lang': (None, 'cn'),
            'ref_source': (None, 'homepage'),
            'utm_source': (None, ''),
        }
        s.post("https://www.zhihu.com/api/v3/oauth/sign_in", files=files, headers=headers)
        s.cookies.save()
    return requests.utils.dict_from_cookiejar(s.cookies)
