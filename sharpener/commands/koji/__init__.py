# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  '__init__.py.py'
__author__  =  'king'
__time__    =  '2024/4/1 上午11:13'


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

from sharpener.conf import CONF


@click.group(name='koji', help='Koji Commands')
def group():
    pass


def task_url(task_id: str) -> str:
    return f"http://{CONF.koji.host}/taskinfo?taskID={task_id}"
