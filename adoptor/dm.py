from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from automata.common.settings import WAIT_LOADING_SECONDS
from automata.common.utils import wait, loading


class DirectMessage():
    '''投稿関連の動作を制御するクラス
    '''

    def __init__(self, mediator, action_counters_repository, dm_histories_repository):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.doll_conf.login_id

        self.action_counters_repository = action_counters_repository
        self.dm_histories_repository = dm_histories_repository

    @loading
    @wait()
    def switch_to_dm_home(self):
        '''[DMトップ]へ遷移する
        モーダルが表示される場合があるので消す
        '''
        self.driver.get(f'https://www.instagram.com/direct/inbox/')
        self.mediator.modal.turn_off_app_recommend_in_dm()

    @loading
    @wait()
    def switch_to_dm_window(self, insta_id):
        '''特定アカとのDM画面へ遷移する

        Args:
            insta_id (str): インスタID

        Returns:
            bool: 遷移に成功 -> True

        Conditions:
            [DMトップ]
        '''
        # 対象アカとのメッセージ画面へ遷移
        user_menu_btn = self.driver.find_elements_by_xpath(f'//*[contains(text(), "{insta_id}")]')
        if not user_menu_btn:
            self.mediator.logger.error(f'DM画面から対象アカを見つけられませんでした: {insta_id}')
            return False
        user_menu_btn[0].click()
        return True

    @loading
    @wait()
    def send_dm(self, insta_id, msg):
        '''ダイレクトメッセージを送信する

        Returns:
            bool: dm送信に成功 -> True

        Conditions:
            [DMトップ]
        '''
        # 入力Boxを取得
        self.switch_to_dm_window(insta_id)
        message_input = self.driver.find_element_by_xpath('//div/textarea')  # div無しだと、隠れたtextareaが取得される
        message_input.send_keys(msg)  # instagramはEnterで送信にならず、送信ボタンのタッチで送信

        # テキストを入力すると送信ボタンが出現
        sleep(1)
        send_btn = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "送信")]')))
        send_btn.click()
        sleep(3)  # 送信のajax通信があるだろうからここでwait

        # DB更新
        self.dm_histories_repository.add_dm_sending(self.login_id, insta_id, msg)
        self.action_counters_repository.increase_action_count({'dm': 1})
        return True

    @loading
    @wait()
    def _read_reply(self):
        '''相手からのダイレクトメッセージを取得する
        だいぶ層が深くてマジックナンバーになってるけど、画像投稿と文章投稿が混在するのでこれ以外難しい

        Returns:
            str[]: 画面上に取得できた返信メッセージ

        Conditions:
            [DMトップ] - [ユーザDM]
        '''

        all_msgs = self.driver.find_elements_by_xpath('//span')
        if not all_msgs:
            return []

        # 右寄せに作用しているclassの無いmsgだけに絞る（divに付随するclassの数で判定）
        new_msgs = []
        for msg in all_msgs:
            position_class = msg.find_element_by_xpath('./../../../../../../..')
            class_cnt = position_class.get_attribute('class')
            class_cnt = class_cnt.split(' ')
            class_cnt = [c for c in class_cnt if c]  # スペースが複数続いているためブランクを弾いて、中身のあるクラス数に絞る
            if len(class_cnt) == 1:  # 右寄せが無い場合の該当divのクラス数: 1
                print('取得msg:', msg.text)
                new_msgs.append(msg.text)
        return new_msgs

    @loading
    @wait()
    def register_dm(self, insta_id):
        '''相手からの新規ダイレクトメッセージをDBへ登録する

        * 日時チェックは難しいので省略し、メッセージ本文だけでユニークチェックする
        * 画面スクロールはせず、デフォルト表示以上は探索しない

        Args:
            insta_id (str): DMを確認するインスタID

        Returns:
            int: 新規登録したメッセージ件数

        Conditions:
            [DMトップ]
        '''

        # 直近50件の返信を取得する ※未確認だけど、これ以上は画面にデフォルト表示されないと思う
        sent_msgs = self.dm_histories_repository.load_messages(insta_id, self.login_id, 50)
        if sent_msgs:
            sent_msgs = [m['message'] for m in sent_msgs]
        else:
            sent_msgs = []

        # DM返信を取得
        self.switch_to_dm_window(insta_id)
        reply_msgs = self._read_reply()

        registered_cnt = 0
        for msg in reply_msgs:
            if msg in sent_msgs:
                # 登録済ならskip
                continue
            self.dm_histories_repository.add_dm_sending(insta_id, self.login_id, msg)
            registered_cnt += 1
        return registered_cnt

    @loading
    @wait()
    def read_estimated_insta_ids(self, scroll_cnt=0):
        '''DM画面に表示されているインスタIDを上から順番に取得する

        * 新着の会話があった順に画面に並ぶはず
        * テキストから直接抜き出せるタグは層が深いので、altを整形して抽出する

        Args:
            scroll_cnt (int): 画面をスクロールする回数

        Returns:
            str[]: 新規登録順のインスタID

        Conditions:
            [DMトップ]
        '''
        insta_ids = []
        for _ in range(scroll_cnt + 1):
            icons = self.driver.find_elements_by_xpath('//img')
            for icon in icons:
                name = icon.get_attribute('alt')
                name = name.split('の')[0].strip()  # alt=xxxxのプロフィール写真 になってるはず
                if name not in insta_ids:
                    insta_ids.append(name)
            self.driver.execute_script('window.scrollBy(0, 400)')
        return insta_ids
