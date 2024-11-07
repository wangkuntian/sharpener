# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'client.py'
__author__  =  'king'
__time__    =  '2022/7/6 16:06'


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
import asyncio
from typing import Dict, Optional

import click
import httpx
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

from sharpener.common import pkg
from sharpener.models.item import Package, Source, TaskState, BuildState

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

PACKAGE_MAP = {
    'python-pytest': 'pytest',
    'python-test': 'python3',
    'python-babel': 'babel',
    'python-subunit': 'subunit',
    'python-osc-lib-tests': 'python-osc-lib',
    'python-oslo-versionedobjects-tests': 'python-oslo-versionedobjects',
    'python-sphinxcontrib-rsvgconverter': 'python-sphinxcontrib'
                                          '-svg2pdfconverter',
}


def check(func):
    def wrap(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.status_code >= 400:
            return None
        return response

    return wrap


HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/103.0.0.0 Safari/537.36'
}


class Client(object):

    def __init__(self):
        self.session = httpx.Client(http2=True, headers=HEADERS)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @staticmethod
    async def _save(path, filename, response):
        total = int(response.headers['Content-Length'])
        with open(path + filename, 'wb') as f:
            with tqdm(desc=f'Download {filename}',
                      total=total,
                      ncols=120,
                      unit_scale=True,
                      unit_divisor=1024,
                      unit='B',
                      colour='#ADFF2F') as progress:
                downloaded = response.num_bytes_downloaded
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    progress.update(response.num_bytes_downloaded - downloaded)
                    downloaded = response.num_bytes_downloaded
                progress.clear()

    async def _download(self, url, path, semaphore):
        async with semaphore:
            async with httpx.AsyncClient(headers=HEADERS) as client:
                async with client.stream('GET', url) as response:
                    filename = url.split('/')[-1]
                    if response.status_code >= 400:
                        click.echo(f'Error package: {filename}')
                        print(f'Error package: {filename}')
                        return
                    await self._save(path, filename, response)

    async def download(self, urls, path):
        semaphore = asyncio.Semaphore(10)
        tasks = [
            asyncio.create_task(self._download(url, path, semaphore))
            for url in urls
        ]
        await asyncio.wait(tasks)

    @check
    def request(self, url: str, method: str = 'GET'
                ) -> Optional[httpx.Response]:
        return self.session.request(method, url)

    def get_packages(self, source: Source) -> Optional[Dict[str, Package]]:
        response = self.request(source.url)
        if not response:
            return {}
        packages = {}
        html = BeautifulSoup(response.text, 'html.parser')
        class_name = 'indexcolname' if source.name == 'centos' else 'link'
        for tr in html.find_all('td', class_=class_name):
            package = tr.a.string
            if package.startswith('Parent'):
                continue
            if package.startswith('repodata'):
                continue
            pkg.check_package(packages, package)

        return packages
