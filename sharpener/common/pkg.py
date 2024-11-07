# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'pkg.py'
__author__  =  'king'
__time__    =  '2022/7/19 10:46'


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
from typing import Dict, Optional, List

import click

from sharpener.common import utils
from sharpener.conf import CONF
from sharpener.common.client import Client
from sharpener.models.item import Package, Source, Project


def get_args_from_srpm_file(srpm_file):
    name = '-'.join(srpm_file.split('.')[0].split('-')[:-1])
    version = srpm_file.split('-')[-2]
    return name, version


def check(src_rpm: str) -> Optional[str]:
    packages = ['boost-nowide',
                'web-assets',
                'parallel',
                'golang-x-sys',
                'golang-x-crypto',
                'golang-gopkg-yaml',
                'golang-googlecode-go-crypto',
                'golang-github-davecgh-go-spew']
    for package in packages:
        if src_rpm.startswith(package):
            return package
    return None


def handle_src_rpm(src_rpm: str):
    name = check(src_rpm)
    if name:
        version = src_rpm.split(f'{name}-')[-1].split('-')[0]
    else:
        if src_rpm.startswith('python3'):
            src_rpm = src_rpm.replace('python3', 'python')
        if src_rpm.startswith('python2'):
            src_rpm = src_rpm.replace('python2', 'python')
        name, version = get_args_from_srpm_file(src_rpm)

    return name, version


def check_package(packages: Dict[str, Package], src_rpm: str):
    name, version = handle_src_rpm(src_rpm)
    if name in packages:
        pkg = packages.get(name)
        pkg.versions.append(version)
        pkg.version = version
        pkg.src_rpm = src_rpm
    else:
        packages[name] = Package(
            name=name,
            version=version,
            versions=[version],
            src_rpm=src_rpm,
        )


def get_package(src_rpm: str, path: str = None) -> Package:
    name, version = handle_src_rpm(src_rpm)
    package = Package(
        name=name,
        version=version,
        versions=[version],
        src_rpm=src_rpm,
        path=path
    )
    return package


def get_package_from_file(file: str) -> Package:
    src_rpm = os.path.basename(file)
    path = os.path.dirname(file)
    return get_package(src_rpm, path)


def get_packages_from_cache(package_file: str) -> Optional[Dict[str, Package]]:
    packages = {}
    click.echo(f'Read packages from {package_file}')
    with open(package_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            check_package(packages, line)
    return packages


def get_pkgs_via_cache_or_net(
        use_cache: bool, pkg_file: str,
        project: Project, client: Client = None
) -> Optional[Dict[str, Package]]:
    if not client:
        client = Client()
    if use_cache:
        if not os.path.isfile(pkg_file):
            click.echo(f'{pkg_file} not exist, require directly.')
            packages = client.get_packages(project.source)
        else:
            packages = get_packages_from_cache(pkg_file)
    else:
        packages = client.get_packages(project.source)
    client.session.close()
    return packages


def get_source(source, version):
    version = f'openstack-{version}'
    sources = {
        'loongnix': Source(
            name='loongnix',
            release='lns8',
            host='pkg.loongnix.cn',
            os_version='8.4',
            openstack_version=version,
            url='https://{host}/loongnix-server/{os_version}/'
                'cloud/Source/{openstack_version}/SPackages/'),
        'centos': Source(
            name='centos',
            release='el8',
            host='vault.centos.org',
            os_version='8-stream',
            openstack_version=version,
            url='https://{host}/{os_version}/'
                'cloud/Source/{openstack_version}/'),
    }
    return sources[source]


def get_project(save_path: str, source: str, version: str):
    source = get_source(source, version)
    project = Project(save_path=save_path, source=source)
    return project


def _handle_gerrit(packages: List[Package], pkg: str, branch: str):
    if pkg.endswith('.src.rpm'):
        return
    elif '://' in pkg:
        name = pkg.split('#')[0].split('/')[-1]
        package = Package(
            name=name,
            url=pkg
        )
        packages.append(package)
    else:
        url = f'git+https://{CONF.gerrit.host}/openstack/{pkg}#origin/{branch}'
        package = Package(
            name=pkg,
            url=url
        )
        packages.append(package)


def get_packages(packages_path: str = None, packages_file: str = None,
                 packages: List[str] = None, use_gerrit: bool = False,
                 branch: str = None) -> Optional[List[Package]]:
    package_objs = []
    if packages_path:
        if utils.check_path_exists([packages_path]):
            for f in os.listdir(packages_path):
                if f.endswith('.src.rpm'):
                    click.echo(f'Found file {f}')
                    package_objs.append(
                        get_package(src_rpm=f, path=packages_path))

    if packages_file:
        if utils.check_file_exists([packages_file]):
            with open(packages_file, 'r+') as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line:
                        continue
                    if not use_gerrit:
                        if line.endswith('.src.rpm') and os.path.isfile(line):
                            click.echo(f'Found file {line}')
                            package_objs.append(get_package_from_file(line))
                    else:
                        _handle_gerrit(package_objs, line, branch)

    if packages:
        for package in packages:
            if not package:
                continue
            if not use_gerrit:
                if utils.check_file_exists([package]):
                    click.echo(f'Found file {package}')
                    package_objs.append(get_package_from_file(package))
            else:
                _handle_gerrit(package_objs, package, branch)

    return package_objs


def format_package(package: str) -> str:
    if '.' in package:
        package = package.replace('.', '-')
    if package.startswith('python3'):
        package = package.replace('python3', 'python')
    return package
