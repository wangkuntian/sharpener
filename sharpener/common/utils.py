# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'utils.py'
__author__  =  'king'
__time__    =  '2022/7/19 10:32'


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
import random
import string
import pandas as pd
from typing import List
from datetime import datetime
from pandas import ExcelWriter, DataFrame

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def get_current_datetime():
    return datetime.now().strftime(DATETIME_FORMAT)


def check_file_and_path(
    files: List[str] = None, paths: List[str] = None
) -> bool:
    return check_path_exists(paths) and check_file_exists(files)


def check_path_exists(paths: List[str]) -> bool:
    for path in paths:
        if not os.path.exists(path):
            click.echo(f'Directory {path} not exists.')
            return False
    return True


def check_file_exists(files: List[str]) -> bool:
    for file in files:
        if not os.path.isfile(file):
            click.echo(f'File {file} not exists.')
            return False
    return True


def save_excel(
    file_path: str,
    data: List[List[str]],
    columns: List[str],
    sheet_name: str = 'sheet1',
) -> None:
    with ExcelWriter(file_path) as writer:
        DataFrame(data, columns=columns).to_excel(
            writer, sheet_name=sheet_name, index=False
        )


def archive(save_path: str, file_name: str, data: List, columns: List[str]):
    now = get_current_datetime()
    excel_file_name = f'{save_path}/{file_name}-{now}.xlsx'
    click.echo(f'Save excel file to {excel_file_name}')
    save_excel(excel_file_name, data, columns=columns)


def read_excel(
    file_path: str, columns: List[str], sheet_name: int = 0
) -> DataFrame:
    data = pd.read_excel(file_path, sheet_name=sheet_name, names=columns)
    return data


def read_file(file_path: str) -> List[str]:
    data = []
    with open(file_path, 'r+') as f:
        lines = f.readlines()
        for line in lines:
            data.append(line.strip())
        return data


def greater_than(v1: str, v2: str) -> int:
    vs_1 = v1.split('.')
    vs_2 = v2.split('.')
    length = len(vs_1) if len(vs_1) <= len(vs_2) else len(vs_2)
    for i in range(length):
        if int(vs_1[i]) == int(vs_2[i]):
            pass
        elif int(vs_1[i]) < int(vs_2[i]):
            return -1
        elif int(vs_1[i]) > int(vs_2[i]):
            return 1
    if len(vs_1) == len(vs_2):
        return 0
    if len(vs_1) > len(vs_2):
        return 1
    return -1


def cmp(build1, build2):
    return greater_than(build1['version'], build2['version'])


def replace(build):
    build['version'] = build['version'].replace('j', '')
    build['version'] = build['version'].replace('b2', '')
    return build


# 定义一个函数生成随机字符串
def generate_random_string(length: int) -> str:
    # 字母和数字的组合
    letters_and_digits = string.ascii_letters + string.digits
    # 随机选择指定长度的字符
    random_string = ''.join(
        random.choice(letters_and_digits) for i in range(length)
    )
    return random_string
