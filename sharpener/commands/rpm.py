# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'rpm.py'
__author__  =  'king'
__time__    =  '2022/7/6 17:43'


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
import time
import asyncio
from typing import List
from functools import cmp_to_key

import click

from sharpener.common import pkg
from sharpener.common import utils
from sharpener.common.koji import Koji
from sharpener.common.client import Client
from sharpener.models.item import PackageStatus
from sharpener.conf import CONF, SOURCES, OPENSTACK_VERSIONS


def _check_and_create_dirs(*args) -> bool:
    for path in args:
        if not os.path.exists(path):
            click.echo(f'Creating directory {path} ...')
            try:
                os.makedirs(path)
                click.echo(f'Directory {path} created success!')
            except OSError:
                click.echo(f'Directory {path} created failed!')
                return False
    return True


@click.group(name='rpm', help='RPM Packages Commands')
def group():
    pass


@group.command(name='freeze', help='Get Latest Packages From Source')
@click.option(
    '-d',
    '--dir',
    'save_path',
    default=CONF.save_path,
    show_default=True,
    help=f'The directory to save packages',
)
@click.option(
    '-s',
    '--source',
    default=CONF.rpm.source,
    show_default=True,
    type=click.Choice(SOURCES),
    help=f'The source of packages',
)
@click.option(
    '-v',
    '--version',
    'openstack_version',
    default=CONF.rpm.openstack_version,
    type=click.Choice(OPENSTACK_VERSIONS),
    show_default=True,
    help=f'The version of openstack',
)
@click.option(
    '--cache/--no-cache',
    'use_cache',
    default=CONF.rpm.cached,
    show_default=True,
    help=f'Using Cache',
)
def freeze(
    save_path: str, source: str, openstack_version: str, use_cache: bool
) -> int:
    project = pkg.get_project(save_path, source, openstack_version)
    pkg_file = project.get_cache_file()
    save_path = project.get_pkg_file_path()
    if not _check_and_create_dirs(save_path):
        return -1
    if use_cache:
        if os.path.isfile(pkg_file):
            click.echo(f'Read packages from {pkg_file}')
            with open(pkg_file, 'r') as f:
                packages = f.readlines()
                for package in packages:
                    click.echo(package.strip())
            return 0
        else:
            click.echo(f'File {pkg_file} not exists')
    else:
        click.echo(f'Query from {project.source.host}')
        with Client() as client:
            packages = client.get_packages(project.source)
            with open(pkg_file, 'w+') as f:
                for _, package in packages.items():
                    click.echo(package.src_rpm)
                    f.write(f'{package.src_rpm}\n')
        return 0


@group.command(name='download', help='Download Packages')
@click.option(
    '-d',
    '--dir',
    'save_path',
    default=CONF.save_path,
    show_default=True,
    help=f'The directory to save downloaded packages',
)
@click.option(
    '-s',
    '--source',
    default=CONF.rpm.source,
    show_default=True,
    type=click.Choice(SOURCES),
    help=f'The source of packages',
)
@click.option(
    '-v',
    '--version',
    'openstack_version',
    default=CONF.rpm.openstack_version,
    show_default=True,
    type=click.Choice(OPENSTACK_VERSIONS),
    help=f'The version of openstack',
)
@click.option(
    '--cache/--no-cache',
    'use_cache',
    default=CONF.rpm.cached,
    show_default=True,
    help=f'Using Cache',
)
@click.option(
    '-f',
    '--file',
    'download_file',
    default=None,
    show_default=True,
    help='The file of downloaded packages',
)
@click.option(
    '-n',
    '--name',
    'names',
    default=None,
    show_default=True,
    multiple=True,
    help='Download the package of specified name',
)
def download(
    save_path: str,
    source: str,
    openstack_version: str,
    use_cache: bool,
    download_file: str,
    names: List[str],
) -> None:
    project = pkg.get_project(save_path, source, openstack_version)
    pkg_file = project.get_cache_file()
    save_path = project.get_pkg_file_path()

    if not _check_and_create_dirs(save_path):
        return

    client = Client()

    packages = pkg.get_pkgs_via_cache_or_net(use_cache, pkg_file, project)

    urls = []
    if names:
        urls = [
            f'{project.source.url}/{package.src_rpm}'
            for name, package in packages.items()
            if name in names
        ]
    elif download_file:
        if not os.path.isfile(download_file):
            click.echo(f'File {download_file} does not exist', err=True)
            return
        with open(download_file, 'r') as f:
            for name in f.readlines():
                name = name.strip()
                if name in packages:
                    urls.append(
                        f'{project.source.url}{packages[name].src_rpm}'
                    )
                elif name.endswith('.src.rpm'):
                    package_name, _ = pkg.handle_src_rpm(name)
                    if package_name in packages:
                        urls.append(
                            f'{project.source.url}'
                            f'{packages[package_name].src_rpm}'
                        )
                    else:
                        click.echo(f'Package {name} not found')
                else:
                    click.echo(f'Package {name} not found')
    else:
        urls = [
            f'{project.source.url}/{package.src_rpm}'
            for _, package in packages.items()
        ]

    if not urls:
        click.echo('Nothing download')
        return

    asyncio.run(client.download(urls, save_path))
    time.sleep(1)
    client.session.close()
    click.echo()
    click.echo(f'Save packages to {save_path}')


@group.command(name='archive', help='Archive Packages To Excel')
@click.option(
    '-d',
    '--dir',
    'save_path',
    default=CONF.save_path,
    show_default=True,
    help=f'The directory of download packages',
)
@click.option(
    '-s',
    '--source',
    default=CONF.rpm.source,
    show_default=True,
    type=click.Choice(SOURCES),
    help=f'The source of packages',
)
@click.option(
    '-v',
    '--version',
    'openstack_version',
    default=CONF.rpm.openstack_version,
    show_default=True,
    type=click.Choice(OPENSTACK_VERSIONS),
    help=f'The version of openstack',
)
@click.option(
    '-t',
    '--tag',
    default=CONF.koji.tag,
    show_default=True,
    help=f'The tag of koji',
)
@click.option(
    '--cache/--no-cache',
    'use_cache',
    default=CONF.rpm.cached,
    show_default=True,
    help=f'Using Cache',
)
def archive(
    save_path: str,
    source: str,
    openstack_version: str,
    tag: str,
    use_cache: bool,
):
    def get_tag_build(build_info):
        tags = client.list_tags(build=build_info['build_id'])
        for tg in tags:
            if tg['name'] == tag:
                return build_info
        return None

    def get_tags_build(build_info):
        tags = client.list_tags(build=build_info['build_id'])
        for tg in tags:
            if tg['name'] in CONF.koji.tags:
                return build_info
        return None

    project = pkg.get_project(save_path, source, openstack_version)
    pkg_file = project.get_cache_file()
    save_path = project.get_pkg_file_path()
    execl_file = project.get_pkg_excel_file()
    if not _check_and_create_dirs(save_path):
        return

    packages = pkg.get_pkgs_via_cache_or_net(use_cache, pkg_file, project)
    data = []
    client = Koji()
    for name, package in packages.items():
        _pkg = client.get_package(name)
        status = PackageStatus.need_created
        max_version = None
        tagged_version = None
        if not _pkg:
            data.append(
                [name, status, tagged_version, max_version, package.version]
            )
            continue
        builds = client.list_builds(package_id=_pkg['id'], state=1)
        if package.name in ('python-lesscpy', 'python-configparser'):
            builds = list(map(utils.replace, builds))
        builds.sort(key=cmp_to_key(utils.cmp), reverse=True)
        for build in builds:
            tagged_build = get_tag_build(build)
            if tagged_build:
                tagged_version = tagged_build['version']
                break
        status = PackageStatus.need_upgrade
        if tagged_version:
            if utils.greater_than(tagged_version, package.version) >= 0:
                status = PackageStatus.ok
        for build in builds:
            max_tagged_version_build = get_tags_build(build)
            if max_tagged_version_build:
                max_version = max_tagged_version_build['version']
                break
        if max_version:
            if status in (PackageStatus.need_upgrade,):
                if utils.greater_than(max_version, package.version) >= 0:
                    status = PackageStatus.need_add_tag

        data.append(
            [name, status, tagged_version, max_version, package.version]
        )
    columns = [
        'Package',
        'Status',
        'Tagged Version',
        'Maximum Version',
        'Require Version',
    ]
    utils.save_excel(execl_file, data, columns)
    click.echo(f'Save to {execl_file}')
    return 0


@group.command(name='check', help="Print Given Srpm File's Package Name")
@click.option(
    '-d',
    '--dir',
    'srpms_path',
    default=None,
    show_default=True,
    help=f'The directory of srpms to check',
)
@click.option(
    '-f',
    '--file',
    'srpms_file',
    default=None,
    show_default=True,
    help='The file of srpms to check',
)
@click.option(
    '-s',
    '--srpm',
    'srpms',
    default=None,
    show_default=True,
    multiple=True,
    help='The name of srpm to check',
)
def check_name(srpms_path: str, srpms_file: str, srpms: List[str]):
    if not any((srpms_path, srpms_file, srpms)):
        click.echo(f'use -d or -f or -s to give srpms')
        return
    if srpms_path:
        if not utils.check_path_exists([srpms_path]):
            return
        files = os.listdir(srpms_path)
        files.sort()
        for f in files:
            if f.endswith('.src.rpm'):
                name, _ = pkg.handle_src_rpm(f)
                click.echo(name)
    if srpms_file:
        if not utils.check_file_exists([srpms_file]):
            return
        with open(srpms_file, 'r+') as f:
            for line in f.readlines():
                line = line.strip()
                if line.endswith('.src.rpm'):
                    if os.path.isfile(line):
                        package = pkg.get_package_from_file(line)
                        click.echo(package.name)
                    else:
                        name, _ = pkg.handle_src_rpm(line)
                        click.echo(name)

    if srpms:
        for srpm in srpms:
            name, _ = pkg.handle_src_rpm(srpm)
            click.echo(name)
