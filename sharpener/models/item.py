# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'item.py'
__author__  =  'king'
__time__    =  '2022/7/18 16:40'


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

from sharpener.models import base
from sharpener.common import utils


class PackageStatus:
    ok = 'OK'
    need_upgrade = 'Need Upgrade'
    need_created = 'Need Create'
    need_add_tag = 'Need Add Tag'


class Package(base.Base):
    def __init__(self, *args, **kwargs):
        self.id = ''
        self.name = ''
        self.version = ''
        self.versions = []
        self.release = ''
        self.src_rpm = ''
        self.path = ''
        self.url = ''
        super(Package, self).__init__(*args, **kwargs)

    def __str__(self):
        return f'Package: {self.name}'


class Source(base.Base):
    def __init__(self, *args, **kwargs):
        self.name = str
        self.release = str
        self.host = str
        self.os_version = str
        self.openstack_version = str
        self.url = ''
        super(Source, self).__init__(*args, **kwargs)
        self.url = self.url.format(
            host=self.host,
            os_version=self.os_version,
            openstack_version=self.openstack_version)


class Project(base.Base):
    def __init__(self, *args, **kwargs):
        self.save_path = ''
        self.source = None
        super(Project, self).__init__(*args, **kwargs)

    def get_pkg_file_path(self):
        return (f'{self.save_path}/{self.source.name}/'
                f'{self.source.openstack_version}/packages/')

    def get_cache_file(self):
        return (f'{self.save_path}/{self.source.name}/'
                f'{self.source.openstack_version}/packages.txt')

    def get_pkg_excel_file(self, now: bool = True):
        file = (f'{self.save_path}/'
                f'{self.source.name}-{self.source.openstack_version}')
        if now:
            time = utils.get_current_datetime()
            return f'{file}-{time}.xlsx'
        return f'{file}.xlsx'


class TaskState(object):
    WAITING = 0
    BUILDING = 1
    FINISHED = 2
    CANCELED = 3
    ASSIGNED = 4
    FAILED = 5
    BUILD_EXISTS = -1

    ALL = [0, 1, 2, 3, 4, 5]


class TaskStates(object):
    @classmethod
    def get_state(cls, state_code: int) -> str:
        states = {
            TaskState.WAITING: 'wait to build',
            TaskState.BUILDING: 'building',
            TaskState.FINISHED: 'finished',
            TaskState.CANCELED: 'canceled',
            TaskState.FAILED: 'failed',
            TaskState.BUILD_EXISTS: 'build already exists'
        }
        return states.get(state_code)


class BuildState(object):
    BUILDING = 0
    COMPLETE = 1
    DELETED = 2
    FAILED = 3
    CANCELED = 4

    @classmethod
    def get_state(cls, state_code: int) -> str:
        states = {
            BuildState.DELETED: 'deleted',
            BuildState.BUILDING: 'building',
            BuildState.COMPLETE: 'finished',
            BuildState.CANCELED: 'canceled',
            BuildState.FAILED: 'failed',

        }
        return states.get(state_code)
