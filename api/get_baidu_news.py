# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 19:21:59 2018

@author: helf
"""


import urllib.request
import re
import numpy as np
import pandas as pd
import time


def get_news_num(keywords=None, begin_date=None, end_date=None):
    '''
    获取百度新闻数量
    '''

    begin_date_format = begin_date.replace("-", "").replace("/", "").replace(".", "")
    begin_datetime = begin_date_format + " 00:00:00"
    begin_date_struct = time.strptime(begin_datetime, "%Y%m%d %H:%M:%S")
    begin_date_stamp = int(time.mktime(begin_date_struct))
    y0 = begin_date_struct.tm_year
    m0 = begin_date_struct.tm_mon
    d0 = begin_date_struct.tm_mday

    end_date_format = end_date.replace("-", "").replace("/", "").replace(".", "")    
    end_datetime = end_date_format + " 23:59:59"
    end_date_struct = time.strptime(end_datetime, "%Y%m%d %H:%M:%S")
    end_date_stamp = int(time.mktime(end_date_struct))
    y1 = end_date_struct.tm_year
    m1 = end_date_struct.tm_mon
    d1 = end_date_struct.tm_mday
    
    data = {"cl" :2,                        # 默认2
            "bt": begin_date_stamp,         # 开始时间戳，从 00:00:00 开始
            "y0": y0,           
            "m0": m0,
            "d0": d0,
            "y1": y1,
            "m1": m1,
            "d1": d1,
            "et":end_date_stamp,            # 结束时间戳，到 23:59:59 结束
            "q1":keywords,                  # 关键词，包含以下全部的关键词对应的输入字符
            "submit":"百度一下",
            "q3":"",                        # 包含以下任意一个关键词
            "q4":"",                        # 不包含以下关键词
            "mt":0,
            "lm":"",
            "s":2,
            "begin_date": begin_date,   # 开始日期
            "end_date": end_date,       # 结束日期
            "tn": "newsdy",             # newsdy:在新闻全文中，newstitledy:仅在新闻的标题中
            "ct1": 1,                   # 1： 按焦点排序； 0：按时间排序
            "ct": 0,                    # =1-ct1
            "rn": 100,                  # 每页显示条数 10/20/50/100
            "q6": ""}                   # 空值

    
    params = urllib.parse.urlencode(data)
    url = "http://news.baidu.com/ns?from=news&" + params
    # print(url)
    
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
    headers = {'User-Agent' : user_agent}
    request = urllib.request.Request(url=url, headers=headers, method="GET")  
    response = urllib.request.urlopen(request)
    data = response.read().decode("utf-8")

    pattern = re.compile(r"找到相关新闻.*?篇", re.S)
    item_list = pattern.findall(data)
    
    if len(item_list) > 0:
        result = item_list[0].replace("约", "").replace(",", "")
        num = int(result[6:-1])
    else:
        num = 0
        
    return num


if __name__ == "__main__":
    
    keywords = "两会+中兴通讯"
    begin_date = "2016-03-03"
    end_date = "2016-03-16"
    
    news_num = get_news_num(keywords, begin_date, end_date)
    print(news_num)
    
    
    