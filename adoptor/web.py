from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from automata.common.settings import WAIT_LOADING_SECONDS
from automata.common.utils import wait, loading


class Web():
    '''Webの移動を制御するクラス
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.doll_conf.login_id
        self.password = self.mediator.doll_conf.password

    def switch_to_instagram_home(self):
        '''インスタグラムのホームへ移動する
        未ログインならログインする
        '''
        self.driver.get('https://www.instagram.com/')
        self.check_logined()

    @loading
    def check_logined(self):
        '''ログイン済みでなければログインページへ飛ぶ
        '''
        login_btn = self.driver.find_elements_by_xpath('//button[contains(text(), "ログイン")]')
        if not login_btn:
            return

        # 未ログインならログインページへ遷移する
        login_btn[0].click()
        self.login()

    @loading
    @wait()
    def login(self):
        '''ログインする

        WARN:
            初回ログイン後のなんか履歴保存する？みたいなやつをさばけてないので何とかしてほしい
        '''
        id_input = self.driver.find_element_by_xpath('//input[contains(@type, "text")]')
        id_input.send_keys(self.login_id)

        pw_input = self.driver.find_element_by_xpath('//input[contains(@type, "password")]')
        pw_input.send_keys(self.password)

        login_btn = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@type, "submit")]')))
        login_btn.click()
