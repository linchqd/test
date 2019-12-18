# ansible docs
### http://www.zsythink.net/
### https://github.com/ansible/ansible-examples/
## install
```
pip3 install ansible
ln -s /usr/local/python3/bin/* /usr/local/bin/
ansible --version
```
## config file
```
mkdir /etc/ansible
wget https://raw.githubusercontent.com/ansible/ansible/devel/examples/ansible.cfg -O /etc/ansible/ansible.cfg
```
## inventory default: /etc/ansible/hosts
```
vim /etc/ansible/hosts

all:
  hosts:
    192.168.10.20:
    www[01:50].example.com:
    db-[a:f].example.com:
    jumper:   # 别名
      ansible_connect: smart
      ansible_host: ip
      ansible_port: 22
      ansible_user: silence
      ansible_become_user: root
      ansible_python_interpreter: "/bin/env python2.6"
  children:
    webservers:
      hosts:
        192.168.10.30:
        test.linchqd.com:
    dbservers:
      hosts:
        192.168.10.40:
    prd:
      children:
        dbservers:
      vars:  # prd组变量
        some_server: foo.southeast.example.com
        halon_system_timeout: 30
  vars:   # 全局变量
    ntp_server: ntp.atlanta.example.com
    proxy: proxy.atlanta.example.com
    
变量还可以写到文件中,有效的文件扩展名包括'.yml','.yaml','.json'或没有文件扩展名:
/etc/ansible/host_vars/foosball   # 主机foosball的变量
/etc/ansible/group_vars/raleigh   # 组raleigh的变量

您还可以创建以组或主机命名的目录。Ansible将按字典顺序读取这些目录中的所有文件。“ raleigh”组的示例:
/etc/ansible/group_vars/raleigh/db_settings
/etc/ansible/group_vars/raleigh/cluster_settings
组中的所有主机都将具有在这些文件中定义的变量

变量 顺序/优先顺序是（从最低到最高）：

所有组（因为它是所有其他组的“父母”）
父组
子组
主办
默认情况下，Ansible按字母顺序合并处于相同父/子级别的组，最后加载的组将覆盖先前的组。例如，a_group将与b_group合并，并且匹配的b_group变量将覆盖a_group中的变量。

您可以通过设置组变量ansible_group_priority来更改同一级别的组的合并顺序（在解决父/子顺序之后）来更改此行为。数字越大，合并的时间越晚，优先级更高

```
## 匹配
```
ansible <pattern> -m <module_name> -a "<module options>"

ex:
    ansible webservers -m service -a "name=httpd state=restarted"
all             匹配所有
host1           匹配host1
host1:host2     匹配host1和host2
group1          匹配组group1
group1:group2   匹配组group1和group2
group1:!group2  匹配在组group1中但是不在group2中的主机
group1:&group2  匹配在组group1中而且在group2中的主机
正则匹配
192.0.*
*.example.com
*.com

您可以根据主机在主机中的位置来定义主机或主机的子集。例如，给定以下组：

[webservers]
cobweb
webbing
weber
您可以使用下标在webservers组中选择单个主机或范围：

webservers[0]       # == cobweb
webservers[-1]      # == weber
webservers[0:2]     # == webservers[0],webservers[1]
                    # == cobweb,webbing
webservers[1:]      # == webbing,weber
webservers[:3]      # == cobweb,webbing,weber
```
## 执行命令  ansible [pattern] -m [module] -a "[module options]"
```

ansible raleigh -m shell -a 'echo $TERM'
ansible atlanta -m copy -a "src=/etc/hosts dest=/tmp/hosts"
ansible webservers -m file -a "dest=/srv/foo/b.txt mode=600 owner=mdehaan group=mdehaan"
该file模块还可以创建目录，类似于：mkdir -p
ansible webservers -m file -a "dest=/path/to/c mode=755 owner=mdehaan group=mdehaan state=directory"
以及（递归）删除目录和删除文件：
ansible webservers -m file -a "dest=/path/to/c state=absent"

管理程序包
您还可以使用临时任务通过软件包管理模块（例如yum）在受管节点上安装，更新或删除软件包。要确保安装软件包而不更新它：

$ ansible webservers -m yum -a "name=acme state=present"
要确保安装了特定版本的软件包：

$ ansible webservers -m yum -a "name=acme-1.5 state=present"
要确保软件包为最新版本：

$ ansible webservers -m yum -a "name=acme state=latest"
要确保未安装软件包：

$ ansible webservers -m yum -a "name=acme state=absent"

管理用户和组
您可以使用临时任务在托管节点上创建，管理和删除用户帐户：

$ ansible all -m user -a "name=foo password=<crypted password here>"

$ ansible all -m user -a "name=foo state=absent"
有关所有可用选项的详细信息，请参见用户模块文档，包括如何操作组和组成员资格。

管理服务
确保在所有Web服务器上启动了服务：

$ ansible webservers -m service -a "name=httpd state=started"
或者，在所有Web服务器上重新启动服务：

$ ansible webservers -m service -a "name=httpd state=restarted"
确保服务已停止：

$ ansible webservers -m service -a "name=httpd state=stopped"

ansible-doc file
```
## 常用模块
```
shell
command
copy
file
fetch
service
user
yum
Hostname
Cron
group
script
```
## playbook
```
hosts
tasks
handlers

```
## roles
site.yml     执行入口文件
roles        目录下的目录以角色名称命名
  common
    files    放用到的文件,如证书文件等
    handlers
      main.yml
    tasks
      main.yml
    templates 放模板文件  
    vars
    defaults
    meta
  mongod
group_vars   目录下文件以group名称命名
hosts        主机清单文件
