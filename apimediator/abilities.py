import os
import pathlib
from datetime import datetime
from logging import getLogger, StreamHandler, FileHandler, Formatter, DEBUG
from selenium import webdriver
from automata.dao import Dao
from automata.common.settings import CHROMEDRIVER_PATH, CHROME_CACHE_SIZE, WAIT_SECONDS
from automata.common.utils import backup_ajax
from automata.adoptor.web import Web
from automata.adoptor.profile import Profile
from automata.adoptor.post import Post
from automata.adoptor.modal import Modal


class Abilities():
    '''各画面制御のコア機能を統括するMediator相当のクラス
    dollの起動処理もここで管理される
    '''

    def __init__(self, doll_id):
        # doll id をセット
        self.doll_id = doll_id

        # 実行日を取得
        self.today = datetime.now().strftime('%Y%m%d')

        # loggerを取得
        self.logger = self.create_logger()
        self.logger.debug('LOADING - BOOTING SYSTEM...')

        # DBセッションを取得
        self.dao = Dao(self.doll_id, self.today)

        # doll のコンフィグを取得
        self.doll_conf = DollConfigs(self.dao)
        self.login_id = self.doll_conf.login_id  # 良く使うのでショートカットを用意

        # webdriver を取得
        self.driver = self.create_driver()

        # 各画面制御の移譲クラスを取得
        self.web = Web(self)
        self.profile = Profile(self)
        self.post = Post(self)
        self.modal = Modal(self)

        # dollを起動中にする
        self.dao.lock_doll_status()

        self.logger.debug(f'AUTOMATA is activated. - doll id: {self.doll_id}, login id: {self.login_id}')

    def close(self):
        '''dollの終了処理
        '''
        self.dao.unlock_doll_status()
        self.dao.conn.close()
        self.driver.close()
        self.driver.quit()
        self.logger.debug(f'AUTOMATA is terminated. doll_id: {self.doll_id}, login id: {self.login_id}')

    def create_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-data-dir={self.doll_conf.browser_data_dir}')  # 同一のデータディレクトリは複数ブラウザで参照できない点に注意
        options.add_argument(f'--disk-cache-size={CHROME_CACHE_SIZE}')
        options.add_experimental_option('mobileEmulation', {'deviceName': self.doll_conf.device_name})
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
        driver.implicitly_wait(WAIT_SECONDS)  # find_element等の最大待ち時間

        # 途中でajaxをバイパス制御するため、xhrのバックアップ実行（ブラウザ側で保管）
        backup_ajax(driver)
        return driver

    def create_logger(self):
        '''ロガーを生成
        '''
        def create_dir_and_log():
            '''必要なディレクトリ, 当日のログファイルが無ければ生成

            Returns:
                str: 当日のログファイルのpath
            '''
            log_dir = f'./log/{self.doll_id}'
            ss_dir = f'./log/{self.doll_id}/screenshots'
            pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)
            pathlib.Path(ss_dir).mkdir(parents=True, exist_ok=True)
            log_path = f'{log_dir}/replay_{self.today}.log'
            if not os.path.exists(log_path):
                pathlib.Path(log_path).touch()
            return log_path

        log_path = create_dir_and_log()
        fmt = "%(asctime)s %(levelname)s [%(name)s] :%(message)s"
        handler = StreamHandler()
        handler.setFormatter(Formatter(fmt))
        handler.setLevel(DEBUG)
        file_handler = FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(Formatter(fmt))
        file_handler.setLevel(DEBUG)

        logger = getLogger(self.doll_id)
        logger.setLevel(DEBUG)
        logger.addHandler(handler)
        logger.addHandler(file_handler)
        logger.propagate = False
        return logger


class DollConfigs():
    '''DBへ保存されているdollのコンフィグを管理
    '''

    def __init__(self, dao):
        # DBからコンフィグを取得
        q_res = dao.fetch_doll_settings()
        self.login_id = q_res['login_id']
        self.password = q_res['password']
        self.doll_group = q_res['doll_group']
        self.browser_data_dir = q_res['browser_data_dir']
        self.profile_dir = q_res['profile_dir']
        self.device_name = q_res['device_name']
        self.doll_group_lake_path = q_res['doll_group_lake_path']
        self.dm_message_id = q_res['dm_message_id']
        self.hashtag_group = q_res['hashtag_group']
        self.post_per_day = q_res['post_per_day']
        self.dm_per_day = q_res['dm_per_day']
        self.fav_per_day = q_res['fav_per_day']
        self.follow_per_day = q_res['follow_per_day']
        self.unfollow_per_day = q_res['unfollow_per_day']
        self.post_per_boot = q_res['post_per_boot']
        self.dm_per_boot = q_res['dm_per_boot']
        self.fav_per_boot = q_res['fav_per_boot']
        self.follow_per_boot = q_res['follow_per_boot']
        self.unfollow_per_boot = q_res['unfollow_per_boot']
