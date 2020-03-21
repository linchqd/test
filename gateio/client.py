#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8


import logging
import sys
import time
import json
import os
from logging.config import dictConfig
from util import GateApi, Redis, compute_order_info

# api info
apiKey = 'E23B5533-1993-488B-B161-64899858EEE3'
secretKey = 'df41f014eeabffde49d2d4b766b9263f42d59bcf0deb8a4fcdd5f8d849af837b'

API_QUERY_URL = 'data.gateio.life'
API_TRADE_URL = 'api.gateio.life'
REDIS_HOST = '192.168.10.20'


# logging setting
# class LogFilter(logging.Filter):
#     def filter(self, record):
#         if record.levelno > 30:
#             return False
#         return True
log_dir = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'logs/')

os.makedirs(log_dir, exist_ok=True)

dictConfig({
    'version': 1,
    'formatters': {
        'access': {
            'format': '%(asctime)s %(levelname)s: %(message)s'
        },
        'error': {
            'format': '%(asctime)s %(levelname)s: %(filename)s:%(module)s:%(funcName)s:%(lineno)d:%(message)s'
        }
    },
    'handlers': {
        'access': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': '{}access.log'.format(log_dir),
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'encoding': 'utf-8',
            'formatter': 'access'
            # 'filters': ['access']
        },
        'error': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'ERROR',
            'filename': '{}error.log'.format(log_dir),
            'when': 'D',
            'interval': 1,
            'backupCount': 7,
            'encoding': 'utf-8',
            'formatter': 'error'
        }
    },
    # 'filters': {
    #     'access': {
    #         '()': LogFilter
    #     }
    # },
    'root': {
        'level': 'INFO',
        'handlers': ['access', 'error']
    }
})

# init obj
gate_query = GateApi(API_QUERY_URL, apiKey, secretKey)
gate_trade = GateApi(API_TRADE_URL, apiKey, secretKey)
redis = Redis(host=REDIS_HOST)

try:
    if not redis.conn.ping():
        logging.error('redis is not connected')
        sys.exit(1)
except Exception as e:
    logging.error('redis is not connected, {}'.format(e))
    sys.exit(1)

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


def buy(price, amounts):
    logging.info('挂买单, 买入价格: {}, 数量: {}'.format(price, amounts))
    try:
        order_buy_number = json.loads(gate_trade.buy(CURRENCY_PAIR, price, amounts))['orderNumber']
        redis.order_buy = order_buy_number
        logging.info('下单成功, 订单号: {}'.format(order_buy_number))
        return True
    except Exception as e:
        logging.error('下单失败,失败原因: {}'.format(str(e.args)))


def sell(price, amounts):
    logging.info('挂卖单, 卖出价格: {}, 数量: {}'.format(price, amounts))
    try:
        order_sell_number = json.loads(gate_trade.sell(CURRENCY_PAIR, price, amounts))['orderNumber']
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
    order_infos = compute_order_info(redis.init_price, redis.number, redis.amount, redis.percent)
    # 下买单
    buy(order_infos['buy_order_price'], order_infos['buy_order_amount'])
    # 下卖单
    sell(order_infos['sell_order_price'], order_infos['sell_order_amount'])


logging.info('程序开始启动.....')

while True:
    try:
        # 判断是不是第一次启动, 是则通过最新成交价进行计算挂单
        if redis.init_price is None:
            init_order()
        else:
            # 判断有没有买单成交
            if redis.order_buy:
                order = json.loads(gate_trade.get_order(redis.order_buy, CURRENCY_PAIR))['order']
                if order['status'] == 'closed':
                    logging.info('买单{}成交'.format(order['orderNumber']))
                    if redis.direction == 'down':
                        # 做空则取消空单, 并flush redis, 根据成交的价格作为init_price价格来计算挂单信息下单
                        if redis.order_sell:
                            gate_trade.cancel_order(redis.order_sell, CURRENCY_PAIR)
                        logging.info('取消空单{}成功'.format(redis.order_sell))
                        redis.conn.flushdb()
                        logging.info('清空redis成功...')
                        init_order(init_price=order['filledRate'])
                    else:
                        # 做多则计算下一个挂单信息
                        order_info = compute_order_info(
                            redis.init_price, redis.number + 1, redis.amount, redis.percent, buy=True)
                        # 下买单
                        if buy(order_info['buy_order_price'], order_info['buy_order_amount']):
                            redis.number += 1
                        redis.direction = 'up'
                        # 下卖单
                        total = redis.buytotal if redis.buytotal is not None else 0
                        if redis.buyfilledamount is None:
                            redis.buytotal = total + order['initialAmount']
                            redis.buyfilledamount = 0
                        elif redis.buyfilledamount > 0:
                            redis.buytotal = total + (order['initialAmount'] - redis.buyfilledamount)
                            redis.buyfilledamount = 0
                        # 查询已有卖单
                        if redis.order_sell:
                            sell_order_tmp = json.loads(gate_trade.get_order(redis.order_sell, CURRENCY_PAIR))['order']
                            # 取消卖单
                            gate_trade.cancel_order(redis.order_sell, CURRENCY_PAIR)
                            logging.info('取消卖单{}成功'.format(redis.order_sell))
                            if sell_order_tmp['filledAmount'] > 0:
                                redis.buytotal = redis.buytotal - sell_order_tmp['filledAmount']
                        sell(order_info['sell_order_price'], redis.buytotal * 0.998)

                elif order['filledAmount'] > 0 and (
                        redis.buyfilledamount is None or order['filledAmount'] != redis.buyfilledamount):
                    if redis.direction != 'down':
                        order_info = compute_order_info(
                            redis.init_price, redis.number + 1, redis.amount, redis.percent, buy=True)
                        if redis.direction is None:
                            redis.direction = 'up'
                            redis.buytotal = order['filledAmount']
                            redis.buyfilledamount = order['filledAmount']
                            sell(order_info['sell_order_price'], redis.buytotal * 0.998)
                        else:
                            redis.buytotal += order['filledAmount'] - redis.buyfilledamount
                            redis.buyfilledamount = order['filledAmount']
                            if redis.order_sell:
                                sell_order_tmp = json.loads(gate_trade.get_order(redis.order_sell, CURRENCY_PAIR))[
                                    'order']
                                gate_trade.cancel_order(redis.order_sell, CURRENCY_PAIR)
                                logging.info('取消卖单{}成功'.format(redis.order_sell))
                                if sell_order_tmp['filledAmount'] > 0:
                                    redis.buytotal = redis.buytotal - sell_order_tmp['filledAmount']
                                sell(sell_order_tmp['initialRate'], redis.buytotal * 0.998)

            # 判断有没有卖单成交
            if redis.order_sell:
                order = json.loads(gate_trade.get_order(redis.order_sell, CURRENCY_PAIR))['order']
                if order['status'] == 'closed':
                    logging.info('卖单{}成交'.format(order['orderNumber']))
                    if redis.direction == 'up':
                        # 做多则取消多单, 并flush redis, 根据成交的价格作为init_price价格来计算挂单信息下单
                        if redis.order_buy:
                            gate_trade.cancel_order(redis.order_buy, CURRENCY_PAIR)
                            logging.info('取消多单{}成功'.format(redis.order_buy))
                        redis.conn.flushdb()
                        logging.info('清空redis成功...')
                        init_order(init_price=order['filledRate'])
                    else:
                        # 做空则计算下一个挂单信息
                        order_info = compute_order_info(
                            redis.init_price, redis.number + 1, redis.amount, redis.percent)
                        # 下卖单
                        if sell(order_info['sell_order_price'], order_info['sell_order_amount']):
                            redis.number += 1
                        redis.direction = 'down'
                        # 下买单
                        total = redis.selltotal if redis.selltotal is not None else 0
                        if redis.sellfilledamount is None:
                            redis.selltotal = total + order['initialAmount']
                            redis.sellfilledamount = 0
                        elif redis.sellfilledamount > 0:
                            redis.selltotal = total + (order['initialAmount'] - redis.sellfilledamount)
                            redis.sellfilledamount = 0
                        # 查询已有买单
                        if redis.order_buy:
                            buy_order_tmp = json.loads(gate_trade.get_order(redis.order_buy, CURRENCY_PAIR))['order']
                            # 取消买单
                            gate_trade.cancel_order(redis.order_buy, CURRENCY_PAIR)
                            logging.info('取消买单{}成功'.format(redis.order_buy))
                            if buy_order_tmp['filledAmount'] > 0:
                                redis.selltotal = redis.selltotal - buy_order_tmp['filledAmount']
                        buy(order_info['buy_order_price'], redis.selltotal * 1.002)

                elif order['filledAmount'] > 0 and (
                        redis.sellfilledamount is None or order['filledAmount'] != redis.sellfilledamount):
                    if redis.direction != 'up':
                        order_info = compute_order_info(
                            redis.init_price, redis.number + 1, redis.amount, redis.percent)
                        if redis.direction is None:
                            redis.direction = 'down'
                            redis.selltotal = order['filledAmount']
                            redis.sellfilledamount = order['filledAmount']
                            buy(order_info['buy_order_price'], redis.selltotal * 1.002)
                        else:
                            redis.selltotal += order['filledAmount'] - redis.sellfilledamount
                            redis.sellfilledamount = order['filledAmount']
                            if redis.order_buy:
                                buy_order_tmp = json.loads(gate_trade.get_order(redis.order_buy, CURRENCY_PAIR))[
                                    'order']
                                gate_trade.cancel_order(redis.order_buy, CURRENCY_PAIR)
                                logging.info('取消买单{}成功'.format(redis.order_buy))
                                if buy_order_tmp['filledAmount'] > 0:
                                    redis.selltotal = redis.selltotal - buy_order_tmp['filledAmount']
                                sell(buy_order_tmp['initialRate'], redis.selltotal * 1.002)
    except Exception as e:
        logging.error('程序发生错误,错误原因: {}'.format(str(e.args)))

    time.sleep(1)
