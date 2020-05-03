from datetime import datetime
from selenium import webdriver
from automata.common.settings import CHROMEDRIVER_PATH, CHROME_CACHE_SIZE, WAIT_SECONDS
from automata.common.utils import backup_ajax
from automata.common.utils import generate_logger
from automata.adoptor.web import Web
from automata.adoptor.profile import Profile
from automata.adoptor.post import Post
from automata.adoptor.modal import Modal
from automata.adoptor.search import Search

from automata.repository.action_counters import ActionCountersRepository
from automata.repository.doll_settings import DollSettingsRepository
from automata.repository.doll_status import DollStatusRepository
from automata.repository.following_status import FollowiingStatusRepository


class Abilities():
    '''各画面制御のコア機能を統括するMediator相当のクラス
    dollの起動処理もここで管理される
    '''

    def __init__(self, doll_id, conn, today):
        self.doll_id = doll_id
        self.today = today
        self.conn = conn

    def setup_doll(self):
        '''Doll向けの機能をセットアップする
        '''
        self.action_counters_repository = ActionCountersRepository(self.conn, self.doll_id, self.today)
        self.doll_settings_repository = DollSettingsRepository(self.conn, self.doll_id, self.today)
        self.doll_status_repository = DollStatusRepository(self.conn, self.doll_id, self.today)
        self.following_status_repository = FollowiingStatusRepository(self.conn, self.doll_id, self.today)

        # loggerを取得
        self.logger = generate_logger(self.doll_id, self.today)
        self.logger.debug('LOADING - BOOTING SYSTEM...')

        # doll のコンフィグを取得
        self.doll_conf = DollConfigs(self.doll_settings_repository)
        self.login_id = self.doll_conf.login_id  # 良く使うのでショートカットを用意

        # webdriver を取得
        self.driver = self.create_driver()

        # 各画面制御の移譲クラスを取得
        self.activate_screen_actions()

        # dollを起動中にする
        self.doll_status_repository.lock_doll()
        self.logger.debug(f'AUTOMATA is activated. - doll id: {self.doll_id}, login id: {self.login_id}')

    def activate_screen_actions(self):
        '''画面制御系のクラスを生成する
        '''

        self.modal = Modal(self, self.action_counters_repository, self.doll_status_repository)
        self.post = Post(self, self.action_counters_repository)
        self.web = Web(self)
        self.profile = Profile(self, self.action_counters_repository, self.following_status_repository)
        self.search = Search(self, self.action_counters_repository)

    def close(self):
        '''Dollの終了処理
        '''
        # driverを真っ先に落とす. profileがロックされてると次の起動も失敗する.
        self.driver.quit()

        self.doll_status_repository.unlock_doll()
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


class DollConfigs():
    '''DBへ保存されているdollのコンフィグを管理
    '''

    def __init__(self, doll_settings_repository):
        # DBからコンフィグを取得
        q_res = doll_settings_repository.fetch_doll_settings()
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
