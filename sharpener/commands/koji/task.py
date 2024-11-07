# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'task.py'
__author__  =  'king'
__time__    =  '2024/4/1 下午1:16'


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

import koji
import click
from typing import List, Dict
from rich.console import Console
from rich.table import Table

from sharpener.common.exceptions import UserNotFoundException
from sharpener.common.log import LOG
from sharpener.common.pkg import format_package
from sharpener.conf import CONF
from sharpener.common import utils
from sharpener.common.koji import Koji
from sharpener.commands.koji import group, task_url
from sharpener.models.item import TaskState, TaskStates
from sharpener.models.task import Task, Tasks
from sharpener.models.user import User

task_columns = ['Package', 'State', 'Info', 'Task ID', 'URL', 'Reason']
task_table = [
    ('Package', 'left', 'cyan', True),
    ('State', 'left', 'magenta', True),
    ('Test Build', 'left', 'cyan', False),
    ('Task', 'left', 'magenta', True),
    ('Completion Time', 'left', 'cyan', False),
    ('Owner', 'left', 'magenta', False),
]


@group.command(name='list-tasks', help='List Packages Tasks Info')
@click.option(
    '-u',
    '--user',
    default=None,
    show_default=True,
    help=f"The build's owner",
)
@click.option(
    '-t',
    '--tag',
    default=CONF.koji.tag,
    show_default=True,
    help=f"The tag of build",
)
@click.option(
    '-d',
    '--days',
    'days',
    default=30,
    show_default=True,
    help='The number of days ago',
)
@click.option(
    '-p',
    'package',
    default=None,
    show_default=True,
    help='The package name',
)
def list_tasks(user: str, tag: str, days: int, package: str):
    with Koji() as client:
        try:
            user_id = None
            if user:
                user = User(name=user, client=client)
                user_id = user.info['id']
            tasks = Tasks(tag=tag, package=package, client=client)
            tasks.get_tasks(user_id, days)
            tasks.print_tasks_table()
        except UserNotFoundException as ex:
            LOG.error(ex)


@group.command(name='get-task', help='Get Task Info')
@click.option(
    '-f',
    '--file',
    'task_file',
    default=None,
    show_default=True,
    help=f'The file of task IDs to get',
)
@click.option(
    '-e',
    '--excel',
    'excel_file',
    default=None,
    help=f'The excel file of build info , default is None',
)
@click.option(
    '-t',
    '--task',
    'tasks',
    default=None,
    multiple=True,
    show_default=True,
    help=f'Task ID',
)
@click.option(
    '--archive/--no-archive',
    default=False,
    show_default=True,
    help='If archive to excel file',
)
@click.option(
    '-d',
    '--dir',
    'save_path',
    default='./',
    show_default=True,
    help='The path to save task info excel',
)
def get_task(
    task_file: str,
    excel_file: str,
    tasks: List[str],
    archive: bool,
    save_path: str,
):
    if not any((task_file, excel_file, tasks)):
        click.echo('Use -f or -e or -t to give task ID.')
        return

    if not utils.check_path_exists([save_path]):
        return

    if not tasks:
        tasks = []

    if task_file:
        if not utils.check_file_exists([task_file]):
            return
        tasks.extend(utils.read_file(task_file))

    data = []
    with Koji() as client:
        for task_id in tasks:
            task = client.get_taskinfo(task_id)
            if not task:
                click.echo(f'Cloud not find task {task_id}.')
                return
            state = task.get('state', 0)
            reason = ''
            build_name = koji.taskLabel(task)
            if '.src.rpm' in build_name:
                package = build_name.split(',')[-1][:-1]
            else:
                package = build_name.split('/')[2].split(':')[0]
            if state == TaskState.FINISHED:
                click.echo(f'{package} finished')
            elif state == TaskState.FAILED:
                click.echo(f'{package} failed')
                reason = client.get_task_result(task_id)
                if 'Build already exists' in reason:
                    state = TaskState.BUILD_EXISTS
            elif state == TaskState.BUILDING:
                click.echo(f'{package} building')
            state_info = TaskStates.get_state(state)
            data.append(
                (
                    package,
                    state_info,
                    build_name,
                    task_id,
                    task_url(task_id),
                    reason,
                )
            )
    if not data:
        return
    if archive:
        utils.archive(save_path, 'task_info', data, task_columns)


@group.command(name='get-task-error', help='Get Task Error')
@click.argument('task', metavar='<task>')
def get_task_error(task: str):
    with Koji() as client:
        task = Task(id=task, client=client)
        task.print_task_table()
