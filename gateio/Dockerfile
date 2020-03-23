FROM linchqd/python:v3.7.5

RUN /bin/cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone

RUN /usr/local/bin/pip3 config set global.index-url http://mirrors.cloud.aliyuncs.com/pypi/simple/ && /usr/local/bin/pip3 config set install.trusted-host mirrors.cloud.aliyuncs.com && /usr/local/bin/pip3 install redis supervisor && ln -s /usr/local/python3/bin/supervisor* /usr/local/bin/

WORKDIR /home/admin/

COPY . /home/admin

RUN chmod +x /home/admin/entrypoint.sh

ENTRYPOINT ["/home/admin/entrypoint.sh"]
