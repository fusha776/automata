from selenium.webdriver.common.by import By


class Post():
    def post_photo(self, msg):
        '''写真を投稿する。
        pathやファイル名ではアップロードする写真を選択できない。
        登録日最新のファイルがデフォルトで選択済のため、これをそのままアップロードする。
        '''

        self.switch_to_instagram_home()
        self.find_post_btn().click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/caption_text_view').send_keys(msg)
        # self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
