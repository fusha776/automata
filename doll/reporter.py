import os
from datetime import datetime
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from automata.common.settings import WAIT_LOADING_SECONDS
from automata.common.settings import REPORTING_DIR
from automata.common.utils import loading, wait
from automata.common.utils import create_logger, create_driver
from automata.repository.reporter_settings import ReporterSettingsRepository

CHROME_LINE_EXTENTION_PATH = 'chrome-extension://ophjlpahpchlmihnnnihgmmeilfjmjjc/index.html'


class LineReporter():
    '''Chrome拡張機能版 LINE経由で結果報告をする

    LINE Developers からAPIでやった方が堅い気はするけど、
    チャンネルの友だち追加を依頼しないといけない等あるのでとりあえずWeb経由にする

    報告先がLINEだけじゃなく複数になったら、Dollの具象クラスに半分移譲することになりそう

    多重投稿を避けるために排他制御が必要
    雑だけど、簡単なのでとりあえずファイルロックで対処する
    '''

    def __init__(self, conn, today):
        self.conn = conn
        self.today = today
        self.doll_id = 'reporter'
        self.logger = create_logger(self.doll_id, self.today)
        self.doll_settings_repository = ReporterSettingsRepository(self.conn, 'reporter', self.today)
        self.conf = self.doll_settings_repository.load_reporter_settings()
        self.activate_driver()

    def activate_driver(self):
        '''Driverを起動する
        '''
        self.driver = create_driver(self.conf['browser_data_dir'], None)

    def close(self):
        # driverを真っ先に落とす. profileがロックされてると次の起動も失敗する.
        self.driver.quit()

    @loading
    @wait()
    def switch_to_home(self):
        '''詳細はログイン履歴が消えてから確認しよう
        '''
        self.driver.get(CHROME_LINE_EXTENTION_PATH)

    @loading
    @wait()
    def login(self):
        '''Chrome版LINEへログインする
        '''
        id_input = self.driver.find_element_by_id('line_login_email')
        pwd_input = self.driver.find_element_by_id('line_login_pwd')

        id_input.clear()
        id_input.send_keys(self.conf['login_id'])
        pwd_input.send_keys(self.conf['password'])

        login_btn = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.ID, 'login_btn')))
        login_btn.click()

    @loading
    @wait()
    def open_destination_room(self, dst_room):
        '''目的のルームを開く
        '''
        search_input = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.ID, '_search_input')))
        search_input.send_keys(dst_room)

        room_btn = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, f'//li[contains(@title, "{dst_room}")]')))
        room_btn.click()

        # ページ遷移をuntilだけで待機しようとすると、遷移前のelementを回収して not attach err を出すのでload待ちが必要
        sleep(5)

        # 対象のルームが開いたことを簡易チェック。遷移できてない場合はエラーが発生
        _ = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, f'//*[contains(text(), "{dst_room}")]')))

    def send_massage(self, input_el, msg):
        '''改行のたびに送信しないように調整しながら、メッセージ入力欄に文字列を埋め込む
        非同期処理のメッセージ送信完了を待つのに、イベント検知が難しいのでsleepを長めに設定して乗り切る
        elementの個数の変化とかで見ても良いのかもしれないけれども
        '''
        for part in msg.split('\n'):
            input_el.send_keys(part)
            ActionChains(self.driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.SHIFT).key_up(Keys.ENTER).perform()

        input_el.send_keys(Keys.ENTER)
        sleep(10)

    @loading
    @wait()
    def _report(self, doll_group):
        '''対象の部屋に結果を送信する
        '''
        # 送信済みならskip
        sent_logs = self.doll_settings_repository.load_history(doll_group, self.today)
        if sent_logs:
            self.logger.info(f'{doll_group} は既に送信済みです. channel: {sent_logs["channel"]}, dst: {sent_logs["destination"]}')
            return

        result_path = f'{REPORTING_DIR}/{self.today}/{doll_group}_{self.today}.txt'
        if not os.path.exists(result_path):
            self.logger.error(f'報告用ファイルが生成されていません {doll_group}')
            raise Exception

        with open(result_path, 'r+', encoding='utf8') as f:
            report_msg = f.read()
            dst_room = self.doll_settings_repository.load_report_mappings(doll_group)['destination']
            self.open_destination_room(dst_room)
            msg_input = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
                EC.element_to_be_clickable((By.ID, '_chat_room_input')))
            self.send_massage(msg_input, report_msg)

            # 送信済み登録する
            self.doll_settings_repository.register_sent_report(doll_group, 'LINE', dst_room)
            self.logger.info(f'集計レポートを送信. {doll_group}')

    @loading
    @wait()
    def _pre_send(self, doll_group):
        '''監視用に結果ファイルを事前送信する
        '''
        result_path = f'{REPORTING_DIR}/{self.today}/{doll_group}_{self.today}.txt'
        if not os.path.exists(result_path):
            self.logger.error(f'報告用ファイルが生成されていません {doll_group}')
            raise Exception

        with open(result_path, 'r+', encoding='utf8') as f:
            report_msg = f'プレチェック: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n' + f.read()
            self.open_destination_room(self.conf['monitor_room'])
            msg_input = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
                EC.element_to_be_clickable((By.ID, '_chat_room_input')))
            self.send_massage(msg_input, report_msg)
        self.logger.info(f'結果ファイルを監視部屋へ事前送信. {doll_group}')

    @loading
    @wait()
    def _monitor(self, doll_group):
        '''監視用に途中経過を送信する
        '''
        interim_path = f'{REPORTING_DIR}/{self.today}/{doll_group}_interim.txt'
        if not os.path.exists(interim_path):
            return

        with open(interim_path, 'r+', encoding='utf8') as f:
            report_msg = f'途中経過: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n' + f.read()
            self.open_destination_room(self.conf['monitor_room'])
            msg_input = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
                EC.element_to_be_clickable((By.ID, '_chat_room_input')))
            self.send_massage(msg_input, report_msg)
        self.logger.info(f'途中経過を監視部屋へ送信. {doll_group}')

    def report(self):
        '''結果レポートを一括送信する
        '''
        self.switch_to_home()
        self.login()
        self._report('nine_japan')

    def monitor(self):
        '''途中経過を一括送信する
        '''
        self.switch_to_home()
        self.login()
        self._monitor('nine_japan')

    def pre_send(self):
        '''途中経過を一括送信する
        '''
        self.switch_to_home()
        self.login()
        self._pre_send('nine_japan')
