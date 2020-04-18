from random import random
from time import sleep
from automata.common.settings import ACTION_WAIT_SECONDS


class Adaptor():
    '''Instagramの操作を関数化するクラス
    共通処理他を管理
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.worker_conf.login_id
