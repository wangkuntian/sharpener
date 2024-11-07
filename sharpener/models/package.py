# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'package.py'
__author__  =  'king'
__time__    =  '2024/8/1 上午10:18'


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

from rich.table import Table
from rich.console import Console
from typing import Dict, Optional

from sharpener.models import base
from sharpener.models.item import BuildState
from sharpener.common.exceptions import PackageNotFoundException

BUILD_TABLE = [
    ('NVR', 'left', 'cyan', True),
    ('Task', 'center', 'cyan', True),
    ('Arches', 'center', 'cyan', False),
    ('Tags', 'left', 'magenta', False),
    ('Owner', 'center', 'magenta', False),
    ('State', 'center', 'cyan', False),
    ('Finished Time', 'center', 'green', False),
]


class Package(base.Base):
    def __init__(self, *args, **kwargs):
        self.name = ''
        self.client = None
        super().__init__(*args, **kwargs)
        self.name = self._handle_package_name(self.name)
        self.info = self.get_package_info(self.name)
        self.builds = []

    @staticmethod
    def _handle_package_name(package: str):
        if '.' in package:
            package = package.replace('.', '-')
        if package.startswith('python3'):
            package = package.replace('python3', 'python')
        return package

    def get_package_info(self, package) -> Optional[Dict[str, str]]:
        pkg_info = self.client.get_package(package)
        if not pkg_info:
            if package.islower():
                raise PackageNotFoundException(package)
            package = package.lower()
            pkg_info = self.client.get_package(package)
            if not pkg_info:
                PackageNotFoundException(package)
        return pkg_info

    def get_builds(
        self,
        user: str = None,
    ):
        self.builds = self.client.list_builds(
            package_id=self.info['id'], user_id=user
        )

    def get_tagged_builds(
        self, tag: str, user: str = None, latest: bool = True
    ):
        self.builds = self.client.list_tagged_builds(
            tag, package=self.info['name'], owner=user, latest=latest
        )

    def get_build_info(
        self,
        build: Dict,
        arch: bool = True,
    ):
        nvr = build['nvr']
        owner = build['owner_name']
        build_id = build['build_id']
        completion_time = build['completion_time']
        if completion_time:
            completion_time = ''.join(completion_time.split('.')[:-1])
        state = build['state']
        state = BuildState.get_state(state)
        task_id = build['task_id']
        build_tags = self.client.list_tags(build=build_id)
        build_tags = [t['name'] for t in build_tags]
        if arch:
            rpms = self.client.list_rpms(build_id=build_id)
            arches = [r['arch'] for r in rpms if r.get('arch', None)]
            if 'src' in arches:
                arches.remove('src')
            arches = '\n'.join(set(arches))
        else:
            arches = ' '
        return (
            nvr,
            str(task_id),
            arches,
            '\n'.join(build_tags),
            owner,
            state,
            completion_time,
        )

    def print_builds_table(
        self,
        arch: bool = True,
    ):
        table = Table()
        for col in BUILD_TABLE:
            table.add_column(
                col[0], justify=col[1], style=col[2], no_wrap=col[3]
            )
        for build in self.builds:
            data = self.get_build_info(build, arch)
            table.add_row(*data)

        if table.columns:
            console = Console()
            console.print(table)
