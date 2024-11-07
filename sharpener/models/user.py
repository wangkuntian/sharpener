# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
__project__ =  'sharpener'
__file__    =  'user.py'
__author__  =  'king'
__time__    =  '2024/8/1 上午11:20'


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
from sharpener.models import base
from sharpener.common.exceptions import UserNotFoundException


class User(base.Base):
    def __init__(self, *args, **kwargs):
        self.name = ''
        self.client = None
        super().__init__(*args, **kwargs)
        self.info = self.get_user_info()

    def get_user_info(self):
        info = self.client.get_user(self.name)
        if not info:
            raise UserNotFoundException(self.name)
        return info
