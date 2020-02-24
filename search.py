from time import sleep
from selenium.webdriver.common.by import By


class Search():

    def back_to_search_home(self):
        cnt = 0
        while True:
            back_btn = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_button_back')
            search_btn = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_search_edit_text')
            if back_btn:
                back_btn[0].click()
            elif search_btn:
                return
            sleep(1)
            cnt += 1
            if cnt >= 20:
                raise Exception('検索ホームへ戻れませんでした')

    def search(self, keywords):
        # 検索ホームへ移動
        self.find_search_btn().click()
        self.back_to_search_home()

        # 検索ワードを入力
        self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_search_edit_text').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_search_edit_text').send_keys(keywords)

        # 一番上の候補をクリック
        self.check_scope_as_tag()
        self.find_element_continually(By.XPATH, '//android.widget.TextView').click()
        self.sort_results_by_newest()

        # とりあえず3回くらいloopを回す
        checked = {}
        names = []
        cnt = 0
        for img in self.check_each(checked, 5, 20):
            img.click()
            sleep(2)
            names.append(self.find_element_continually(By.ID, 'com.instagram.android:id/row_feed_photo_profile_name').text)
            self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_button_back').click()
            cnt += 1
            if cnt > 10:
                break
        print(names)

    def check_each(self, checked, slide_cnt, needed_img_cnt):
        '''キャッシュ保存（checked）によって、以下が達成される。必要に応じて調整。
        1. 同じ投稿をクリックしなくなる
        2. ある程度同じユーザの投稿をクリックしなくなる

        Yield:
            img (webElement): 画像をフォーカスした webElement
        '''

        imgs = self.driver.find_elements_by_xpath(
            '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.instagram.android:id/recycler_view"]/android.widget.ImageView')
        for img in imgs:
            description = img.get_attribute('content-desc').split('―')[0].strip()
            if description not in checked:
                checked[description] = True
                yield img

        if slide_cnt > 0:
            self.slide_to_next()
            yield from self.check_each(slide_cnt - 1, checked)

    def check_scope_as_tag(self):
        btns = self.find_elements_continually(By.ID, 'com.instagram.android:id/tab_button_name_text')
        for btn in btns:
            if btn.text == 'タグ':
                btn.click()
                return
        raise Exception('検索タグを押せませんでした')

    def check_scope_as_account(self):
        btns = self.find_elements_continually(By.ID, 'com.instagram.android:id/tab_button_name_text')
        for btn in btns:
            if btn.text == 'アカウント':
                btn.click()
                return
        raise Exception('検索タグを押せませんでした')

    def sort_results_by_newest(self):
        '''検索結果を新着順でソート
        '''
        self.find_elements_by_text_continually('最近')[0].click()

    def sort_results_by_popularity(self):
        '''検索結果を人気順でソート
        '''
        self.find_elements_by_text_continually('トップ')[0].click()

    def slide_to_next(self):
        '''3*3 ブロック分、検索結果画面を下へスライドする
        '''
        self.driver.swipe(540, 1700, 540, 1700 - 370*3, 5000)
