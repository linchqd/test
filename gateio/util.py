#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

import http.client
import hashlib
import urllib.parse
import hmac
import json


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

    # 所有交易对
    def pairs(self):
        url = "/api2/1/pairs"
        params = ''
        return http_get(self.__url, url, params)

    # 单项交易行情
    def ticker(self, param):
        url = "/api2/1/ticker"
        return http_get(self.__url, url, param)

    # 获取我的当前挂单列表
    def all_orders(self, params):
        url = "/api2/1/private/openOrders"
        params = params if params else {}
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)

    # 获取下单状态
    def get_order(self, params):
        url = "/api2/1/private/getOrder"
        return http_post(self.__url, url, params, self.__apiKey, self.__secretKey)