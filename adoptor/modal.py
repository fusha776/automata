from time import sleep
from automata.common.utils import wait, loading


class Modal():
    '''モーダルダイアログ の動作を制御するクラス

    レコメンド系はたぶん基本的にYesで答えておいた方が、繰り返し出現せずに楽
    そのままブラウザ落としたら次は聞いてこないから、エラー落ちとリランで無理やり逃げる手もある
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.worker_conf.login_id

    @loading
    def check_dialog(self):
        '''モーダルが出現しているか確認する
        '''
        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        return bool(dialog)

    def turn_on_home_shortcut(self):
        '''[Instagramをホーム画面に追加] で、ホーム画面に追加を選択する
        '''
        check = self.driver.find_element_by_xpath('//*[contains(text(), "ホーム画面に追加しますか？")]')
        if not check:
            return

        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        on_btn = dialog.find_element_by_xpath('.//button[contains(text(), "ホーム画面に追加")]')
        on_btn.click()

    @loading
    def turn_on_notice(self):
        '''[お知らせをオンにする] をオンにする
        '''
        check = self.driver.find_element_by_xpath('//*[contains(text(), "お知らせをオンにする")]')
        if not check:
            return

        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        on_btn = dialog.find_element_by_xpath('.//button[contains(text(), "オンにする")]')
        on_btn.click()
