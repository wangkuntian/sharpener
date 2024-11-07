# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'build.py'
__author__  =  'king'
__time__    =  '2024/4/1 上午11:14'


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
import time
import click
from typing import List

from sharpener.common import pkg
from sharpener.common.exceptions import (
    UserNotFoundException,
    PackageNotFoundException,
)
from sharpener.conf import CONF
from sharpener.common.log import LOG
from sharpener.common.koji import Koji
from sharpener.commands.koji import group
from sharpener.models.package import Package
from sharpener.models.user import User


@group.command(name='build', help='Build Packages')
@click.option(
    '-d',
    '--dir',
    'pkg_path',
    default=None,
    show_default=True,
    help=f'The directory of packages to build',
)
@click.option(
    '-f',
    '--file',
    'pkg_file',
    default=None,
    show_default=True,
    help='The file of packages to build',
)
@click.option(
    '-p',
    '--package',
    'pkgs',
    default=None,
    show_default=True,
    multiple=True,
    help='The package to build',
)
@click.option(
    '-t',
    '--tag',
    'build_target',
    default=CONF.koji.tag,
    show_default=True,
    help=f'The tag to add',
)
@click.option(
    '--test/--no-test',
    default=CONF.koji.test_build,
    show_default=True,
    help=f'Test build',
)
@click.option(
    '--limit',
    default=20,
    show_default=True,
    help='Limit of packages build one time',
)
@click.option(
    '--wait',
    default=900,
    show_default=True,
    help='Wait to build packages',
)
def build_pkg(
    pkg_path: str,
    pkg_file: str,
    pkgs: List[str],
    build_target: str,
    test: bool,
    limit: int,
    wait: int,
):
    if not any((pkg_path, pkg_file, pkgs)):
        click.echo(f'use -d or -f or -p to give packages')
        return

    packages = pkg.get_packages(pkg_path, pkg_file, pkgs)

    with Koji() as client:

        if build_target != CONF.koji.tag:
            if not client.target_checked(build_target, test):
                return
        count = 0
        for package in packages:
            if count >= limit:
                count = 0
                time.sleep(wait)
            count += 1
            task_id = client.build(
                package.name, package.path, package.src_rpm, build_target, test
            )
            click.echo(f'Created task: {task_id}')
            click.echo(f'Task info: {client.server}/taskinfo?taskID={task_id}')


@group.command(name='list-builds', help='List Builds')
@click.option(
    '-t',
    '--tag',
    default=None,
    show_default=True,
    help=f'Build tag',
)
@click.option(
    '-u', '--user', default=None, show_default=True, help='Build user'
)
@click.argument('package', metavar='<package>')
def list_builds(tag: str, user: str, package: str):
    with Koji() as client:
        try:
            user_id = None
            if user:
                user = User(name=user, client=client)
                user_id = user.info['id']
            package = Package(name=package, client=client)
            if tag:
                package.get_tagged_builds(tag, user_id, False)
            else:
                package.get_builds(user_id)
            package.print_builds_table()
        except UserNotFoundException as ex:
            LOG.error(ex)
        except PackageNotFoundException as ex:
            LOG.error(ex)
