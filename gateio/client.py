#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

from util import GateApi
from pprint import pprint


apiKey = 'E23B5533-1993-488B-B161-64899858EEE3'
secretKey = 'df41f014eeabffde49d2d4b766b9263f42d59bcf0deb8a4fcdd5f8d849af837b'

API_QUERY_URL = 'data.gateio.life'
API_TRADE_URL = 'api.gateio.life'

gate_query = GateApi(API_QUERY_URL, apiKey, secretKey)
gate_trade = GateApi(API_TRADE_URL, apiKey, secretKey)

# 获取最新成交价格
last_price = gate_query.ticker('ae_usdt')['last']

base_price = 0

current_counts = 0

current_order = {
    'price': 0,
    'amount': 0
}
# 当前的买和卖挂单信息   买和卖的总数量
'''
    A.程序启动 判断是否有没有 衡量价格  
        没有：
            1.通过获取最新成交价或自定义衡量价格
            2.通过衡量价格和网格百分比计算买和卖单的价格和数量
            3.挂买和卖单并记录挂单信息
            4.进入B
        有:
            进入B
    B.每秒钟查询买和卖单的成交状态,判断成交状态,都没成交继续循环：
        买单成交
            全部成交:
                1.计算下一个买单的价格和数量并挂单记录
                2.判断是不是第一次买入
                    是： 进入B循环
                    否： 取消卖单,重新计算卖出价格和数量挂单卖出并记录,进入B循环
            部分成交:
                1.获取成交数量,挂单卖出成交数量并记录
        卖单成交
            全部成交:
            
            部分成交:
    https://blog.csdn.net/linwow/article/details/95227392
'''
pprint(gate_trade.get_order({'orderNumber': 9019936601, 'currencyPair': 'cdt_usdt'}))

# pprint(gate_trade.all_orders({'currencyPair': 'cdt_usdt'}))