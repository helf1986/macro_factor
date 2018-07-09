
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 16 10:11:12 2018

@author: helf
"""


import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
myfont = mpl.font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttf')
mpl.rcParams['axes.unicode_minus'] = False

from WindPy import w
w.start()

from api.get_baidu_news import get_news_num


conf_date = pd.read_csv('two_conference_date.csv', encoding='gbk')
conf_date.index = conf_date['年份']
conf_date['开始日期'] = [str(conf_date.loc[each, '年份']) + '/' + conf_date.loc[each, '开始日期'] for each in conf_date.index] 
conf_date['结束日期'] = [str(conf_date.loc[each, '年份']) + '/' + conf_date.loc[each, '结束日期'] for each in conf_date.index] 


conf_date['begin'] = [time.strftime('%Y-%m-%d',time.strptime(each, '%Y/%m/%d')) for each in conf_date['开始日期']]
conf_date['end'] = [time.strftime('%Y-%m-%d',time.strptime(each, '%Y/%m/%d')) for each in conf_date['结束日期']]

benchmark_code = '000300.SH'

netvalue_real = pd.DataFrame([], columns=conf_date.index[7:])
netvalue_excess = pd.DataFrame([], columns=conf_date.index[7:])


factor = 'news_num'

for each_year in conf_date.index[-5:-4]:
    
    print(each_year)
    
    # 处理主要观察日期
    begin_date = conf_date.loc[each_year, 'begin']
    end_date = conf_date.loc[each_year, 'end']
    
    wdata = w.tdaysoffset(-60, begin_date, "")
    begin_date_b60 = wdata.Data[0][0].strftime('%Y-%m-%d')
    wdata = w.tdaysoffset(-1, begin_date, "")
    begin_date_b1 = wdata.Data[0][0].strftime('%Y-%m-%d')    
    wdata = w.tdaysoffset(5, end_date, "")
    end_date_a5 = wdata.Data[0][0].strftime('%Y-%m-%d')
    wdata = w.tdaysoffset(120, end_date, "")
    end_date_a120 = wdata.Data[0][0].strftime('%Y-%m-%d')
    wdata = w.tdaysoffset(240, end_date, "")
    end_date_a240 = wdata.Data[0][0].strftime('%Y-%m-%d')
    
    
    # 中证800成分股
    index_code = "000300.SH"
    wdata = w.wset("sectorconstituent","date=" + begin_date+ ";windcode=" + index_code)
    stk_pool = pd.DataFrame(wdata.Data[1:], index=['code', 'name'], columns=wdata.Codes).T
    stk_pool.index = stk_pool['code']
    stk_pool = stk_pool.drop(['code'],axis=1)
    stock_codes = list(stk_pool.index)

    
    # 获取所有股票因子值，会议召开前60个交易日，和会议召开后5个交易日内
    stk_pool_data = stk_pool.copy()
    stk_pool_data['news_num_before'] = 0
    stk_pool_data['news_num_between'] = 0
    stk_pool_data['news_num_ratio'] = 0
    stk_pool_data['mtm'] = 0
    
    # 算法二：会议召开期间和“两会”相关的新闻数
    count = 0
    for nn in range(len(stock_codes)):
        each_code = stock_codes[nn]
        each_company = stk_pool.loc[each_code, 'name'].replace("(退市)", "")
        stk_pool_data.loc[each_code, 'news_num_before'] = get_news_num(each_company, begin_date_b60, begin_date_b1)
        stk_pool_data.loc[each_code, 'news_num_between'] = get_news_num("两会+" + each_company, begin_date, end_date_a5)
        print(each_code, each_company, stk_pool_data.loc[each_code, 'news_num_before'], stk_pool_data.loc[each_code, 'news_num_between'])
        
        count += 1
        if (count%11 == 0):
            time.sleep(5)
    
    stk_pool_data['news_num_ratio'] = stk_pool_data['news_num_between']/stk_pool_data['news_num_before']
    # 观察会议召开前60个交易日和会议召开后240个交易的收盘价走势
    wdata = w.wsd(stock_codes, 'close', begin_date_b60, end_date_a240, "PriceAdj=F")
    stock_close = pd.DataFrame(wdata.Data, index=wdata.Codes, columns=wdata.Times).T
    stock_close.index = [each.strftime('%Y-%m-%d') for each in stock_close.index]
    stock_close.fillna(method='pad')

        
    # 计算从两会开始到结束5日内的动量
    stock_data_tmp = stock_close[stock_close.index>=begin_date]
    stock_data_tmp = stock_data_tmp[stock_data_tmp.index<=end_date_a5]
    stock_data_tmp = stock_data_tmp.apply(lambda x:x.iloc[-1]/x.iloc[0]-1)
    stk_pool_data['mtm'] = stock_data_tmp
    
    stk_pool_data.to_csv("data/factor_LimitNewsAndMtm_"+str(each_year)+".csv")


    stk_pool_filter = stk_pool_data[(stk_pool_data['news_num_between']>=10) & (stk_pool_data['mtm']>0.015)]
    stk_pool_sorted = stk_pool_filter.sort_values(by='mtm', ascending=False)
    num_stk = len(stk_pool_data) 
    stk_selected = stk_pool_sorted.iloc[0:int(num_stk/10)]
    stk_selected_codes = list(stk_selected.index)
    

    # 计算持仓股票平均净值,以会议召开日后的第一个交易日为1.0
    wdata = w.tdaysoffset(1, begin_date, "")
    begin_date_a1 = wdata.Data[0][0].strftime('%Y-%m-%d')
    stock_netvalue = stock_close.apply(lambda x: x/x.loc[begin_date_a1])
    stock_netvalue_mean = stock_netvalue.mean(1)
    
    # 计算业绩基准的净值走势
    wdata = w.wsd(benchmark_code, 'close', begin_date_b60, end_date_a240, "PriceAdj=F")
    bm_close = pd.DataFrame(wdata.Data, index=wdata.Codes, columns=wdata.Times).T
    bm_close.index = [each.strftime('%Y-%m-%d') for each in bm_close.index]
    bm_netvalue = bm_close/bm_close.loc[begin_date_a1]

    # 计算业绩基准的净值走势
    benchmark_code2 = '000905.SH'
    wdata = w.wsd(benchmark_code2, 'close', begin_date_b60, end_date_a240, "PriceAdj=F")
    bm2_close = pd.DataFrame(wdata.Data, index=wdata.Codes, columns=wdata.Times).T
    bm2_close.index = [each.strftime('%Y-%m-%d') for each in bm2_close.index]
    bm2_netvalue = bm2_close/bm2_close.loc[begin_date_a1]

    
    # 把策略和基准放在一起比较
    netvalue = pd.DataFrame([], columns=[each_year, '沪深300', '中证500'])
    netvalue[each_year] = stock_netvalue_mean.copy()
    netvalue['沪深300'] = bm_netvalue.copy()
    netvalue['中证500'] = bm2_netvalue.copy()
        
    fig = plt.figure()
    netvalue.plot(figsize=(12,6))
    plt.legend([each_year, '沪深300', '中证500'], prop=myfont, loc='upper left')
    plt.grid(True)
    plt.ylabel('净值', fontproperties=myfont)
    plt.xlabel('日期', fontproperties=myfont)
    plt.xticks(rotation=90)
    # plt.gcf().autofmt_xdate()
    fig.tight_layout()
    plt.savefig("data/" + index_code.replace('.', '') + "_factor_" + factor + "_" + str(each_year) + ".png")

    
    netvalue_1 = netvalue[each_year].copy()
    netvalue_1.index = range(-61,len(netvalue_1)-61)
    netvalue_real[each_year] = netvalue_1.copy()
    
    netvalue_2 = netvalue[each_year]/netvalue['沪深300']
    netvalue_2.index = range(-61,len(netvalue_2)-61)
    netvalue_excess[each_year] = netvalue_2.copy()

    
    
netvalue_mean = pd.DataFrame([], columns = ['real', 'exess'])
netvalue_mean['real'] = netvalue_real.mean(1)
netvalue_mean['exess'] = netvalue_excess.mean(1)  
netvalue_mean.plot(grid=True)
