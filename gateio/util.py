#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

import http.client
import hashlib
import urllib.parse
import hmac
import json
import ssl

from redis import StrictRedis, ConnectionPool


ssl._create_default_https_context = ssl._create_unverified_context


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
    def get_order(self, order_number, currency_pair):
        url = "/api2/1/private/getOrder"
        params = {'orderNumber': order_number, 'currencyPair': currency_pair}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 取消订单
    def cancel_order(self, order_number, currency_pair):
        url = "/api2/1/private/cancelOrder"
        params = {'orderNumber': order_number, 'currencyPair': currency_pair}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 取消所有订单
    def cancel_all_orders(self, trade_type, currency_pair):
        url = "/api2/1/private/cancelAllOrders"
        params = {'type': trade_type, 'currencyPair': currency_pair}
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

    @property
    def order_buy(self):
        return self.conn.get('order_buy')

    @order_buy.setter
    def order_buy(self, value):
        self.conn.set('order_buy', value)

    @property
    def order_sell(self):
        return self.conn.get('order_sell')

    @order_sell.setter
    def order_sell(self, value):
        self.conn.set('order_sell', value)

    @property
    def direction(self):
        return self.conn.get('direction')

    @direction.setter
    def direction(self, value):
        self.conn.set('direction', value)

    @property
    def buytotal(self):
        return self.conn.get('buytotal')

    @buytotal.setter
    def buytotal(self, value):
        self.conn.set('buytotal', value)

    @property
    def buyfilledamount(self):
        return self.conn.get('buyfilledamount')

    @buyfilledamount.setter
    def buyfilledamount(self, value):
        self.conn.set('buyfilledamount', value)

    @property
    def selltotal(self):
        return self.conn.get('selltotal')

    @selltotal.setter
    def selltotal(self, value):
        self.conn.set('selltotal', value)

    @property
    def sellfilledamount(self):
        return self.conn.get('sellfilledamount')

    @sellfilledamount.setter
    def sellfilledamount(self, value):
        self.conn.set('sellfilledamount', value)


def compute_order_info(init_price, number, amount, percent, buy=False):
    if 4 <= int(number) <= 5:
        percent = 0.03
    elif int(number) >= 6:
        percent = 0.05

    if int(number) == 0:
        buy_order_price = '%.4f' % (float(init_price) * (1 - float(percent)))
        buy_order_amount = '%.2f' % (float(amount) * (2 ** int(number)))
        sell_order_price = '%.4f' % (float(init_price) * (1 + float(percent)))
        sell_order_amount = '%.2f' % (float(amount) * (2 ** int(number)))
    elif buy:
        buy_order_price = '%.4f' % (float(init_price) * (1 - (float(percent) * (int(number) + 1))))
        buy_order_amount = '%.2f' % (float(amount) * (2 ** int(number)))
        sell_order_price = '%.4f' % (float(init_price) * (1 - (int(number) - 1) * float(percent)))
        sell_order_amount = '%.2f' % (float(buy_order_amount) * 0.998)
    else:
        sell_order_price = '%.4f' % (float(init_price) * (1 + (float(percent) * (int(number) + 1))))
        sell_order_amount = '%.2f' % (float(amount) * (2 ** int(number)))
        buy_order_price = '%.4f' % (float(init_price) * (1 + (int(number) - 1) * float(percent)))
        buy_order_amount = '%.2f' % (float(sell_order_amount) * 1.002)

    return {
        'buy_order_price': buy_order_price,
        'buy_order_amount': buy_order_amount,
        'sell_order_price': sell_order_price,
        'sell_order_amount': sell_order_amount
    }
