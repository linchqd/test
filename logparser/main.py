#!/usr/bin/env python2
# _*_ coding: utf-8 _*_

import os
import sys
import logging
import argparse
import crayons
import datetime
import subprocess

logging.basicConfig(level=logging.DEBUG,  format="%(asctime)s %(levelname)s:%(module)s:%(funcName)s:%(message)s")


class LogAnalyse(object):
    def __init__(self, directory, filename, days):
        self.log_path = directory
        self.log_filename = filename
        self.file_list = self.list_date(days)
        self.result = {}

    def list_date(self, days):
        day_list = {}
        today = datetime.datetime.today()
        if days > 1:
            d = days - 1
            while d > 0:
                temp = '{}.{}'.format(self.log_filename, (today - datetime.timedelta(days=d)).strftime('%Y-%m-%d'))
                day_list[temp] = []
                d -= 1
        day_list['{}.{}'.format(self.log_filename, today.strftime('%Y-%m-%d'))] = []
        return self.list_file(day_list)

    def list_file(self, day_list):
        if not os.path.exists(self.log_path):
            logging.error(crayons.red("log path is don't exists"))
            sys.exit(0)
        for filename in os.listdir(self.log_path):
            for pre in day_list.keys():
                if filename.startswith(pre):
                    day_list[pre].append('{}'.format(os.path.join(self.log_path, filename)))
        return day_list

    def analyse(self):
        self.result['total'] = 0
        self.result['ex_total'] = 0
        for pre, files in self.file_list.items():
            self.result[pre] = {}
            self._analyse(pre, files)
            print(crayons.green('{} 异常api统计信息: 异常总数: {}'.format(pre, self.result[pre]['exception_api_total'])))
            self.result['ex_total'] += self.result[pre]['exception_api_total']
            for k, v in self.result[pre]['exception_api'].items():
                print(crayons.red("\t{}: {}, api: {}".format(k, v['total'], list(v['api']))))
        temp = ''
        for p in self.file_list.keys():
            temp += '{}* '.format(os.path.join(self.log_path, p))
        api_speed = subprocess.Popen(
            'sort -t, -nk5 {} | tail -1'.format(temp),
            shell=True, stdout=subprocess.PIPE).communicate()[0]
        print(crayons.green("api调用总数: {}, 异常api总数: {}, api调用成功率: {}, api耗时: {}".format(
            self.result['total'], self.result['ex_total'],
            round((self.result['total'] - self.result['ex_total'])/float(self.result['total']), 4),
            api_speed.split(',')[4])))

    def _analyse(self, pre, files):
        self.result[pre]['exception_api_total'] = 0
        self.result[pre]['exception_api'] = {}
        for fn in files:
            with open(fn) as f:
                line = f.readline().split(',')
                while len(line) > 1:
                    if line[9] != '1000':
                        if line[9] not in self.result[pre]['exception_api']:
                            self.result[pre]['exception_api'][line[9]] = {}
                            self.result[pre]['exception_api'][line[9]]['api'] = set()
                            self.result[pre]['exception_api'][line[9]]['total'] = 0
                        self.result[pre]['exception_api'][line[9]]['api'].add(line[5])
                        self.result[pre]['exception_api'][line[9]]['total'] += 1
                        self.result[pre]['exception_api_total'] += 1
                    self.result['total'] += 1
                    line = f.readline().split(',')


def main():
    parse = argparse.ArgumentParser(description='Log Analyse Tool')
    parse.add_argument('--version', action='version', version='v1.0.20200221')
    parse.add_argument('--days', help='special date, default 1', type=int, choices=[1,2,3,4,5,6,7], default=1)
    parse.add_argument('--directory', help='log path', type=str, default='/home/test/logs')
    parse.add_argument('--filename', help='log filename prefix', type=str, default='gateway-page-digest.log')
    args = parse.parse_args()
    LogAnalyse(**vars(args)).analyse()


if __name__ == '__main__':
    main()
