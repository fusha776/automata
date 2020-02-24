from time import sleep
from random import random
import re
from selenium.webdriver.common.by import By


class Search():

    def back_to_search_home(self):
        cnt = 0
        while True:
            home_signal = self.driver.find_elements_by_id('com.instagram.android:id/destination_hscroll')
            if home_signal:
                return
            self.push_app_back_btn()
            sleep(1)
            cnt += 1
            print(f'pushed back {cnt}')
            if cnt >= 20:
                raise Exception('検索ホームへ戻れませんでした')

    def search(self, keyword):
        # 検索ホームへ移動
        self.push_search_btn()
        self.back_to_search_home()

        # 検索ワードを入力
        self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_search_edit_text').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_search_edit_text').send_keys(keyword)

        # 一番上の候補をクリック
        self.check_scope_as_tag()
        self.select_keyword_in_suggestions(keyword)
        self.sort_results_by_newest()

        # とりあえず3回くらいloopを回す
        names = []
        for img in self.img_each(5, 1):
            img.click()
            sleep(1 + 3 * random())
            names.append(self.find_element_continually(By.ID, 'com.instagram.android:id/row_feed_photo_profile_name').text.split(' ')[0])
            self.find_element_continually(By.ID, 'com.instagram.android:id/action_bar_button_back').click()
        print(names)

    def img_each(self, slide_cnt=0, needed_img_cnt=50, checked=None):
        '''キャッシュ保存（checked）によって以下が達成される。必要に応じて調整。
        1. 同じ投稿をクリックしなくなる
        2. ある程度同じユーザの投稿をクリックしなくなる
        3. たまに画像を飛ばしてしまう（スクロールや待機時間が要調整かも）

        Yield:
            img (webElement): 画像をフォーカスした webElement
        '''

        # 終了チェック
        if (slide_cnt < 0) or (needed_img_cnt <= 0):
            return

        # 初回ならmemoを初期化
        if checked is None:
            checked = {}

        imgs = self.driver.find_elements_by_xpath(
            '//androidx.recyclerview.widget.RecyclerView[@resource-id="com.instagram.android:id/recycler_view"]/android.widget.ImageView')
        has_picked = False
        for img in imgs:
            description = img.get_attribute('content-desc').split('―')[0].strip()
            if description not in checked:
                checked[description] = True
                has_picked = True
                break

        if has_picked:
            yield img
            needed_img_cnt -= 1
        else:
            self.slide_to_next()
            slide_cnt -= 1

        print(f'picked: {has_picked},', f'slide zan: {slide_cnt},', f'img zan: {needed_img_cnt}')
        yield from self.img_each(slide_cnt, needed_img_cnt, checked)

    def gather_hashtags(self):
        '''投稿コメントからハッシュタグを回収する

        Condition:
            投稿一覧画面（フルサイズ）が表示されていること

        Return:
            str[]: `#` 抜きのハッシュタグ
        '''
        detail = self.go_to_reply()
        detail = detail.text
        hashtags = re.findall('#(.+?)[\n| ]', detail.replace('#', ' #'))  # ハッシュ同士で挟まれたタグを拾うために、ブランクを付与
        self.push_forced_back_btn()

        return hashtags

    def go_to_reply(self):
        '''投稿一覧画面（フルサイズ）から、リプライ画面へ遷移する

        Condition:
            投稿一覧画面（フルサイズ）が表示されていること

        Return:
            webElement: リプライ画面のコメント内容を指した webElement
        '''
        cnt = 0
        while True:
            # リプライ画面へ来ていたら返却
            detail = self.driver.find_elements_by_id('com.instagram.android:id/row_comment_textview_comment')
            if detail:
                return detail

            # 1つ上の投稿が描画キャッシュされている可能性があるため、一番下のコメントを取得する
            view = self.driver.find_elements_by_id('com.instagram.android:id/row_feed_comment_textview_layout')
            if view:
                view[-1].click()
            sleep(1)
            cnt += 1
            if cnt >= 20:
                raise Exception('リプライ画面へ遷移できませんでした')

    def go_to_profile(self):
        '''投稿一覧画面（フルサイズ）から、プロフィール画面へ遷移する

        Condition:
            投稿一覧画面（フルサイズ）が表示されていること
        '''
        self.find_element_continually(By.ID, 'com.instagram.android:id/row_feed_photo_profile_name').click()

    def select_keyword_in_suggestions(self, keyword):
        '''検索候補の中から、ルールベースで1つ選んで検索をかける。

        優先順:
            完全一致 > 検索ワードが部分一致 > 最上位の検索候補

        Condition:
            検索候補が表示されていること
        '''
        suggestions = self.find_elements_continually(By.ID, 'com.instagram.android:id/row_hashtag_textview_tag_name')
        # 1. 完全一致
        for s_i in suggestions:
            if s_i.text.replace('#', '') == keyword:
                s_i.click()
                return

        # 2. 検索ワードが部分一致
        for s_i in suggestions:
            if keyword in s_i.text:
                s_i.click()
                return

        # 3. 最上位の検索候補
        suggestions[0].click()

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
