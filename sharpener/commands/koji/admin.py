# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'admin.py'
__author__  =  'king'
__time__    =  '2024/4/1 下午3:03'


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
from typing import List

import koji
import click

from sharpener.conf import CONF
from sharpener.common.koji import Koji
from sharpener.commands.koji import group, task_url


@group.command(name='rebuild', help='Rebuild Packages')
@click.option(
    '--privileged',
    'privileged',
    default=True,
    show_default=True,
    is_flag=True,
    help='Privileged rebuild',
)
@click.argument('tasks', nargs=-1, metavar='<task>')
def rebuild(privileged: bool, tasks: List[str]):
    with Koji() as client:
        for task in tasks:
            click.echo(f'Old task url: {task_url(task)}')
            new_task = client.rebuild(task)
            click.echo(f'New task url: {task_url(new_task)}')
            if privileged:
                try:
                    client.set_task_priority(new_task)
                    click.echo(f'Set new task {new_task} to privileged')
                except koji.ActionNotAllowed as ex:
                    click.echo(f'Set task priority error: {ex}')


@group.command(name='delete-build', help='Delete Build')
@click.argument('build', metavar='<build>')
def delete_build(build: str):
    with Koji() as client:
        result = client.delete_build(build)
        click.echo(f'Deleted build {build}: {result}')


@group.command(name='tag-build', help='Add Tag To Builds')
@click.option(
    '-t',
    '--tag',
    default=CONF.koji.tag,
    show_default=True,
    help=f'The tag to add',
)
@click.argument('builds', nargs=-1, metavar='<build>')
def tag_builds(tag: str, builds):
    with Koji() as client:
        for build in builds:
            try:
                result = client.tag_build(tag, build)
                click.echo(result)
            except koji.TagError as ex:
                click.echo(ex, err=True)
                package = '-'.join(build.split('.')[0].split('-')[:-1])
                client.add_package(tag, package, owner=CONF.koji.user)
                result = client.tag_build(tag, build)
                click.echo(result)


@group.command(name='untag-build', help='Untag Builds')
@click.option(
    '-t',
    '--tag',
    default=CONF.koji.tag,
    show_default=True,
    help=f'The tag to remove',
)
@click.argument('builds', nargs=-1, metavar='<build>')
def untag_builds(tag: str, builds):
    with Koji() as client:
        for build in builds:
            client.untag_build(tag, build)


@group.command(name='set-build-owner', help='Set Build Owner')
@click.option(
    '-u',
    '--user',
    default=CONF.koji.user,
    show_default=True,
    help=f'The user to set',
)
@click.argument('builds', nargs=-1, metavar='<build>')
def build_owner(user: str, builds):
    if not builds:
        click.echo('Require at least 1 argument: one or more build', err=True)
        return
    with Koji() as client:
        for build in builds:
            client.set_build_owner(build, user)
