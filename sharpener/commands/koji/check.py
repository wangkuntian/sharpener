# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'check.py'
__author__  =  'king'
__time__    =  '2024/4/1 下午1:22'


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
import click
from typing import List

from sharpener.conf import CONF
from sharpener.common import utils
from sharpener.common.koji import Koji
from sharpener.commands.koji import group
from sharpener.models.item import TaskState


@group.command(
    name='check-package', help='Check the package if it has been built'
)
@click.option(
    '-f',
    '--file',
    'pkgs_file',
    default=None,
    show_default=True,
    help='The file of packages to get builds',
)
@click.option(
    '-p',
    '--package',
    'pkgs',
    default=None,
    multiple=True,
    show_default=True,
    help='The package to get builds',
)
@click.option(
    '-t',
    '--tag',
    'tags',
    default=CONF.koji.tags,
    multiple=True,
    show_default=True,
    help=f'The tag of build',
)
def check_package(pkgs_file: str, pkgs: List[str], tags: List[str]):
    if not any((pkgs_file, pkgs)):
        click.echo('use -f or -p to give packages')
        return
    with Koji() as client:
        packages = []
        if pkgs_file:
            if not utils.check_file_exists([pkgs_file]):
                return
            packages.extend(utils.read_file(pkgs_file))
        else:
            packages = pkgs

        for package in packages:
            click.echo(f'checking {package}')
            pkg_info = client.get_package(package)
            if not pkg_info:
                click.echo(f'Package {package} not found')
                return
            builds = client.list_builds(package_id=pkg_info['id'])
            for build_info in builds:
                task_id = build_info['task_id']
                task = client.get_taskinfo(task_id)
                state = task.get('state', 0)
                if state == TaskState.FINISHED:
                    build_tags = client.list_tags(build=build_info['build_id'])
                    build_tags = [t['name'] for t in build_tags]
                    if set(tags) & set(build_tags):
                        click.echo(f'{package} has been built')
                        break
            else:
                click.echo(f'{package} does not have been built')

            click.echo()
