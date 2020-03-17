#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

import http.client
import hashlib
import urllib.parse
import hmac
import json
import ssl
import os
import logging
from logging.config import dictConfig

from redis import StrictRedis, ConnectionPool


ssl._create_default_https_context = ssl._create_unverified_context


# logging setting
class LogFilter(logging.Filter):
    def filter(self, record):
        if record.levelno > 30:
            return False
        return True


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
            'formatter': 'access',
            'filters': ['access']
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
    'filters': {
        'access': {
            '()': LogFilter
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['access', 'error']
    }
})


def get_sign(params, secret_key):
    secret_key_bytes = bytes(secret_key, encoding='utf8')

    sign = ''
    for key in params.keys():
        value = str(params[key])
        sign += key + '=' + value + '&'
    sign_bytes = bytes(sign[:-1], encoding='utf8')

    my_sign = hmac.new(secret_key_bytes, sign_bytes, hashlib.sha512).hexdigest()
    return my_sign


def http_get(url, resource, params=''):
    conn = http.client.HTTPSConnection(url, timeout=10)
    conn.request("GET", resource + '/' + params)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    return json.loads(data)


def http_post(url, resource, params, api_key, secret_key):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "KEY": api_key,
        "SIGN": get_sign(params, secret_key)
    }

    conn = http.client.HTTPSConnection(url, timeout=10)

    temp_params = urllib.parse.urlencode(params) if params else ''
    print(temp_params)

    conn.request("POST", resource, temp_params, headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    params.clear()
    conn.close()
    return data


class GateApi(object):
    def __init__(self, url, api_key, secret_key):
        self.__url = url
        self.__apiKey = api_key
        self.__secretKey = secret_key

    # 获取帐号资金余额
    def balances(self):
        url = "/api2/1/private/balances"
        param = {}
        return http_post(self.__url, url, param, self.__apiKey, self.__secretKey)

    # 市场订单参数
    def market_info(self):
        url = "/api2/1/marketinfo"
        params = ''
        return http_get(self.__url, url, params)

    # 所有交易对
    def pairs(self):
        url = "/api2/1/pairs"
        params = ''
        return http_get(self.__url, url, params)

    # 单项交易行情
    def ticker(self, param):
        url = "/api2/1/ticker"
        return http_get(self.__url, url, param)

    # 买入
    def buy(self, currency_pair, rate, amount):
        url = "/api2/1/private/buy"
        params = {'currencyPair': currency_pair, 'rate': rate, 'amount': amount}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 卖出
    def sell(self, currency_pair, rate, amount):
        url = "/api2/1/private/sell"
        params = {'currencyPair': currency_pair, 'rate': rate, 'amount': amount}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 获取我的当前挂单列表
    def all_orders(self, params):
        url = "/api2/1/private/openOrders"
        params = params if params else {}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 获取下单状态
    def get_order(self, params):
        url = "/api2/1/private/getOrder"
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)


class Redis(object):
    def __init__(self, host='127.0.0.1', port=6379, db=0, password=None):
        self.conn = StrictRedis(connection_pool=ConnectionPool(
            host=host, port=port, db=db, password=password, decode_responses=True))

    @property
    def init_price(self):
        return self.conn.get('init_price')

    @init_price.setter
    def init_price(self, value):
        self.conn.set('init_price', value)

    @property
    def number(self):
        return self.conn.get('number')

    @number.setter
    def number(self, value):
        self.conn.set('number', value)

    @property
    def amount(self):
        return self.conn.get('amount')

    @amount.setter
    def amount(self, value):
        self.conn.set('amount', value)

    @property
    def percent(self):
        return self.conn.get('percent')

    @percent.setter
    def percent(self, value):
        self.conn.set('percent', value)

    def flush_all_keys(self):
        for key in self.conn.keys():
            self.conn.delete(key)


def compute_order_info(init_price, number, amount, percent, buy=False):
    if int(number) == 0:
        buy_order_price = '%.4f' % (float(init_price) * (1 - float(percent)))
        buy_order_amount = '%.3f' % (float(amount) * (2 ** int(number)))
        sell_order_price = '%.4f' % (float(init_price) * (1 + float(percent)))
        sell_order_amount = '%.3f' % (float(amount) * (2 ** int(number)))
    elif buy:
        buy_order_price = '%.4f' % (float(init_price) * (1 - (float(percent) * (int(number) + 1))))
        buy_order_amount = '%.3f' % (float(amount) * (2 ** int(number)))
        sell_order_price = '%.4f' % (float(init_price) * (1 - (int(number) - 1) * float(percent)))
        sell_order_amount = '%.3f' % (float(buy_order_amount * 0.998))
    else:
        sell_order_price = '%.4f' % (float(init_price) * (1 + (float(percent) * (int(number) + 1))))
        sell_order_amount = '%.3f' % (float(amount) * (2 ** int(number)))
        buy_order_price = '%.4f' % (float(init_price) * (1 + (int(number) - 1) * float(percent)))
        buy_order_amount = '%.3f' % (sell_order_amount * 1.002)

    return {
        'buy_order_price': buy_order_price,
        'buy_order_amount': buy_order_amount,
        'sell_order_price': sell_order_price,
        'sell_order_amount': sell_order_amount
    }
