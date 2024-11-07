# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'spec.py'
__author__  =  'king'
__time__    =  '2023/6/1 下午2:53'


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
import os
import click
import datetime

from sharpener.conf import CONF


@click.group(name='spec', help='Spec Commands')
def group():
    pass


def get_changelog(
    name: str,
    email: str,
    version: str,
    release: str,
    micro_version: str,
    msg: str,
):
    now = datetime.datetime.now().strftime('%a %b %d %Y')
    return (
        f'* {now} {name} <{email}> - '
        f'{version}-{release}.{micro_version}\n',
        f'- {msg}\n\n',
    )


@group.command(name='update', help='Update Spec File')
@click.option(
    '-c',
    '--changelog',
    'msg',
    default=None,
    show_default=True,
    help='The changelog message',
)
@click.option(
    '-v',
    '--version',
    'version',
    default=None,
    show_default=True,
    help='The version of spec',
)
@click.option(
    '-r',
    '--release',
    'release',
    default=None,
    show_default=True,
    help='The release of spec',
)
@click.option(
    '-m',
    '--micro-version',
    'micro_version',
    default=None,
    show_default=True,
    help='The micro-version of spec',
)
@click.option(
    '-n',
    '--name',
    'name',
    default=CONF.gerrit.user,
    show_default=True,
    help=f'User name',
)
@click.option(
    '-e',
    '--email',
    'email',
    default=CONF.gerrit.email,
    show_default=True,
    help=f'User email',
)
@click.argument('spec', metavar='<spec>')
def update_spec(
    msg: str,
    version: str,
    release: str,
    micro_version: str,
    name: str,
    email: str,
    spec: str,
):
    if not os.path.isfile(spec):
        click.echo(f'{spec} does not exist')
        return
    old_version = old_release = old_micro_version = None
    with open(spec, 'r+') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if line.startswith('Version'):
                line = line.strip().replace(' ', '')
                old_version = line.split(':')[-1]
                if version:
                    click.echo(
                        f'old version is {old_version}, '
                        f'new version is {version}'
                    )
                    old_version = version
                    lines[index] = f'Version: {old_version}'
                continue

            if line.startswith('Release'):
                line = line.strip().replace(' ', '').split(':')[-1]
                if '%{?dist}' in line:
                    temp = line.split('%{?dist}')
                    old_release, old_micro_version = temp

                    if old_release.endswith('.'):
                        old_release = old_release[:-1]
                    if old_micro_version.startswith('.'):
                        old_micro_version = old_micro_version[1:]
                    if release:
                        click.echo(
                            f'old release is {release}, '
                            f'new release is {release}'
                        )
                        old_release = release

                    if micro_version:
                        click.echo(
                            f'old micro version is {old_micro_version}, '
                            f'new micro version is {micro_version}'
                        )
                        old_micro_version = micro_version

                    if release or micro_version:
                        lines[index] = (
                            f"Release: {old_release}"
                            + '%{?dist}'
                            + f".{old_micro_version} \n"
                        )
                else:
                    old_release = line
                    if release:
                        click.echo(
                            f'old release is {release}, '
                            f'new release is {release}'
                        )
                        old_release = release
                        lines[index] = f'Release: {old_release}'

                    if micro_version:
                        click.echo('Spec does not have micro version')

                continue

            if line.startswith('%changelog'):
                if not msg:
                    break
                changelog_1, changelog_2 = get_changelog(
                    name,
                    email,
                    old_version,
                    old_release,
                    old_micro_version,
                    msg,
                )
                lines.insert(index + 1, changelog_1)
                lines.insert(index + 2, changelog_2)
                break

        with open(f'{spec}', 'w+') as w:
            w.writelines(lines)
