#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
# vue + xtermjs: https://blog.csdn.net/qq_31126175/article/details/84346305

import paramiko
import pprint


class SSH(object):
    def __init__(self, host, username, auth_type=1, port=22, password=None, pkey=None):
        self.host = host
        self.username = username
        self.port = port
        self.password = password
        self.auth_type = auth_type
        self.pkey = pkey
        self._transport = None
        self.ssh = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.auth_type == 1:
                self.ssh.connect(self.host, self.port, self.username, self.password, timeout=8)
            else:
                self.ssh.connect(self.host, self.port, self.username, self.pkey, timeout=8)
        except Exception as e:
            return e
        self._transport = self.ssh.get_transport()

    def close(self):
        self._transport.close()

    def exec_command(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        pprint.pprint(stdout.readlines())

    # def upload(self, local_path, target_path):
    #     # 连接，上传
    #     sftp = paramiko.SFTPClient.from_transport(self._transport)
    #     # 将location.py 上传至服务器 /tmp/test.py
    #     sftp.put(local_path, target_path, confirm=True)
    #     # print(os.stat(local_path).st_mode)
    #     # 增加权限
    #     # sftp.chmod(target_path, os.stat(local_path).st_mode)
    #     sftp.chmod(target_path, 0o755)  # 注意这里的权限是八进制的，八进制需要使用0o作为前缀
    #
    # def download(self, target_path, local_path):
    #     # 连接，下载
    #     sftp = paramiko.SFTPClient.from_transport(self._transport)
    #     # 将location.py 下载至服务器 /tmp/test.py
    #     sftp.get(target_path, local_path)


ssh = SSH(host='127.0.0.1', username='test', password='root')
ssh.connect()
ssh.exec_command('ifconfig')