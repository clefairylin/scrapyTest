#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : main.py
# @Author: lxy
# @Date  : 2017/11/22
# @Desc  :

import sys
import os

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# execute(['scrapy', 'crawl', 'jobbole'])
# execute(['scrapy', 'crawl', 'zhihu'])
execute(['scrapy', 'crawl', 'productKeyword'])
