#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8


import logging
from util import GateApi, Redis, compute_order_info
import sys
import time
import json
from pprint import pprint

# api info
apiKey = 'E23B5533-1993-488B-B161-64899858EEE3'
secretKey = 'df41f014eeabffde49d2d4b766b9263f42d59bcf0deb8a4fcdd5f8d849af837b'

API_QUERY_URL = 'data.gateio.life'
API_TRADE_URL = 'api.gateio.life'
REDIS_HOST = '127.0.0.1'


# init obj
gate_query = GateApi(API_QUERY_URL, apiKey, secretKey)
gate_trade = GateApi(API_TRADE_URL, apiKey, secretKey)
redis = Redis(host=REDIS_HOST)

# set run var
AMOUNT = 100
PERCENT = 0.05
COINS = 'AE'
CURRENCY_PAIR = 'ae_usdt'


def get_balances():
    res = json.loads(gate_trade.balances())
    if res['result'] == 'true':
        usdt = res['available']['USDT']
        coin = res['available'][COINS]
        return {'usdt': usdt, 'coin': coin}


def buy(price, amount):
    logging.info('挂买单, 买入价格: {}, 数量: {}'.format(order_info['buy_order_price'], order_info['buy_order_amount']))
    try:
        order_buy_number = json.loads(gate_trade.buy(
            CURRENCY_PAIR, order_info['buy_order_price'], order_info['buy_order_amount']))['orderNumber']
        redis.order_buy = order_buy_number
        logging.info('下单成功, 订单号: {}'.format(order_buy_number))
        return True
    except Exception as e:
        logging.error('下单失败,失败原因: {}'.format(str(e.args)))


def sell(price, amount):
    logging.info('挂卖单, 卖出价格: {}, 数量: {}'.format(order_info['sell_order_price'], order_info['sell_order_amount']))
    try:
        order_sell_number = json.loads(gate_trade.sell(
            CURRENCY_PAIR, order_info['sell_order_price'], order_info['sell_order_amount']))['orderNumber']
        redis.order_sell = order_sell_number
        logging.info('下单成功, 订单号: {}'.format(order_sell_number))
        return True
    except Exception as e:
        logging.error('下单失败,失败原因: {}'.format(str(e.args)))


def init_order(init_price=None):
    if init_price is None:
        # 获取最新成交价格
        redis.init_price = gate_query.ticker(CURRENCY_PAIR)['last']
        logging.info('程序init启动,获取init price为最新成交价: {}'.format(redis.init_price))
    else:
        redis.init_price = init_price
        logging.info('程序init启动,init price为最新成交价: {}'.format(init_price))

    redis.number = 0
    redis.amount = AMOUNT
    redis.percent = PERCENT
    order_info = compute_order_info(redis.init_price, redis.number, redis.amount, redis.percent)
    # 下买单
    buy(order_info['buy_order_price'], order_info['buy_order_amount'])
    # 下卖单
    sell(order_info['sell_order_price'], order_info['sell_order_amount'])


logging.info('程序开始启动.....')

while True:
    try:
        # 判断是不是第一次启动, 是则通过最新成交价进行计算挂单
        if redis.init_price is None:
            init_order()
        else:
            # 判断有没有买单
            if redis.order_buy:
                order = json.loads(gate_trade.get_order(redis.order_buy, CURRENCY_PAIR))['order']
                if order['status'] == 'closed':
                    logging.info('买单{}成交'.format(order['orderNumber']))
                    if redis.direction == 'down':
                        # 做空则取消空单, 并flush redis, 根据成交的价格作为init_price价格来计算挂单信息下单
                        gate_trade.cancel_order(redis.order_sell, CURRENCY_PAIR)
                        logging.info('取消空单{}成功'.format(redis.order_sell))
                        redis.conn.flushdb()
                        logging.info('清空redis成功...')
                        init_order(init_price=order['filledRate'])
                    else:
                        # 做多则计算下一个挂单信息
                        order_info = compute_order_info(redis.init_price, redis.number + 1, redis.amount, redis.percent)
                        # 下买单
                        if buy(order_info['buy_order_price'], order_info['buy_order_amount']):
                            redis.number += 1
                            redis.direction = 'up'
                        # 下卖单
                        total = redis.buytotal if redis.buytotal is not None else 0
                        if redis.buyfilledamount is None:
                            redis.buytotal = total + order['initialRate']
                            redis.buyfilledamount = 0
                        elif redis.buyfilledamount > 0:
                            redis.buytotal = total + (order['initialRate'] - redis.buyfilledamount)
                            redis.buyfilledamount = 0
                        sell_order_tmp = json.loads(gate_trade.get_order(redis.order_sell, CURRENCY_PAIR))['order']
                        if sell_order_tmp['filledAmount'] > 0:
                            pass
                        sell(order_info['sell_order_price'], redis.buytotal)

                elif order['filledAmount'] > 0 and (redis.buyfilledamount is None or order['filledAmount'] != redis.buyfilledamount):
                    total = redis.buytotal if redis.buytotal is not None else 0
                    filled_record = redis.buyfilledamount if redis.buyfilledamount is not None else 0
                    total += order['filledAmount'] - filled_record
                    redis.buytotal = total
                    redis.buyfilledamount = order['filledAmount']
            else:
                # 没有多单则挂上
                order_info = compute_order_info(redis.init_price, redis.number, redis.amount, redis.percent)
                amount = redis.selltotal if redis.selltotal is not None else order_info['buy_order_amount']
                buy(order_info['buy_order_price'], amount)
                # 取消空单 重新挂
                    # 做多则计算下一个挂单信息
            # 如果订单成交,判断当前是做多还是做空
            #cancelled
            #     # 做多则计算下一个挂单信息
            #  filledAmount
            #     # 做空则取消多单, 并情况redis, 根据成交的价格作为init_price价格来计算挂单信息
            # if status == 'open':
            #     print(status)
        time.sleep(1)
    except Exception as e:
        logging.error('程序发生错误,错误原因: {}'.format(str(e.args)))
        logging.error('程序退出')
        sys.exit(1)

# redis.conn.hmset('current_order', current_order)
# print(redis.conn.hmget('current_order', ['price', 'amount'])[0].decode('utf-8'))
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
# pprint(gate_trade.get_order({'orderNumber': 9019936601, 'currencyPair': 'cdt_usdt'}))

# pprint(gate_trade.cancel_order(redis.order_buy, CURRENCY_PAIR))
# pprint(gate_trade.cancel_all_orders('buy', CURRENCY_PAIR))
# print(json.loads(gate_trade.get_order(redis.order_buy, CURRENCY_PAIR))['order']['status'])
