# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'objects.py'
__author__  =  'king'
__time__    =  '2024/8/1 上午9:29'


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
from rich.align import Align
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from sharpener.common.log import LOG
from sharpener.conf import CONF
from sharpener.models import base
from sharpener.models.item import TaskState, TaskStates
from sharpener.common.exceptions import (
    TaskNotFoundException,
    PackageNotFoundException,
)
from sharpener.models.package import Package

TASK_ERROR_TABLE = [
    ('Package', 'left', 'white', True),
    ('Task', 'center', 'green', True),
    ('Tag', 'center', 'cyan', True),
    ('State', 'center', 'green', True),
]

TASK_REASON_TABLE = [
    ('Error Reason', 'red', 'cyan', True),
    ('NVR', 'center', 'blue', True),
    ('Task', 'center', 'green', True),
    ('State', 'center', 'green', True),
]

ERROR_PREFIX_1 = 'No matching package to install: '
ERROR_PREFIX_2 = 'nothing provides'
INIT_MOCK_ERROR = 'could not init mock buildroot'

TASKS_TABLE = [
    ('Package', 'left', 'cyan', True),
    ('State', 'left', 'magenta', True),
    ('Test Build', 'left', 'cyan', False),
    ('Task', 'left', 'magenta', True),
    ('Completion Time', 'left', 'cyan', False),
    ('Owner', 'left', 'magenta', False),
]


def task_url(task_id: str) -> str:
    return f"http://{CONF.koji.host}/taskinfo?taskID={task_id}"


def remove_debug(line: str):
    if '443' in line:
        line = line.replace('DEBUG util.py:443:', '')
    else:
        line = line.replace('DEBUG util.py:444:', '')
    return line[3:]


class Task(base.Base):
    def __init__(self, *args, **kwargs):
        self.id = ''
        self.client = None
        super().__init__(*args, **kwargs)
        self.reason = []
        self.url = task_url(self.id)
        self.package = ''
        self.state = 0
        self.tag = ''
        self.info = dict()
        self.init_task_info()

    def init_task_info(self):
        task_info = self.client.get_taskinfo(self.id)
        if not task_info:
            raise TaskNotFoundException(self.id)
        self.info = task_info
        build_request = self.info.get('request', None)
        if build_request:
            if len(build_request) == 3:
                build, self.tag, opts = build_request
            elif len(build_request) == 5:
                build, self.tag, arch, test_build, opts = build_request
            else:
                build = self.tag = opts = None
            if isinstance(self.tag, int):
                self.tag = self.client.get_tag(self.tag)['name']
            if 'git+https://' in build or 'git+http://' in build:
                self.package = build.split('#')[0].split('/')[-1]
            elif 'cli-build/' in build:
                self.package = build.split('/')[-1]
        self.state = self.info.get('state', None)
        if self.state == TaskState.FAILED:
            self.handle_failed_task()
        else:
            LOG.info(f"Task {self.id} not failed.")

    def handle_failed_task(self):
        task_result = self.client.get_task_result(self.id)
        children = self.client.get_task_children(self.id)
        child_id = None
        for child in children:
            method = child.get('method', None)
            state = child.get('state', None)
            if state == TaskState.FAILED:
                if method in ['buildSRPMFromSCM', 'buildArch']:
                    child_id = child['id']
                    break
        if child_id and INIT_MOCK_ERROR in task_result:
            result = self.client.read_task_mock_log(child_id)
            error = 'Error:'
            if error in result:
                lines = result.split('\n')
                start = -1
                end = -1
                for index, line in enumerate(lines):
                    if error in line:
                        start = index
                    if not line:
                        end = index
                error_info = '\n'.join(lines[start:end])
                self.reason.append(error_info)

        elif child_id and 'root.log' in task_result:
            result = self.client.read_task_root_log(child_id)
            error = 'No matching package to install'
            if error in result:
                for line in result.split('\n'):
                    if error not in line:
                        continue
                    package_name = line.split(': ')[-1].replace("'", '')
                    self.reason.append(f'{error}: {package_name}')
            error = 'Error:'
            if error in result:
                lines = result.split('\n')
                start = -1
                end = -1
                for index, line in enumerate(lines):
                    if error in line:
                        start = index + 1
                    if 'util.py:443' in line or 'util.py:444' in line:
                        end = index
                errors = list(map(remove_debug, lines[start : end + 1]))
                if len(errors) > 0:
                    error_info = '\n'.join(errors)
                    self.reason.append(error_info)
            if len(self.reason) == 0:
                result = self.client.read_task_build_log(child_id)
                error = 'RPM build errors:'
                if error in result:
                    lines = result.split('\n')
                    start = -1
                    end = -1
                    for index, line in enumerate(lines):
                        if error in line:
                            start = index
                        if start <= index and 'raise' in line:
                            end = index
                    error_info = '\n'.join(lines[start : end + 1])
                    self.reason.append(error_info)

        if len(self.reason) == 0:
            self.reason.append(task_result)

    def print_task_table(self):
        state = TaskStates.get_state(self.state)
        table = Table()
        for col in TASK_ERROR_TABLE:
            table.add_column(
                col[0], justify=col[1], style=col[2], no_wrap=col[3]
            )

        table.add_row(
            *(
                self.package,
                self.url,
                self.tag,
                state,
            )
        )

        console = Console()
        console.print(table)
        if self.state != TaskState.FAILED:
            return
        error_table = Table()
        for col in TASK_REASON_TABLE:
            error_table.add_column(
                col[0], justify=col[1], style=col[2], no_wrap=col[3]
            )
        for r in self.reason:
            nvr, task_id, state = '', '', ''
            if r.startswith(ERROR_PREFIX_1):
                package = r.split(ERROR_PREFIX_1)[-1].strip()
                r = package
                package = package.split(' ')[0].strip()
                try:
                    package = Package(name=package, client=self.client)
                    package.get_tagged_builds(self.tag, latest=True)
                    if not package.builds:
                        package.get_builds()
                    build = package.builds[0]
                    (
                        nvr,
                        task_id,
                        arches,
                        build_tags,
                        owner,
                        state,
                        completion_time,
                    ) = package.get_build_info(build, False)

                except PackageNotFoundException as ex:
                    nvr = str(ex)
            error_table.add_row(*(r, nvr, task_id, state))
        console.print(error_table)


def _get_task_info(task):
    build_request = task.get('request', None)
    build, target, opts = build_request
    state = TaskStates.get_state(task['state'])
    completion_time = task.get('completion_time')
    user_name = task.get('owner_name', None)
    test_build = 'true' if opts.get('scratch', False) else 'false'
    if completion_time:
        completion_time = completion_time.split('.')[0]
    return build, target, state, completion_time, user_name, test_build


class Tasks(base.Base):
    def __init__(self, *args, **kwargs):

        self.client = None
        self.tag = ''
        self.package = ''
        super().__init__(*args, **kwargs)
        self.tasks = []

    def get_tasks(self, user_id: str, days: int):
        self.tasks = self.client.list_tasks(user_id, days=days)

    def check_task_info(self, task):
        build_request = task.get('request', None)
        if not build_request:
            return
        build, target, opts = build_request
        if target != self.tag:
            return
        if self.package not in build:
            return False
        if 'git+https://' in build or 'git+http://' in build:
            package_name = build.split('#')[0].split('/')[-1]
            if package_name != self.package:
                return
        elif 'cli-build/' in build:
            srpm = build.split('/')[-1]
            if not srpm.startswith(self.package):
                return
        state = TaskStates.get_state(task['state'])
        completion_time = task.get('completion_time')
        user_name = task.get('owner_name', None)
        test_build = 'true' if opts.get('scratch', False) else 'false'
        if completion_time:
            completion_time = completion_time.split('.')[0]
        return state, completion_time, user_name, test_build

    def print_tasks_table(self):
        table = Table()
        for col in TASKS_TABLE:
            table.add_column(
                col[0], justify=col[1], style=col[2], no_wrap=col[3]
            )
        if self.package:
            for task in self.tasks:
                data = self.check_task_info(task)
                if not data:
                    continue
                (
                    state,
                    completion_time,
                    user_name,
                    test_build,
                ) = data
                table.add_row(
                    *(
                        self.package,
                        state,
                        test_build,
                        task_url(task['id']),
                        completion_time,
                        user_name,
                    )
                )

        else:
            for task in self.tasks:
                (
                    build,
                    target,
                    state,
                    completion_time,
                    user_name,
                    test_build,
                ) = _get_task_info(task)

                if target != self.tag:
                    continue
                package = None
                if 'git+https://' in build or 'git+http://' in build:
                    package = build.split('#')[0].split('/')[-1]
                elif 'cli-build/' in build:
                    package = build.split('/')[-1]
                table.add_row(
                    *(
                        package,
                        state,
                        test_build,
                        task_url(task['id']),
                        completion_time,
                        user_name,
                    )
                )

        console = Console()
        console.print(table)
