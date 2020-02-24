from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium.webdriver.common.mobileby import MobileBy

from automata.addon import DriverEx
from automata.search import Search
from automata.post import Post
from automata.profile import Profile


class InstagramPixel(DriverEx, Search, Post, Profile):

    def __init__(self):
        # driver を起動
        desired_caps = {}
        desired_caps['platformName'] = 'Android'
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.camera_storage = '/storage/emulated/0/DCIM/Camera'

    def find_home_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'ホーム')
        if btn:
            return btn[0]
        else:
            return None

    def find_search_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, '検索・発見')
        if btn:
            return btn[0]
        else:
            return None

    def find_post_btn(self):
        btn = self.find_elements_continually(MobileBy.ACCESSIBILITY_ID, 'カメラ')
        if bool(btn) & (len(btn) >= 1):
            return btn[1]
        else:
            return None

    def push_back_btn(self):
        back_btn = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_button_back')
        if back_btn:
            back_btn[0].click()

    def launch_instagram(self):
        # ホームからinstagramを起動
        self.switch_to_android_home()
        self.find_element_continually(MobileBy.ACCESSIBILITY_ID, 'Instagram').click()

    def switch_to_instagram_home(self):
        '''ホームボタンが見つかればクリックする。
        見つからない場合は起動中のinstagram落として再起動する。
        3回再起動して上手くいかなければException
        '''

        def reboot(self):
            self.launch_instagram()
            self.driver.keyevent(AndroidKey.APP_SWITCH)
            self.driver.swipe(540, 1100, 540, 100, 200)
            self.launch_instagram()
            return self.wait()

        home_btn = self.driver.find_elements_by_accessibility_id('ホーム')
        if home_btn:
            home_btn[0].click()
            return

        # ホームボタンが見つからなかった場合
        for i in range(0, 3):
            if reboot(self):
                print('load sucessed')
                return
        raise Exception('ホーム画面へ遷移できませんでした')
