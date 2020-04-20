from automata.common.utils import wait, loading


class Modal():
    '''モーダルダイアログ の動作を制御するクラス

    レコメンド系はたぶん基本的にYesで答えておいた方が、繰り返し出現せずに楽（Noにするかちょっと迷ってる、お知らせは都度効いてくるからOFFがよさそう）
    そのままブラウザ落としたら次は聞いてこないから、エラー落ちとリランで無理やり逃げる手もある
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.worker_conf.login_id

    def turn_on(self):
        '''出現しているモーダルに Yes と返答して消す
        '''
        if self.check_dialog():
            self.turn_on_home_shortcut()
            self.turn_on_notice()

    @loading
    @wait
    def check_dialog(self):
        '''モーダルが出現しているか確認する
        '''
        dialog = self.driver.find_elements_by_xpath('//*[contains(@role, "dialog")]')
        return bool(dialog)

    @loading
    def turn_on_home_shortcut(self):
        '''[Instagramをホーム画面に追加] で、ホーム画面に追加を選択する (もう一方はキャンセルだった気が)
        '''
        check = self.driver.find_elements_by_xpath('//*[contains(text(), "ホーム画面に追加しますか？")]')
        if not check:
            return

        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        on_btn = dialog.find_element_by_xpath('.//button[contains(text(), "ホーム画面に追加")]')
        on_btn.click()

    @loading
    def turn_on_notice(self):
        '''[お知らせをオンにする] をオフにする

        ブラウザの許可が追加で必要になって、ちょっと難しそうだから「後で」を選択し続ける方がいいかも
        '''
        check = self.driver.find_elements_by_xpath('//*[contains(text(), "お知らせをオンにする")]')
        if not check:
            return

        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        off_btn = dialog.find_element_by_xpath('.//button[contains(text(), "後で")]')
        off_btn.click()

    @loading
    @wait
    def press_unfollow_at_profile_home(self):
        '''確認ダイアログのアンフォローボタン（プロフィール画面）で、アンフォローを押す
        wait 無しでも動くけど、動作が不自然だから待機を入れよう（自動生成ではなく、タッチで生成するダイアログのため）

        Conditions:
            [プロフィール] - [アンフォロー確認ダイアログ]
        '''
        dialog = self.driver.find_element_by_xpath('//*[contains(@role, "dialog")]')
        unfollow_btn = dialog.find_element_by_xpath('.//button[contains(text(), "フォローをやめる")]')
        unfollow_btn.click()
