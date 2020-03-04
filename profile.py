from time import sleep
from selenium.webdriver.common.by import By


class Profile():

    def back_to_profile_home(self):
        cnt = 0
        while True:
            username_btn = self.driver.find_elements_by_id('com.instagram.android:id/title_view')
            if username_btn:
                return
            self.push_app_back_btn()
            sleep(1)
            cnt += 1
            if cnt >= 20:
                raise Exception('プロフィールホームへ戻れませんでした')

    def follow(self):
        '''フォローボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
            int: フォロー成功: True, フォロー失敗: False
        '''
        el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローする"]', sec=10)
        if el:
            el[0].click()
            return True
        el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローバックする"]', sec=10)
        if el:
            el[0].click()
            return True
        return False

    def unfollow(self):
        '''フォロー解除ボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
            int: アンフォロー成功: 1, アンフォロー失敗: 0
        '''
        el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=10)
        if el:
            el[1].click()  # idx:0 は、対象ユーザのフォロー一覧を指す
            return True

        el = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_sheet_unfollow_row', sec=10)
        if el:
            el[0].click()
            return True
        return False

    def fetch_profile(self):
        '''ユーザの基本情報を取得する
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
        list[str or int]: [username, ]
        '''
        # 省略されている場合を考慮して、解除のためにクリックする
        bio_el = self.find_elements_continually(By.ID, 'com.instagram.android:id/profile_header_bio_text', sec=10)
        if bio_el:
            bio_el[0].click()
            bio_el = self.find_elements_continually(By.ID, 'com.instagram.android:id/profile_header_bio_text', sec=10)  # 再描画後を取得

        profiles = {}
        profiles['username'] = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_textview_title')
        profiles['name'] = self.driver.find_elements_by_id('com.instagram.android:id/profile_header_full_name')
        profiles['posts'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_post_count')
        profiles['follower'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_followers_count')
        profiles['following'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_following_count')
        profiles['website'] = self.driver.find_elements_by_id('com.instagram.android:id/profile_header_website')
        profiles['bio'] = bio_el

        # webElement が格納されているので、値を取り出す
        for col in profiles:
            if profiles[col]:
                profiles[col] = profiles[col][0].text
            else:
                profiles[col] = None

        # 数値へ変換
        profiles['posts'] = int(profiles['posts'].replace(',', ''))
        profiles['follower'] = int(profiles['follower'].replace(',', ''))
        profiles['following'] = int(profiles['following'].replace(',', ''))
        return profiles

    def send_dm(self, msg):
        '''DMを送る
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
            bool: DM送信の成功可否
            exception: エラーが発生していなければ None
        '''

        try:
            self.driver.find_element(By.XPATH, '//android.widget.TextView[@text="メッセージ"]').click()
            msg_input = self.driver.find_element_by_id('com.instagram.android:id/row_thread_composer_edittext')
            msg_input.click()
            msg_input.send_keys(msg)
            self.driver.find_element_by_id('com.instagram.android:id/row_thread_composer_button_send').click()
            self.push_back_btn()
        except Exception as e:
            # 何らかの理由でDMの送信に失敗した場合
            return False, e
        return True, None
