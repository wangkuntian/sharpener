# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'gerrit.py'
__author__  =  'king'
__time__    =  '2024/4/2 下午3:43'


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


class Worker(object):
    def __init__(self, user: str, tag: str, branch: str,
                 parent_tag: str = None,
                 built_packages: List[str] = None):
        self.client = Koji()
        self.checking_packages = set()
        self.need_build_packages = set()
        self.checked_packages = {'python3', 'systemd', 'git', 'python-py'}
        self.failed_packages = set()
        self.not_found = set()
        self.build_requires = []
        self.user = user
        self.tag = tag
        self.parent_tag = parent_tag
        self.branch = branch
        self.built_packages = built_packages

    def init_need_build_packages(self):
        path = f'/etc/sharpener/{CONF.koji.need_build_packages_file}'
        if not os.path.isfile(path):
            return
        with open(path, 'r+') as f:
            lines = f.readlines()
            for line in lines:
                click.echo(f"line: {line}")

    def get_package_build_requires(self, package: str) -> Optional[List[str]]:
        url = f'https://gerrit-dev.uniontech.com/plugins/gitiles/' \
              f'openstack/{package}/+/refs/heads/{self.branch}/{package}.spec'
        response = requests.get(url, verify=False)
        if response.status_code >= 400:
            return []
        build_requires = []
        root = BeautifulSoup(response.text, 'html.parser')
        lines = root.find_all('tr', class_='FileContents-line')
        for index, line in enumerate(lines):
            spans = line.find(id=f'{index + 1}').find_all('span')
            value = ''.join(list(map(lambda x: x.string, spans)))
            if value.startswith('#'):
                continue
            if value.startswith('BuildRequires'):
                if '>' in value or '=' in value:
                    require = value.split(' ')[-3]
                else:
                    value = value.replace('\t', ' ')
                    require = value.split(' ')[-1]

                if require.startswith('/usr/bin'):
                    continue

                if '%{pyver}' in require:
                    require = require.replace('%{pyver}', '3')

                if '%{python3_pkgversion}' in require:
                    require = require.replace('%{python3_pkgversion}', '3')

                if require.startswith('python3'):
                    require = require.replace('python3', 'python')

                if require.startswith('python2'):
                    require = require.replace('python2', 'python')

                if require.startswith('python-devel'):
                    require = 'python3'
                if require:
                    if require in PACKAGE_MAP:
                        build_requires.append(PACKAGE_MAP[require])
                    else:
                        build_requires.append(require)
        # click.echo(f'Package {package} build requires: {build_requires}')
        return list(set(build_requires))

    def _check_package_build(self, package: str, tag: str,
                             user: str = None) -> bool:
        builds = self.client.list_builds(package_id=package,
                                         user_id=user,
                                         state=BuildState.COMPLETE,
                                         query_opts={'limit': 1})
        passed = False
        if builds:
            build_info = builds[0]
            build_tags = self.client.list_tags(build=build_info['build_id'])
            build_tags = [t['name'] for t in build_tags]
            if tag in build_tags:
                passed = True
        # click.echo(f"{package}'s {tag} check package build {passed}")
        return passed

    def check_package_build(self, package: str) -> bool:
        return self._check_package_build(package, self.tag, self.user)

    def check_other_package_build(self, package: str) -> bool:
        return self._check_package_build(package, 'kongzi-mips')

    def check(self, package: str, first_run=True) -> bool:
        if package in self.built_packages or package in self.checked_packages:
            # click.echo(f'Package {package} has already been built')
            return True
        if package in self.failed_packages:
            return False
        if package in self.checking_packages:
            click.echo('Circular Reference')
            return False
        self.checking_packages.add(package)
        package_info = self.client.get_package(package)
        if not package_info:
            # click.echo(f'Package {package} not found')
            self.not_found.add(package)
            return False
        if not first_run:
            if self.check_package_build(package):
                self.checked_packages.add(package)
                return True
            elif self.check_other_package_build(package):
                self.checked_packages.add(package)
                return True
        build_requires = self.get_package_build_requires(package)
        results = []
        for i in build_requires:
            # click.echo(f'Checking package {i}')
            result = self.check(i, first_run=False)
            results.append(result)
        if results and all(results):
            # click.echo(f'Package {package} passed')
            self.checked_packages.add(package)
            return True
        else:
            # click.echo(f'Package {package} not passed')
            self.failed_packages.add(package)
            return False
