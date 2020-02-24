from time import sleep
from selenium.webdriver.common.by import By


class Profile():

    def back_to_profile_home(self):
        cnt = 0
        while True:
            self.push_back_btn()
            username_btn = self.driver.find_elements_by_id('com.instagram.android:id/title_view')
            if username_btn:
                return
            sleep(1)
            cnt += 1
            if cnt >= 20:
                raise Exception('プロフィールホームへ戻れませんでした')

    def follow(self):
        '''フォローボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip
        対象ユーザのprofile画面が表示されていることが前提。
        '''
        el = self.driver.find_elements(By.XPATH, '//android.widget.TextView[@text="フォローする"]')
        if el:
            el[0].click()

    def unfollow(self):
        '''フォロー解除ボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip
        対象ユーザのprofile画面が表示されていることが前提。
        '''
        el = self.driver.find_elements(By.XPATH, '//android.widget.TextView[@text="フォロー中"]')
        if el:
            el[1].click()  # idx:0 は、対象ユーザのフォロー一覧を指す
        else:
            return None

        el = self.driver.find_elements_by_id('com.instagram.android:id/follow_sheet_unfollow_row')
        if el:
            el[0].click()
        else:
            return None

    def send_dm(self, msg):
        '''DMを送る
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip
        対象ユーザのprofile画面が表示されていることが前提。

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
