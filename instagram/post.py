from selenium.webdriver.common.by import By


class Post():
    ''' TODO:
    投稿画面だけはリンクボタンが消えるので、これに対応するために back_to_xxx_btn を修正する
    '''

    def post_photo(self, msg):
        '''写真を投稿する。
        pathやファイル名ではアップロードする写真を選択できない。
        登録日最新のファイルがデフォルトで選択済のため、これをそのままアップロードする。
        '''

        self.switch_to_instagram_home()
        self.push_post_btn()
        self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/caption_text_view').send_keys(msg)

        if self.dryrun:
            return
        self.find_element_continually(By.ID, 'com.instagram.android:id/next_button_textview').click()
