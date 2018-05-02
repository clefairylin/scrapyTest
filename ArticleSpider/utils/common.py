#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : common.py
# @Author: lxy
# @Date  : 2017/12/4
# @Desc  :
import datetime
import hashlib
import re


def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    md5 = hashlib.md5()
    md5.update(url)
    return md5.hexdigest()


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception:
        create_date = datetime.datetime.now().date()
    return create_date


def get_number_value(value):
    number_match = re.match(".*?([\d,]+).*", value)
    if number_match:
        number = number_match.group(1)
        number = int(number.replace(",", ""))
    else:
        number = 0
    return number


def remove_splash(value):
    return value.replace("/", "")


def get_string_between(source: str, start, end=None):
    start_index = source.find(start)
    if start_index >= 0:
        if end is None:
            return source[start_index:]
        else:
            end_index = source.find(end, start_index)
            if end_index > 0:
                return source[start_index + len(start):end_index]
            else:
                return None
    else:
        return None

