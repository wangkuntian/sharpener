# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'gerrit.py'
__author__  =  'king'
__time__    =  '2023/2/10 13:56'


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
import glob
import time
import shutil
import subprocess
from typing import Optional, Union, List

import click
from tqdm import tqdm
from git.repo import Repo
from git import RemoteProgress
from git.exc import GitCommandError
from rich import console, progress

from sharpener.common import pkg, utils
from sharpener.common.koji import Koji
from sharpener.conf import CONF, BRANCHES


@click.group(name='gerrit', help='Gerrit Commands')
def group():
    pass


class TqdmProgress(RemoteProgress):
    def __init__(self, desc=''):
        super(TqdmProgress, self).__init__()
        self.bar = tqdm(desc=desc, ncols=120)

    def update(
        self,
        op_code: int,
        cur_count: Union[str, float],
        max_count: Union[str, float, None] = None,
        message: str = "",
    ) -> None:
        self.bar.total = max_count
        self.bar.n = cur_count
        self.bar.refresh()


def _get_git_url(repo_name: str):
    return (
        f'ssh://{CONF.gerrit.admin}@{CONF.gerrit.host}:{CONF.gerrit.port}/'
        f'{repo_name}'
    )


def _get_base_command():
    command = (
        f'ssh -n -p {CONF.gerrit.port} '
        f'{CONF.gerrit.admin}@{CONF.gerrit.host}'
    )
    return command


def _clone(repo_name: str, save_path: str, branch='master') -> Optional[Repo]:
    click.echo(f'Clone repository {repo_name} from gerrit')
    repo = None
    try:
        repo = Repo.clone_from(
            _get_git_url(repo_name),
            save_path,
            branch=branch,
            progress=TqdmProgress(f'Clone {repo_name}'),
        )
        repo.git.config('user.name', CONF.gerrit.user)
        repo.git.config('user.email', CONF.gerrit.email)
    except GitCommandError as ex:
        click.echo(f'Failed to clone {repo_name}, reason is {ex}')
    finally:
        return repo


def _check_save_path(save_path: str, repo_name: str) -> Optional[str]:
    if not os.path.isdir(save_path):
        click.echo(f'Directory {save_path} not exists')
        return None
    save_path = f'{save_path}/{repo_name}'

    if os.path.isdir(save_path):
        click.echo(
            f'Directory {save_path} already exists, please delete before task'
        )
        return None
    return save_path


def _create(prefix: str, repo_name: str, parent: str = 'openstack'):
    command = (
        f'{_get_base_command()} '
        f'gerrit create-project -b master --empty-commit -p {parent} '
        f'{prefix}/{repo_name}'
    )
    subprocess.run(command.split(), check=True)
    click.echo(f'Create repository {prefix}/{repo_name} successful')


def _create_branch(prefix: str, repo_name: str, branch: str, base: str):
    command = (
        f'{_get_base_command()} '
        f'gerrit create-branch {prefix}/{repo_name} {branch} {base}'
    )
    subprocess.run(command.split(), check=True)
    click.echo(
        f'Create branch {branch} for project '
        f'{prefix}/{repo_name} successful'
    )


def _init(prefix: str, save_path: str, repo_name: str) -> int:
    save_path = _check_save_path(save_path, repo_name)
    if not save_path:
        return 1

    repo_path = f'{prefix}/{repo_name}'
    click.echo(f'Init repository {repo_path}')
    repo = _clone(repo_path, save_path)
    if not repo:
        return 1
    click.echo('Add README.md')
    with open(save_path + '/README.md', 'w+') as f:
        f.writelines(
            [
                f'# {repo_name} \n',
                f'The repository is about to build package {repo_name}. \n',
            ]
        )

    repo.git.add('README.md')
    repo.git.commit('-m', 'Add README.md')
    repo.remote().push()
    click.echo(f'Push to {repo_path}')
    return 0


def _clean(work_dir: str):
    click.echo('Clean environment')
    click.echo(f'Remove directory {work_dir}')
    shutil.rmtree(work_dir)


def _delete(prefix: str, repo_name: str):
    command = (
        f'{_get_base_command()} '
        f'delete-project delete --yes-really-delete '
        f'{prefix}/{repo_name}'
    )
    subprocess.run(command.split(), check=False)
    click.echo(f'Delete repository {prefix}/{repo_name} successful')


@group.command(name='create', help='Create Repository')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    type=click.Choice(['openstack']),
    show_default=True,
    help='The prefix of repository, like openstack/[repo].',
)
@click.argument('repo_name', metavar='<repo>')
def create(prefix: str, repo_name: str):
    _create(prefix, repo_name)


@group.command(name='create-and-init', help='Create Repository and Init')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo].',
)
@click.option(
    '-d',
    'save_path',
    default='./',
    show_default=True,
    help='The directory of the repository',
)
@click.option(
    '--clean/--no-clean',
    default=True,
    show_default=True,
    help='If clean the environment when initialization finished',
)
@click.argument('repo_name', metavar='<repo>')
def create_and_init(prefix: str, save_path: str, clean: bool, repo_name: str):
    _create(prefix, repo_name)
    result = _init(prefix, save_path, repo_name)
    if result:
        return
    if clean:
        _clean(f'{save_path}/{repo_name}')


@group.command(name='init', help='Init Repository')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo].',
)
@click.option(
    '-d',
    'save_path',
    default='./',
    show_default=True,
    help='The directory of the repository',
)
@click.option(
    '--clean/--no-clean',
    default=True,
    show_default=True,
    help='If clean the environment when initialization finished',
)
@click.argument('repo_name', metavar='<repo>')
def init(prefix: str, save_path: str, clean: bool, repo_name: str):
    result = _init(prefix, save_path, repo_name)
    if result:
        return
    if clean:
        _clean(f'{save_path}/{repo_name}')


@group.command(name='import', help='Import SRPM File To Repository')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo]',
)
@click.option(
    '-b',
    'branch',
    default=None,
    show_default=True,
    type=click.Choice(BRANCHES),
    help='The branch of repository',
)
@click.option(
    '-d',
    'save_path',
    default='./',
    show_default=True,
    help='The directory of the repository',
)
@click.option('-f', 'srpm_file', default=None, help='The srpm file to import')
@click.option('-m', 'message', default=None, help='Commit message')
@click.option(
    '--clean/--no-clean',
    default=False,
    show_default=True,
    help='If clean the environment when job finished',
)
@click.argument('repo_name', metavar='<repo>')
def import_source(
    prefix: str,
    branch: str,
    save_path: str,
    srpm_file: str,
    message: str,
    clean: bool,
    repo_name: str,
):
    if not srpm_file:
        click.echo(f'src rpm file is none')
        return

    if not branch:
        click.echo('Branch can not be null')
        return

    if not os.path.isfile(srpm_file):
        click.echo(f'File {srpm_file} not exists')
        return

    package = pkg.get_package_from_file(srpm_file)
    if not repo_name:
        repo_name = package.name

    save_path = _check_save_path(save_path, repo_name)
    if not save_path:
        return
    repo_name = f'{prefix}/{repo_name}'
    repo = _clone(repo_name, save_path)
    if not repo:
        return

    create_new_branch = True
    for ref in repo.remote().refs:
        if branch in ref.name:
            create_new_branch = False
            remote_branch = ref.name
            repo.git.checkout('-b', branch, remote_branch)
            break

    if create_new_branch:
        current = repo.create_head(branch)
        current.checkout()

    click.echo(f'Import {srpm_file} to repository {repo_name}')
    work_dir = os.path.abspath(save_path)
    srpm_file = os.path.abspath(srpm_file)
    os.chdir(work_dir)

    click.echo('Remove old files before commit')
    patch_files = glob.glob(f'{work_dir}/*.patch')
    tar_files = glob.glob(f'{work_dir}/*.tar.gz')
    spec_files = glob.glob(f'{work_dir}/*.spec')
    for file in patch_files + tar_files + spec_files:
        click.echo(f'Remove {file}')
        os.remove(file)

    click.echo(f'Extract {srpm_file} to {work_dir}')
    command = f'rpm2cpio {srpm_file} | cpio -idmv'
    subprocess.run(command, shell=True)

    if not repo.untracked_files:
        click.echo('Nothing changes')
    else:
        repo.git.add('.')
        if not message:
            message = f'Init {branch}'
        repo.git.commit('-m', message)
        origin = repo.remote()
        origin.push(
            branch, progress=TqdmProgress(f'Push to {repo_name}')
        ).raise_if_error()

    if clean:
        _clean(work_dir)


@group.command('delete', help='Delete Repository')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo]',
)
@click.argument('repo_name', nargs=-1, metavar='<repo>')
def delete(prefix: str, repo_name: str):
    _delete(prefix, repo_name)


@group.command('clone', help='Clone Repository')
@click.option(
    '-d',
    'save_path',
    default='./',
    show_default=True,
    help='The directory of the repository',
)
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo]',
)
@click.option(
    '-b',
    'branch',
    default='master',
    show_default=True,
    type=click.Choice(BRANCHES),
    help='The branch of repository',
)
@click.option('-c', 'change', default=None, help='The command after clone')
@click.option('-m', 'message', default=None, help='Commit message')
@click.option(
    '--push/--no-push',
    default=False,
    show_default=True,
    help='Push change to the repository',
)
@click.argument('repo_name', metavar='<repo>')
def clone(
    save_path: str,
    prefix: str,
    branch: str,
    change: str,
    message: str,
    push: bool,
    repo_name: str,
):
    save_path = _check_save_path(save_path, repo_name)
    if not save_path:
        return
    name = f'{prefix}/{repo_name}'
    repo = _clone(name, save_path, branch)
    if change:
        os.chdir(save_path)
        subprocess.run(change, shell=True)
        repo.git.add('.')
        if not message:
            message = f'Update {repo_name}.spec'
        repo.git.commit('-m', message)
    if push:
        origin = repo.remote()
        origin.push(
            branch, progress=TqdmProgress(f'Push to {name}')
        ).raise_if_error()


@group.command(name='build', help='Build Packages with gerrit')
@click.option(
    '-f',
    '--file',
    'packages_file',
    default=None,
    show_default=True,
    help='The file of packages to build',
)
@click.option(
    '-p',
    '--package',
    'packages',
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
    '-b',
    'branch',
    default=None,
    show_default=True,
    type=click.Choice(BRANCHES),
    help=f'The branch of repository',
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
    help='The path to save build info excel',
)
@click.option(
    '--priority',
    default=-10,
    show_default=True,
    help='Build priority',
)
@click.option(
    '--channel',
    default=None,
    show_default=True,
    help='Build channel',
)
def build_packages(
    packages_file: str,
    packages: List[str],
    build_target: str,
    branch: str,
    test: bool,
    limit: int,
    wait: int,
    archive: bool,
    save_path: str,
    priority: int,
    channel: str,
):
    if not any((packages_file, packages)):
        click.echo(f'use -f or -p to give packages')
        return
    if not branch:
        click.echo('branch must be given!')
        return

    if not utils.check_path_exists([save_path]):
        return

    client = Koji()
    client.session.login()

    if build_target != CONF.koji.tag:
        if not client.target_checked(build_target, test):
            return

    pkgs = pkg.get_packages(
        packages_file=packages_file,
        packages=packages,
        use_gerrit=True,
        branch=branch,
    )
    count = 0
    data = []
    total = len(pkgs)
    for index, package in enumerate(pkgs):
        if count >= limit:
            count = 0
            if (total - index - 1) / limit > 0:
                click.echo()
                click.echo(f'Wait {wait} seconds to continue.')
                time.sleep(wait)
        count += 1
        task_id = client.build(
            package.name,
            '',
            package.url,
            build_target,
            test,
            use_gerrit=True,
            priority=priority,
            channel=channel,
        )
        click.echo(f'Created task: {task_id}')
        click.echo(f'Task info: {client.server}/taskinfo?taskID={task_id}\n')
        if archive:
            data.append([package.name, task_id])
    client.session.logout()

    if archive:
        now = utils.get_current_datetime()
        file_name = f'{save_path}//buildInfo-{now}.xlsx'
        if test:
            file_name = f'{save_path}//buildInfo-test-{now}.xlsx'
        columns = ['Name', 'Task ID']
        utils.save_excel(file_name, data, columns)
        click.echo(f'save excel file to {file_name}')


@group.command(name='create-branch', help='Create A New Branch For A Project')
@click.option(
    '-p',
    'prefix',
    default='openstack',
    show_default=True,
    type=click.Choice(['openstack']),
    help='The prefix of repository, like openstack/[repo]',
)
@click.option(
    '-b',
    'base',
    default='master',
    show_default=True,
    type=click.Choice(['master', 'train-source', 'victoria-source']),
    help='The base of created branch',
)
@click.argument('project', metavar='<project>')
@click.argument('branch', metavar='<branch>')
def create_branch(prefix: str, base: str, project: str, branch: str):
    _create_branch(prefix, project, branch, base)
