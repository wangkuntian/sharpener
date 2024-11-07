# Sharpener
UnionTech Team's Quick Patch Tool.

# 安装
设置虚环境，源码安装。
```bash
pip install .
```

注：UOS桌面操作系统 1050专业版需要提前作如下操作。

```shell
sudo apt install krb5-config krb5-user libkrb5-dev
# 参考链接: https://github.com/OfflineIMAP/offlineimap/issues/541
```

# 使用
```bash
uos-tool --help
Usage: uos-tool [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version
  --help     Show this message and exit.

Commands:
  gerrit  Gerrit Commands
  koji    Koji Commands
  rpm     RPM Packages Commands
  spec    Spec Commands

```

* gerrit命令用于对gerrit的一些操作
* koji命令用于拓展原本在koji中的一些命令
* rpm命令主要用于下载或者归档SRPM包
* spec命令主要用于对spec文件的操作

注意，由于在使用过程中会存在多种SRPM包的源和多个OpenStack版本，所以命令行工具的存储目录都存在类似下面的目录结构。
```bash
├── centos                    # 源，可选为centos和loongnix
│   └── openstack-victoria    # OpenStack版本
│       ├── packages          # SRPM包的存放位置
│       └── packages.txt      # SRPM包的归档文件，里是所有最新的SRPM包的信息。
```

**当命令行中有指定目录的参数，请确保当前用户在指定目录下拥有创建目录的权利。**

## 配置文件
编包工具默认的配置文件是/etc/sharpener/sharpener.conf
```bash
[DEFAULT]
save_path = '/opt/sharpener'

[rpm]
cached = True
source = 'centos'
openstack_version = 'victoria'

[koji]
host = '10.30.38.131'
user = 'openstack-a'
password = 'uos.com'
tag = 'kongzi-openstack-victoria'
parent_tag = 'kongzi'
tags = kongzi-openstack-victoria,fuyu-openstack-victoria
test_build = True


[gerrit]
host = '10.30.38.104'
port = 29418
admin = ut002944

user = wangkuntian
email = wangkuntian@uniontech.com

```

## RPM相关
```bash
uos-tool rpm --help
Usage: uos-tool rpm [OPTIONS] COMMAND [ARGS]...

  RPM Packages Commands

Options:
  --help  Show this message and exit.

Commands:
  archive   Archive Packages To Excel
  check     Print Given Srpm File's Package Name
  download  Download Packages
  freeze    Get Latest Packages From Source


```

### archive
使用archive将获取到最新的SRPM包的相关信息归档到Excel文件中，Excel文件的文件名加入了时间戳以区别。
```bash
uos-tool rpm archive --help
Usage: uos-tool rpm archive [OPTIONS]

  Archive Packages To Excel

Options:
  -d, --dir TEXT                  The directory of download packages
                                  [default: /opt/sharpener]
  -s, --source [loongnix|centos]  The source of packages  [default: centos]
  -v, --version [victoria|wallaby|xena|yoga]
                                  The version of openstack  [default:
                                  victoria]
  -t, --tag TEXT                  The tag of koji  [default: kongzi-openstack-
                                  victoria]
  --cache / --no-cache            Using Cache  [default: cache]
  --help                          Show this message and exit.

```

#### 参数解析
* -d，指定SRPM包的下载目录，工具会从此目录下拿取SRPM包，与koji中的进行比较。默认/opt/sharpener/。
* -s，指定SRPM包的源，可选项有loongnix和centos，默认是centos。
* -v，指定OpenStack的版本，可选版本有victoria、wallaby、xena、yoga，默认是victoria。
* -t，指定koji中的tag，默认是kongzi-openstack-victoria。
* --cache/--no-cache，是否启用缓存，默认启用。主要是为了读取指定目录下的packages.txt文件。默认目录是/opt/sharpener/。

#### 示例
保存到默认位置。
```bash
uos-tool rpm archive
```
保存到当前目录。
```bash
uos-tool rpm archive -d ./
```

### check
使用check命令可以获取给出的SRPM文件的包名。
```bash
uos-tool rpm check --help
Usage: uos-tool rpm check [OPTIONS]

  Print Given Srpm File's Package Name

Options:
  -d, --dir TEXT   The directory of srpms to check
  -f, --file TEXT  The file of srpms to check
  -s, --srpm TEXT  The name of srpm to check
  --help           Show this message and exit.
```

#### 参数解析
* -d，给出一个目录，输出目录下所有SRPM文件的包名。
* -f，给出一个文件，输出文件中所有SRPM的包名。
* -s，给出一个SRPM文件，输出SRPM的包名。

#### 示例
```bash
uos-tool rpm check -s openstack-nova-22.4.0-1.3.uelc20.src.rpm
openstack-nova
```

### download
使用download下载指定或者多个SRPM包。
```bash
uos-tool rpm download --help
Usage: uos-tool rpm download [OPTIONS]

  Download Packages

Options:
  -d, --dir TEXT                  The directory to save downloaded packages
                                  [default: /opt/sharpener]
  -s, --source [loongnix|centos]  The source of packages  [default: centos]
  -v, --version [victoria|wallaby|xena|yoga]
                                  The version of openstack  [default:
                                  victoria]
  --cache / --no-cache            Using Cache  [default: cache]
  -f, --file TEXT                 The file of downloaded packages
  -n, --name TEXT                 Download the package of specified name
  --help                          Show this message and exit.

```

#### 参数解析
* -d，指定SRPM包的下载目录。默认/opt/sharpener/。
* -s，指定SRPM包的源，可选项有loongnix和centos，默认是centos。
* -v，指定OpenStack的版本，可选版本有victoria、wallaby、xena、yoga，默认是victoria。
* --cache/--no-cache，是否启用缓存，默认启用。主要是为了读取指定目录下的packages.txt文件。默认目录是/opt/sharpener/。
* -f，指定需要下载的SRPM包的文件，与上面多个-n的形式类似。
* -n，指定SRPM包的名称可以是名称也可以是NVR的形式，可以指定多个。

#### 示例
下载单个包。
```bash
uos-tool rpm download -n python-cliff
```

下载多个包，-n的方式。
```bash
uos-tool rpm download -n openstack-cinder -n openstack-nova
```

下载多个包，-f的方式。
```bash
cat ./packages.txt
openstack-cinder
openstack-nova

uos-tool rpm download -f ./packages.txt
```

### freeze
使用freeze命令可获取指定源下的SRPM包的相关信息，并将信息输出到终端或者文件中。
```bash
uos-tool rpm freeze --help
Usage: uos-tool rpm freeze [OPTIONS]

  Get Latest Packages From Source

Options:
  -d, --dir TEXT                  The directory to save packages  [default:
                                  /opt/sharpener]
  -s, --source [loongnix|centos]  The source of packages  [default: centos]
  -v, --version [victoria|wallaby|xena|yoga]
                                  The version of openstack  [default:
                                  victoria]
  --cache / --no-cache            Using Cache  [default: cache]
  --help                          Show this message and exit.

```

#### 参数解析
* -d，指定SRPM包的下载目录。默认/opt/sharpener/。
* -s，指定SRPM包的源，可选项有loongnix和centos，默认是centos。
* -v，指定OpenStack的版本，可选版本有victoria、wallaby、xena、yoga，默认是victoria。
* --cache/--no-cache，是否启用缓存，默认启用。主要是为了读取指定目录下的packages.txt文件。默认目录是/opt/sharpener/。

#### 示例
```bash
uos-tool rpm freeze -d ./
```

## Koji相关
```bash
uos-tool koji --help
Usage: uos-tool koji [OPTIONS] COMMAND [ARGS]...

  Koji Commands

Options:
  --help  Show this message and exit.

Commands:
  build            Build Packages
  check-package    Check the package if it has been built
  delete-build     Delete Build
  get-task         Get Task Info
  get-task-error   Get Task Error
  list-builds      List Builds
  list-tasks       List Packages Tasks Info
  rebuild          Rebuild Packages
  set-build-owner  Set Build Owner
  tag-build        Add Tag To Builds
  untag-build      Untag Builds

```

### build
类似koji build的命令，提交SRPM进行编包。这里封装了koji的相关环境配置和用户配置，不需要再去初始化koji。

```bash
uos-tool koji build --help
Usage: uos-tool koji build [OPTIONS]

  Build Packages

Options:
  -d, --dir TEXT      The directory of packages to build
  -f, --file TEXT     The file of packages to build
  -p, --package TEXT  The package to build
  -t, --tag TEXT      The tag to add  [default: kongzi-openstack-victoria]
  --test / --no-test  Test build  [default: test]
  --limit INTEGER     Limit of packages build one time  [default: 20]
  --wait INTEGER      Wait to build packages  [default: 900]
  --help              Show this message and exit.


```

#### 参数解析
* -d，指定需要编包的SRPM文件的目录。
* -f，指定需要编包的文件路径，内容可以是package名称或者是SRPM包的路径，与下面多个-p的形式类似。
* -p，指定koji需要编包的package名称，或者是SRPM包的路径。
* -t，指定koji中的tag，默认是kongzi-openstack-victoria。
* --test/--no-test，是否是测试提交，默认是True。
* --limit，指定一次性提交多少个包，默认20个。
* --wait，指定一次性提交包后需要等待多少秒才能再次提交，默认900秒。

#### 示例
测试提交编包python-cliff，默认会去/opt/sharpener/根据源和OpenStack版本来查找python-cliff的SRPM包。
```bash
uos-tool koji build -p python-cliff
```

正式提交。
```bash
uos-tool koji build --test false -p python-cliff
```

指定SRPM包的路径。
```bash
uos-tool koji build -p ./python-cliff-3.4.0-1.el8.src.rpm
```

提交多个。
```bash
uos-tool koji build -p openstack-cinder -p openstack-nova
uos-tool koji build -p openstack-cinder -p /root/openstack-nova-22.4.0-1.el8.src.rpm
```

指定package文件。
```bash
cat ./packages.txt
openstack-cinder
/root/openstack-nova-22.4.0-1.el8.src.rpm

uos-tool koji build -f ./packages.txt
```

### check-package
检测包的最近一次构建是否编过，如果构建有错误会输出构建出错的原因，可以输出到Excel文件中。
```bash
uos-tool koji check-package --help
Usage: uos-tool koji check-package [OPTIONS]

  Check the package if it has been built

Options:
  -f, --file TEXT     The file of packages to get builds
  -p, --package TEXT  The package to get builds
  -t, --tag TEXT      The tag of build  [default: kongzi-openstack-victoria,
                      fuyu-openstack-victoria]
  --help              Show this message and exit.

```

#### 参数解析
* -f，指定需要检测的包的文件，默认None。
* -p，指定检测包的名称，默认是None。
* -t，指定构建的tag，默认是配置文件中的koji.tags。
* --archive/--no-archive，是否将结果归档到Excel文件中。
* -d，Excel归档文件的路径，默认是当前目录。

#### 示例
```bash
uos-tool koji check-package -p openstack-nova
Checking package openstack-nova
Package openstack-nova has already been built

```

### delete-build
删除指定构建
```bash
uos-tool koji delete-build --help
Usage: uos-tool koji delete-build [OPTIONS] <build>

  Delete Build

Options:
  --help  Show this message and exit.

```

### get-task
获取指定task ID的任务的执行状态。
```bash
uos-tool koji get-task --help
Usage: uos-tool koji get-task [OPTIONS]

  Get Task Info

Options:
  -f, --file TEXT           The file of task IDs to get
  -e, --excel TEXT          The excel file of build info , default is None
  -t, --task TEXT           Task ID
  --archive / --no-archive  If archive to excel file  [default: no-archive]
  -d, --dir TEXT            The path to save task info excel  [default: ./]
  --help                    Show this message and exit.

```

#### 参数解析
* -f，指定包含task ID的文件。
* -e，指定build命令中生成的Excel文件。
* -t，指定task ID。
* --archive/--no-archive，是否归档成Excel文件，默认否。
* -d，Excel文件存放目录，默认是当前目录。

#### 示例
```bash
uos-tool koji get-task -t 534785
openstack-nova finished
```

### get-task-error
获取任务失败的原因。
```bash
uos-tool koji get-task-error --help
Usage: uos-tool koji get-task-error [OPTIONS] <task>

  Get Task Error

Options:
  --help  Show this message and exit.

```

#### 参数解析
* task，task ID。

#### 示例
示例一。
```bash
uos-tool koji get-task-error 534785
[14:25:10] INFO     Task 534785 not failed
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Package        ┃                    Task                    ┃            Tag            ┃  State   ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ openstack-nova │ http://10.30.38.131/taskinfo?taskID=534785 │ kongzi-openstack-victoria │ finished │
└────────────────┴────────────────────────────────────────────┴───────────────────────────┴──────────┘


```
示例二。

```bash
uos-tool koji get-task-error 2100693
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Package          ┃                    Task                     ┃             Tag              ┃ State  ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ openstack-cinder │ http://10.30.38.131/taskinfo?taskID=2100693 │ fuyu-sw8a-openstack-victoria │ failed │
└──────────────────┴─────────────────────────────────────────────┴──────────────────────────────┴────────┘
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Error Reason     ┃                 NVR                 ┃  Task   ┃  State   ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ python3-os-brick │ python-os-brick-4.0.5-1.uel20.8a.01 │ 2100691 │ finished │
└──────────────────┴─────────────────────────────────────┴─────────┴──────────┘

```

### list-builds
查看指定tag下的build，以表格的形式输出到终端上，包括
```bash
uos-tool koji list-builds --help
Usage: uos-tool koji list-builds [OPTIONS] <package>

  List Builds

Options:
  -t, --tag TEXT   Build tag
  -u, --user TEXT  Build user
  --help           Show this message and exit.

```

#### 参数解析

* -t，指定build的tags，默认是None，不指定则为全部tag。
* -u，指定build的构建者，默认是None，不指定则为全部的用户。

#### 示例
查看python-cliff包下的所有build。
```bash
uos-tool koji list-builds python-cliff
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ NVR                              ┃  Task   ┃ Arches ┃ Tags                         ┃    Owner     ┃  State   ┃    Finished Time    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ python-cliff-4.3.0-1.uos25       │ 2239604 │ noarch │ V25                          │  mahailiang  │ finished │ 2024-10-12 04:20:23 │
│ python-cliff-3.4.0-1.uel20.8a.01 │ 2080222 │ noarch │ fuyu-sw8a-openstack-victoria │ fuyu-jenkins │ finished │ 2024-07-28 20:42:44 │
│ python-cliff-3.7.0-1.uel20.8a    │ 2018884 │ noarch │ fuyu-sw8a                    │ fuyu-jenkins │ finished │ 2024-07-16 09:31:11 │
│ python-cliff-4.3.0-1.uel         │ 1633712 │        │                              │     V25      │  failed  │ 2024-04-14 14:51:09 │
│ python-cliff-3.4.0-1.uelm20      │ 1459386 │ noarch │                              │ openstack-a  │ finished │ 2024-03-15 22:23:00 │
│ python-cliff-3.4.0-1.uelm20.1    │ 1182485 │ noarch │ kongzi-mips                  │    kongzi    │ finished │ 2023-12-21 13:36:40 │
│ python-cliff-3.4.0-1.uel20.jk.01 │ 684607  │ noarch │ fuyu-sw-openstack-victoria   │ openstack-e  │ finished │ 2023-07-05 10:09:33 │
│ python-cliff-1.4.4-1.uelc20      │ 552046  │ noarch │ kongli                       │    kongli    │ finished │ 2023-06-08 02:33:38 │
│ python-cliff-3.4.0-1.uelc20      │ 324725  │ noarch │ kongzi-openstack-victoria    │ openstack-a  │ finished │ 2023-04-12 17:33:20 │
│ python-cliff-3.4.0-1.uelc20.1    │  63234  │ noarch │ kongzi                       │    kongzi    │ finished │ 2023-03-14 23:42:30 │
│                                  │         │        │ kongzi-1050u2-update         │              │          │                     │
│                                  │         │        │ kongzi-sw                    │              │          │                     │
│ python-cliff-3.7.0-1.uel20.jk    │  None   │ noarch │ fuyu-sw                      │     fuyu     │ finished │ 2023-03-10 10:05:49 │
└──────────────────────────────────┴─────────┴────────┴──────────────────────────────┴──────────────┴──────────┴─────────────────────┘

```

查看python-cliff包的指定tag下的所有build。
```bash
uos-tool koji list-builds -t kongzi-openstack-victoria python-cliff
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ NVR                         ┃  Task  ┃ Arches ┃ Tags                      ┃    Owner    ┃  State   ┃    Finished Time    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ python-cliff-3.4.0-1.uelc20 │ 324725 │ noarch │ kongzi-openstack-victoria │ openstack-a │ finished │ 2023-04-12 17:33:20 │
└─────────────────────────────┴────────┴────────┴───────────────────────────┴─────────────┴──────────┴─────────────────────┘

```

查看python-cliff包的指定构建者下的所有build。
```bash
uos-tool koji list-builds -u openstack-a python-cliff
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ NVR                         ┃  Task   ┃ Arches ┃ Tags                      ┃    Owner    ┃  State   ┃    Finished Time    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ python-cliff-3.4.0-1.uelm20 │ 1459386 │ noarch │                           │ openstack-a │ finished │ 2024-03-15 22:23:00 │
│ python-cliff-3.4.0-1.uelc20 │ 324725  │ noarch │ kongzi-openstack-victoria │ openstack-a │ finished │ 2023-04-12 17:33:20 │
└─────────────────────────────┴─────────┴────────┴───────────────────────────┴─────────────┴──────────┴─────────────────────┘

```

### list-tasks
查看包的任务列表。
```bash
uos-tool koji list-tasks --help
Usage: uos-tool koji list-tasks [OPTIONS]

  List Packages Tasks Info

Options:
  -u, --user TEXT     The build's owner
  -t, --tag TEXT      The tag of build  [default: kongzi-openstack-victoria]
  -d, --days INTEGER  The number of days ago  [default: 30]
  -p TEXT             The package name
  --help              Show this message and exit.

```

#### 参数解析
* -u，指定构建用户，默认是None。
* -t，指定构建的tag，默认是kongzi-openstack-victoria。
* -d，指定搜寻task的最大时间范围，默认是30天。

#### 示例
```bash
uos-tool koji list-tasks -p ustack -u openstack-a -t V25 -d 10
┏━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Package ┃ State    ┃ Test Build ┃ Task                                        ┃ Completion Time     ┃ Owner       ┃
┡━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ ustack  │ finished │ true       │ http://10.30.38.131/taskinfo?taskID=2393549 │ 2024-11-04 10:35:41 │ openstack-a │
│ ustack  │ failed   │ false      │ http://10.30.38.131/taskinfo?taskID=2395176 │ 2024-11-04 11:34:17 │ openstack-a │
│ ustack  │ finished │ false      │ http://10.30.38.131/taskinfo?taskID=2396148 │ 2024-11-04 14:28:53 │ openstack-a │
└─────────┴──────────┴────────────┴─────────────────────────────────────────────┴─────────────────────┴─────────────┘

```

### rebuild
重新构建。
```bash
uos-tool koji rebuild --help
Usage: uos-tool koji rebuild [OPTIONS] <task>

  Rebuild Packages

Options:
  --privileged  Privileged rebuild  [default: True]
  --help        Show this message and exit.

```

#### 参数解析
* --privileged，是否用高优先级，默认True。


### set-build-owner
设置构建的用户。
```bash
 uos-tool koji set-build-owner --help
Usage: uos-tool koji set-build-owner [OPTIONS] <build>

  Set Build Owner

Options:
  -u, --user TEXT  The user to set  [default: openstack-a]
  --help           Show this message and exit.


```

#### 参数解析
* -u，指定构建用户，默认是openstack-a。


### tag-build
将build打上指定tag，如果package不在对应的tag里，会自动加入。
```bash
uos-tool koji tag-build --help
Usage: uos-tool koji tag-build [OPTIONS] <build>

  Add Tag To Builds

Options:
  -t, --tag TEXT  The tag to add  [default: kongzi-openstack-victoria]
  --help          Show this message and exit.


```

#### 参数解析
* -t，指定build的tag，默认是kongzi-openstack-victoria。

#### 示例
```bash
uos-tool koji tag-build python-cliff-2.13.0-1.uelc20.03 python-cliff-2.13.0-1.uelc20.04
```

### untag-build
将build打上指定tag，如果package不在对应的tag里，会自动加入。
```bash
uos-tool koji untag-build --help
Usage: uos-tool koji untag-build [OPTIONS] <build>

  Untag Builds

Options:
  -t, --tag TEXT  The tag to remove  [default: kongzi-openstack-victoria]
  --help          Show this message and exit.

```

#### 参数解析
* -t，指定移除的tag，默认是kongzi-openstack-victoria。

#### 示例
```bash
uos-tool koji untag-build python-cliff-2.13.0-1.uelc20.03 python-cliff-2.13.0-1.uelc20.04
```

## Gerrit相关
```bash
uos-tool gerrit --help
Usage: uos-tool gerrit [OPTIONS] COMMAND [ARGS]...

  Gerrit Commands

Options:
  --help  Show this message and exit.

Commands:
  build            Build Packages with gerrit
  clone            Clone Repository
  create           Create Repository
  create-and-init  Create Repository and Init
  create-branch    Create A New Branch For A Project
  delete           Delete Repository
  import           Import SRPM File To Repository
  init             Init Repository

```

### build
将gerrit的project提交到koji上进行编包。
```bash
uos-tool gerrit build --help
Usage: uos-tool gerrit build [OPTIONS]

  Build Packages with gerrit

Options:
  -f, --file TEXT                 The file of packages to build
  -p, --package TEXT              The package to build
  -t, --tag TEXT                  The tag to add  [default: kongzi-openstack-
                                  victoria]
  -b [openstack-train-1060a|openstack-victoria-1060a|openstack-victoria-1060e|openstack-victoria-1060e-sw]
                                  The branch of repository
  --test / --no-test              Test build  [default: test]
  --limit INTEGER                 Limit of packages build one time  [default:
                                  20]
  --wait INTEGER                  Wait to build packages  [default: 900]
  --archive / --no-archive        If archive to excel file  [default: no-
                                  archive]
  -d, --dir TEXT                  The path to save build info excel  [default:
                                  ./]
  --priority INTEGER              Build priority  [default: -10]
  --channel TEXT                  Build channel
  --help                          Show this message and exit.

```

#### 参数解析
* -f，指定包含包名的文件。
* -p，指定koji需要编包的package名称。
* -t，指定koji中的tag，默认是kongzi-openstack-victoria。
* -b，gerrit项目中的分支名，可选值openstack-train-1060a、openstack-victoria-1060a、openstack-victoria-1060e、openstack-victoria-1060e-sw，默认是None。
* --test/--no-test，是否是测试提交，默认是True。
* --limit，指定一次性提交多少个包，默认20个。
* --wait，指定一次性提交包后需要等待多少秒才能再次提交，默认900秒。
* --archive/--no-archive，是否归档成Excel文件，默认否。
* -d，Excel文件存放目录，默认是当前目录。
* --priority，构建的优先级，数字越小优先级越高，默认-10。
* --channel，构建的通道，默认None。

#### 示例
```bash
uos-tool gerrit build -t kongzi-openstack-victoria -b openstack-victoria-1060a -p openstack-nova
```

### clone
将gerrit项目clone并做相关操作。
```bash
 uos-tool gerrit clone --help
Usage: uos-tool gerrit clone [OPTIONS] <repo>

  Clone Repository

Options:
  -d TEXT                         The directory of the repository  [default: ./]
  -p [openstack]                  The prefix of repository, like
                                  openstack/[repo]  [default: openstack]
  -b [openstack-train-1060a|openstack-victoria-1060a|openstack-victoria-1060e|openstack-victoria-1060e-sw]
                                  The branch of repository  [default: master]
  -c TEXT                         The command after clone
  -m TEXT                         Commit message
  --push / --no-push              Push change to the repository  [default: no-
                                  push]
  --help                          Show this message and exit.

```

#### 参数解析
* -d，存放项目的目录，默认是当前目录。
* -p，项目名的前缀，默认是openstack。
* -b，gerrit项目中的分支名，可选值openstack-train-1060a、openstack-victoria-1060a、openstack-victoria-1060e、openstack-victoria-1060e-sw，默认是master。
* -c，clone项目之后执行的命令。
* -m，提交的信息。
* --push/--no-push，是否推送提交，默认否。

#### 示例
```bash
uos-tool gerrit clone -b openstack-victoria-1060a -c "touch test.txt" -m "Add test.txt" openstack-nova
```

### create
创建一个新的gerrit项目。
```bash
 uos-tool gerrit create --help
Usage: uos-tool gerrit create [OPTIONS] <repo>

  Create Repository

Options:
  -p [openstack]  The prefix of repository, like openstack/[repo].  [default:
                  openstack]
  --help          Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。

#### 示例
```bash
uos-tool gerrit create openstack-nova
```

### create-and-init
创建gerrit项目并初始化。
```bash
uos-tool gerrit create-and-init --help
Usage: uos-tool gerrit create-and-init [OPTIONS] <repo>

  Create Repository and Init

Options:
  -p [openstack]        The prefix of repository, like openstack/[repo].
                        [default: openstack]
  -d TEXT               The directory of the repository  [default: ./]
  --clean / --no-clean  If clean the environment when initialization finished
                        [default: clean]
  --help                Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。
* -d，项目的存放目录，默认是当前目录。
* --clean/--no-clean，初始化完项目后是否清空，默认True。

#### 示例
```bash
uos-tool gerrit create-and-init --no-clean openstack-nova
```

### create-branch
创建gerrit项目的分支。
```bash
uos-tool gerrit create-branch --help
Usage: uos-tool gerrit create-branch [OPTIONS] <project> <branch>

  Create A New Branch For A Project

Options:
  -p [openstack]                  The prefix of repository, like
                                  openstack/[repo]  [default: openstack]
  -b [master|train-source|victoria-source]
                                  The base of created branch  [default:
                                  master]
  --help                          Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。
* -d，指定创建分支的base分支，默认是master。

#### 示例
```bash
uos-tool gerrit create-branch -b master openstack-nova openstack-victoria-1060e
```

### delete
删除gerrit项目。
```bash
uos-tool gerrit delete --help
Usage: uos-tool gerrit delete [OPTIONS] <repo>

  Delete Repository

Options:
  -p [openstack]  The prefix of repository, like openstack/[repo]  [default:
                  openstack]
  --help          Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。

#### 示例
```bash
uos-tool gerrit delete openstack-nova
```

### import
导入SRPM文件到gerrit项目中。
```bash
uos-tool gerrit import --help
Usage: uos-tool gerrit import [OPTIONS] <repo>

  Import SRPM File To Repository

Options:
  -p [openstack]                  The prefix of repository, like
                                  openstack/[repo]  [default: openstack]
  -b [openstack-train-1060a|openstack-victoria-1060a|openstack-victoria-1060e|openstack-victoria-1060e-sw]
                                  The branch of repository
  -d TEXT                         The directory of the repository  [default:
                                  ./]
  -f TEXT                         The srpm file to import
  -m TEXT                         Commit message
  --clean / --no-clean            If clean the environment when job finished
                                  [default: no-clean]
  --help                          Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。
* -b，gerrit项目中的分支名，可选值openstack-train-1060a、openstack-victoria-1060a、openstack-victoria-1060e、openstack-victoria-1060e-sw，默认是None。
* -d，存放项目的目录，默认是当前目录。
* -f，指定SRPM文件。
* -m，提交的信息。
* --clean/--no-clean，初始化完项目后是否清空，默认是。

#### 示例
```bash
uos-tool gerrit import -b openstack-victoria-1060a -f ./openstack-nova-22.4.0-1.uel20.02.src.rpm -m "init" openstack-nova
```

### init
初始化gerrit项目。
```bash
uos-tool gerrit init --help
Usage: uos-tool gerrit init [OPTIONS] <repo>

  Init Repository

Options:
  -p [openstack]        The prefix of repository, like openstack/[repo].
                        [default: openstack]
  -d TEXT               The directory of the repository  [default: ./]
  --clean / --no-clean  If clean the environment when initialization finished
                        [default: clean]
  --help                Show this message and exit.

```

#### 参数解析
* -p，项目名的前缀，默认是openstack。
* -d，存放项目的目录，默认是当前目录。
* --clean/--no-clean，初始化完项目后是否清空，默认True。

#### 示例
```bash
uos-tool gerrit init openstack-nova
```

## spec文件相关
```bash
uos-tool spec --help
Usage: uos-tool spec [OPTIONS] COMMAND [ARGS]...

  Spec Commands

Options:
  --help  Show this message and exit.

Commands:
  update  Update Spec File

```

### update
修改spec文件。
```bash
uos-tool spec update --help
Usage: uos-tool spec update [OPTIONS] <spec>

  Update Spec File

Options:
  -c, --changelog TEXT      The changelog message
  -v, --version TEXT        The version of spec
  -r, --release TEXT        The release of spec
  -m, --micro-version TEXT  The micro-version of spec
  -n, --name TEXT           User name  [default: xxx]
  -e, --email TEXT          User email  [default: xxx@uniontech.com]
  --help                    Show this message and exit.

```

#### 参数解析
* -c，changelog的内容。
* -v，修改后的版本。
* -r，修改后release的版本。
* -m，修改后的小版本号。
* -n，changelog提交的用户名称。
* -e，changelog提交的用户邮箱。

#### 示例
```bash
uos-tool spec update -v 2.5 ./openstack-nova.spec
```
