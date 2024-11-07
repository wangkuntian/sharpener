# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'koji.py'
__author__  =  'king'
__time__    =  '2024/4/2 下午4:19'


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
import koji
import requests
import datetime
from typing import Dict, List, Optional
from koji_cli.lib import _progress_callback, unique_path

from sharpener.conf import CONF
from sharpener.models.item import TaskState


class Koji(object):
    def __init__(self):
        opts = {
            'user': CONF.koji.user,
            'password': CONF.koji.password,
        }
        self.server = f'http://{CONF.koji.host}'
        self.session = koji.ClientSession(f'{self.server}/kojihub', opts=opts)

    def __enter__(self):
        self.session.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.logout()

    def login(self):
        self.session.login()

    def logout(self):
        self.session.logout()

    def target_checked(self, target: str, test_build: bool) -> bool:
        build_target = self.session.getBuildTarget(target)
        if not build_target:
            click.echo(f'No such build target: {target}')
            return False
        dest_tag = self.session.getTag(build_target['dest_tag'])
        if not dest_tag:
            click.echo(
                f"No such destination tag: {build_target['dest_tag_name']}"
            )
            return False
        if dest_tag['locked'] and not test_build:
            click.echo(f"Destination tag {dest_tag['name']} is locked")
            return False
        return True

    def get_packages(self, tag: str) -> Dict[str, str]:
        my_tag = self.session.getTag(tag)
        packages = self.session.listPackages(tagID=my_tag['id'])
        packages = {p['package_name']: p['package_id'] for p in packages}
        return packages

    def build(
        self,
        package: str,
        path: str,
        source: str,
        build_target: str,
        test_build: bool = True,
        use_gerrit: bool = False,
        priority=-10,
        channel=None,
    ) -> str:

        if not use_gerrit:
            server_dir = unique_path('cli-build')
            click.echo(f'Upload to {server_dir}')
            self.session.uploadWrapper(
                f'{path}/{source}', server_dir, callback=_progress_callback
            )
            source = f'{server_dir}/{source}'
            click.echo()
        click.echo(package)
        if not test_build and not use_gerrit:
            pkgs = self.get_packages(build_target)
            pkg_id = pkgs.get(package, None)
            if not pkg_id:
                click.echo(f'Add package {package} to {build_target}')
                self.session.packageListAdd(
                    build_target, package, owner=CONF.koji.owner
                )

        task_id = self.session.build(
            source,
            build_target,
            opts={'scratch': test_build},
            priority=priority,
            channel=channel,
        )
        return task_id

    def rebuild(self, task_id: str) -> str:
        return self.session.resubmitTask(task_id)

    def get_taskinfo(self, task_id: str, request: bool = True) -> Dict:
        return self.session.getTaskInfo(task_id, request=request, strict=False)

    def get_tag(self, tag) -> Dict:
        return self.session.getTag(
            tag, strict=False, event=None, blocked=False
        )

    def get_task_children(
        self, task_id: str, request: bool = True
    ) -> List[Dict]:
        return self.session.getTaskChildren(
            task_id, request=request, strict=False
        )

    def read_task_root_log(self, task_id: str) -> Optional[str]:
        url = (
            f"{self.server}/kojifiles/work/tasks/"
            f"{task_id % 10000}/{task_id}/root.log"
        )
        response = requests.get(url)
        if response.status_code >= 400:
            return None
        else:
            return response.text

    def read_task_build_log(self, task_id: str) -> Optional[str]:
        url = (
            f"{self.server}/kojifiles/work/tasks/"
            f"{task_id % 10000}/{task_id}/build.log"
        )
        response = requests.get(url)
        if response.status_code >= 400:
            return None
        else:
            return response.text

    def read_task_mock_log(self, task_id: str) -> Optional[str]:
        url = (
            f"{self.server}/kojifiles/work/tasks/"
            f"{task_id % 10000}/{task_id}/mock_output.log"
        )
        response = requests.get(url)
        if response.status_code >= 400:
            return None
        else:
            return response.text

    def get_task_result(self, task_id: str) -> str:
        try:
            result = self.session.getTaskResult(task_id, raise_fault=True)
        except Exception as ex:
            reason = str(ex)
        else:
            reason = result
        return reason

    def get_task_output(self, task_id: str) -> List:
        return self.session.listTaskOutput(
            task_id, stat=False, all_volumes=False, strict=False
        )

    def get_package(self, package: str) -> Dict:
        return self.session.getPackage(package, strict=False, create=False)

    def list_tags(
        self,
        build: str = None,
        package: str = None,
        perms: bool = True,
        query_opts: Dict = None,
        pattern: str = None,
    ) -> List[Dict]:
        return self.session.listTags(
            build=build,
            package=package,
            perms=perms,
            queryOpts=query_opts,
            pattern=pattern,
        )

    def list_builds(
        self,
        package_id: str = None,
        user_id: str = None,
        task_id: str = None,
        state: int = None,
        query_opts: Dict = None,
    ) -> List[Dict]:
        return self.session.listBuilds(
            packageID=package_id,
            userID=user_id,
            taskID=task_id,
            prefix=None,
            state=state,
            volumeID=None,
            source=None,
            createdBefore=None,
            createdAfter=None,
            completeBefore=None,
            completeAfter=None,
            type=None,
            typeInfo=None,
            queryOpts=query_opts,
            pattern=None,
            cgID=None,
        )

    def check_user(self, user: str) -> (bool, Optional[Dict]):
        user = self.get_user(user)
        if not user:
            click.echo(f'user {user} not found')
            return False, None
        return True, user

    def get_user(self, user: str) -> Dict:
        return self.session.getUser(
            userInfo=user, strict=False, krb_princs=True
        )

    def list_rpms(self, build_id: str = None) -> List[Dict]:
        return self.session.listRPMs(
            buildID=build_id,
            buildrootID=None,
            imageID=None,
            componentBuildrootID=None,
            hostID=None,
            arches=None,
            queryOpts=None,
        )

    def tag_build(self, tag: str, build: str) -> str:
        return self.session.tagBuild(tag, build, force=False, fromtag=None)

    def untag_build(self, tag: str, build: str):
        self.session.untagBuild(tag, build, strict=True, force=False)

    def add_package(self, tag: str, package: str, owner: str):
        self.session.packageListAdd(
            tag,
            package,
            owner=owner,
            block=None,
            extra_arches=None,
            force=False,
            update=False,
        )

    def list_tasks(
        self,
        user_id: str = None,
        state: List[int] = TaskState.ALL,
        order: str = 'asc',
        days: int = 30,
    ) -> List[Dict]:
        now = datetime.datetime.now()
        ago = datetime.timedelta(days=days)
        opts = {
            'state': state,
            'method': 'build',
            'decode': True,
            'completeAfter': (now - ago).isoformat(),
        }

        if user_id:
            opts['owner'] = user_id

        if order == 'asc':
            query = {'order': 'completion_time'}
        else:
            query = {'order': '-completion_time'}
        return self.session.listTasks(opts=opts, queryOpts=query)

    def set_build_owner(self, build: str, owner: str):
        self.session.setBuildOwner(build, owner)

    def delete_build(self, build: str) -> bool:
        return self.session.deleteBuild(build)

    def set_task_priority(self, task, priority=5):
        self.session.setTaskPriority(task, priority, recurse=True)

    def list_tagged_builds(
        self, tag: str, package: str, owner: str = None, latest: bool = True
    ) -> List[Dict]:
        return self.session.listTagged(
            tag,
            event=None,
            inherit=False,
            prefix=None,
            latest=latest,
            package=package,
            owner=owner,
            type=None,
            strict=False,
            extra=True,
        )
