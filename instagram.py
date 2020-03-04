from datetime import datetime

from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium.webdriver.common.mobileby import MobileBy

from automata.addon import DriverEx
from automata.search import Search
from automata.post import Post
from automata.profile import Profile
from automata.dao import Dao


class InstagramPixel(DriverEx, Search, Post, Profile):

    def __init__(self, worker_id):
        # worker id は後で引数行きになる
        self.worker_id = worker_id

        # 実行日を取得
        self.today = datetime.now().strftime('%Y%m%d')

        # DBセッションを取得
        self.dao = Dao(self.worker_id, self.today)

        # DBからコンフィグを取得
        q_res = self.dao.fetch_worker_settings()
        self.worker_group = q_res[0]
        self.worker_group_lake_path = q_res[1]
        self.dm_message_id = q_res[2]
        self.hashtag_group = q_res[3]
        self.post_per_day = q_res[4]
        self.dm_per_day = q_res[5]
        self.fav_per_day = q_res[6]
        self.follow_per_day = q_res[7]
        self.unfollow_per_day = q_res[8]
        self.post_per_boot = q_res[9]
        self.dm_per_boot = q_res[10]
        self.fav_per_boot = q_res[11]
        self.follow_per_boot = q_res[12]
        self.unfollow_per_boot = q_res[13]

        # driver を起動
        desired_caps = {}
        desired_caps['platformName'] = 'Android'
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.camera_storage = '/storage/emulated/0/DCIM/Camera'

    def push_home_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'ホーム')
        if btn:
            btn[0].click()
            self.wait()

    def push_search_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, '検索・発見')
        if btn:
            btn[0].click()
            self.wait()

    def push_post_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'カメラ')
        if bool(btn) & (len(btn) >= 1):
            btn[1].click()  # [0] は写真撮影画面へ飛ぶ
            self.wait()

    def push_activity_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'アクティビティ')
        if bool(btn) & (len(btn) >= 1):
            btn[0].click()
            self.wait()

    def push_profile_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'プロフィール')
        if bool(btn) & (len(btn) >= 1):
            btn[0].click()
            self.wait()

    def push_app_back_btn(self):
        '''アプリ内の「戻る」相当の要素をタッチする

        Return:
            bool: クリック可否
        '''
        back_btn = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_button_back')
        if back_btn:
            back_btn[0].click()
            return True
        return False

    def push_forced_back_btn(self):
        '''何らかの手段で前に戻ろうとする
        まず画面のボタンから戻ろうとし（安定性が高い）、できなければ android key で前に戻る
        '''
        if self.push_app_back_btn():
            return
        else:
            self.driver.keyevent(AndroidKey.BACK)

    def launch_instagram(self):
        # ホームからinstagramを起動
        self.switch_to_android_home()
        self.find_elements_by_text_continually('Instagram')[0].click()

    def reboot_instagram(self):
        '''インスタを再起動する
        '''
        self.launch_instagram()
        self.driver.keyevent(AndroidKey.APP_SWITCH)
        self.driver.swipe(540, 1100, 540, 100, 200)
        self.launch_instagram()
        return self.wait()

    def switch_to_instagram_home(self):
        '''ホームボタンが見つかればクリックする。
        見つからない場合は起動中のinstagram落として再起動する。
        3回再起動して上手くいかなければException
        '''
        home_btn = self.driver.find_elements_by_accessibility_id('ホーム')
        if home_btn:
            home_btn[0].click()
            return

        # ホームボタンが見つからなかった場合
        for i in range(0, 3):
            if self.reboot_instagram():
                print('load sucessed')
                return
        raise Exception('ホーム画面へ遷移できませんでした')
