# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  '__init__.py'
__author__  =  'king'
__time__    =  '2023/2/8 11:24'


                              _ooOoo_
                             o8888888o
                             88" . "88
                             (| -_- |)
                             O\  =  /O
                          ____/`---'\____
                        .'  \\|     |//  `.
                       /  \\|||  :  |||//  \
                      /  _||||| -:- |||||-  \
                      |   | \\\  -  /// |   |
                      | \_|  ''\---/''  |   |
                      \  .-\__  `-`  ___/-. /
                    ___`. .'  /--.--\  `. . __
                 ."" '<  `.___\_<|>_/___.'  >'"".
                | | :  `- \`.;`\ _ /`;.`/ - ` : | |
                \  \ `-.   \_ __\ /__ _/   .-` /  /
           ======`-.____`-.___\_____/___.-`____.-'======
                              `=---='
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                       佛祖保佑        永无BUG
"""

from oslo_config import cfg
from oslo_config.cfg import ConfigParser, _Namespace

TAGS = ['kongzi', 'kongzi-openstack-victoria', 'fuyu-openstack-victoria']
CONFIG_FILE = '/etc/sharpener/sharpener.conf'
OPENSTACK_VERSIONS = ['victoria', 'wallaby', 'xena', 'yoga']
SOURCES = ['loongnix', 'centos']
BRANCHES = [
    'openstack-train-1060a',
    'openstack-victoria-1060a',
    'openstack-victoria-1060e',
    'openstack-victoria-1060e-sw',
]
CONF = cfg.CONF


def rpm_register_opts(conf):
    rpm_group = cfg.OptGroup('rpm', title='RPM options', help='')
    rpm_opts = [
        cfg.BoolOpt('cached', default=True, help=''),
        cfg.StrOpt('source', default='centos', choices=SOURCES, help=''),
        cfg.StrOpt(
            'openstack_version',
            default='victoria',
            choices=OPENSTACK_VERSIONS,
            help='',
        ),
    ]

    conf.register_group(rpm_group)
    conf.register_opts(rpm_opts, group=rpm_group)


def koji_register_opts(conf):
    koji_group = cfg.OptGroup('koji', title='koji options', help='')
    koji_opts = [
        cfg.IPOpt('host', default='10.30.38.131', help=''),
        cfg.StrOpt('user', default='openstack-a', help=''),
        cfg.StrOpt('password', default='uos.com', help=''),
        cfg.StrOpt('tag', default='kongzi-openstack-victoria', help=''),
        cfg.StrOpt('parent_tag', default='kongzi', help=''),
        cfg.ListOpt('tags', default=TAGS, help=''),
        cfg.BoolOpt('test_build', default=True, help=''),
        cfg.StrOpt(
            'need_build_packages_file', default='packages.txt', help=''
        ),
    ]

    conf.register_group(koji_group)
    conf.register_opts(koji_opts, group=koji_group)


def gerrit_register_opts(conf):
    gerrit_group = cfg.OptGroup('gerrit', title='gerrit options')
    gerrit_opts = [
        cfg.IPOpt('host', default='10.30.38.104', help=''),
        cfg.PortOpt('port', default=29418, help=''),
        cfg.StrOpt('admin', default='ut002944', help=''),
        cfg.StrOpt('user', default='wangkuntian', help=''),
        cfg.StrOpt('email', default='wangkuntian@uniontech.com', help=''),
    ]
    conf.register_group(gerrit_group)
    conf.register_opts(gerrit_opts, group=gerrit_group)


def setup(config_file: str = CONFIG_FILE):
    CONF._config_opts = CONF._make_config_options(config_file, '')
    CONF.register_cli_opts(CONF._config_opts)
    namespace = _Namespace(CONF)
    ConfigParser._parse_file(config_file, namespace)
    CONF._namespace = namespace

    default_opts = [cfg.StrOpt('save_path', default='/opt/sharpener', help='')]

    CONF.register_opts(default_opts)

    rpm_register_opts(CONF)
    koji_register_opts(CONF)
    gerrit_register_opts(CONF)


setup()
