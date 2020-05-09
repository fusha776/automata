from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from automata.common.settings import WAIT_LOADING_SECONDS
from automata.common.utils import wait, loading
from automata.common.utils import to_num


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
        '''
        self.driver.get(f'https://www.instagram.com/direct/inbox/')

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
        user_menu_btn = self.driver.find_elements_by_xpath(f'//*[contains(text(), {insta_id})]')
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
            [DMトップ] - [ユーザDM]
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
    def _read_replay(self):
        '''相手からのダイレクトメッセージを取得する

        Returns:
            str[]: 画面上に取得できた返信メッセージ

        Conditions:
            [DMトップ] - [ユーザDM]
        '''

        # アイコン有無から相手のメッセージを特定する
        replay_boxs = self.driver.find_elements_by_xpath('//a/img/../../../..')

        reply_msgs = []
        for reply_box in replay_boxs:
            msg = reply_box.find_elements_by_xpath('.//span')
            # 画像の場合はspanに文字が埋め込まれない
            if msg:
                reply_msgs.append(msg.text)
        return reply_msgs

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
        sent_msgs = self.dm_histories_repository.load_messages(insta_id, self.login_id)
        sent_msgs = [m['message'] for m in sent_msgs]

        # DM返信を取得
        self.switch_to_dm_window(insta_id)
        reply_msgs = self._read_replay()

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
    def estimate_insta_id(self):
        '''投稿画面から投稿者のインスタIDを推定する
        htmlの変更に強くするためにもネストの深いタグを辿ることは回避したいので、浅い検索条件から推定する

        条件:
            リンクにテキストが含まれるaタグの中で出現回数最大のリンク

        Returns:
            str: インスタID

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        a_cnts = {}
        anchors = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, '//a')))
        # clickable は単数しか取得できないので、要素の確認後に取りなおす
        anchors = self.driver.find_elements_by_xpath('//a')
        for a in anchors:
            link = a.get_attribute('href')
            tag_text = a.text

            # テキストがブランクならskip
            if not tag_text:
                continue

            if tag_text not in a_cnts:
                a_cnts[tag_text] = 0
            if tag_text in link:
                a_cnts[tag_text] += 1
        return max(a_cnts, key=a_cnts.get)

    @loading
    def read_post_msg(self):
        '''投稿コメントを取得する

        WARN:
            投稿コメント無しの場合はタグが生成されない
            投稿コメント無し & レス有り の場合、レスを取得してしまうけどレアケースとして保留にしておきます

        Returns:
            str: 投稿コメント

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        self.push_read_more_btn()
        msg_tags = self.driver.find_elements_by_xpath('//div[contains(@data-testid, "post-comment-root")]/span/span')
        if msg_tags:
            return msg_tags[0].text
        return None

    @loading
    @wait()
    def read_fav_cnt(self):
        '''該当の写真投稿のfav数を取得する

        WARN:
            動画投稿のfav数はスマホから回収できない

        Returns:
            int: fav数

        Conditions:
            [投稿写真]
        '''
        fav_tags = self.driver.find_elements_by_xpath('//a[contains(@href, "liked_by")]/span')
        if fav_tags:
            fav_cnt = to_num(fav_tags[0].text)
            return fav_cnt
        return None

    @wait(1)
    def push_read_more_btn(self):
        '''続きを読むボタンを押す

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        self.driver.execute_script('window.scrollBy(0, 300)')
        more_btn = self.driver.find_elements_by_xpath('//button[contains(text(), "続きを読む")]')
        if more_btn:
            more_btn[0].click()
