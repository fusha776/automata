from time import sleep
from selenium.webdriver.common.by import By


class Avtivity():
    def back_to_activity_home(self):
        cnt = 0
        while True:
            username_btn = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_textview_title')
            if username_btn:
                return

            # まずホームボタンの再プッシュを試す
            if cnt <= 10:
                self.push_activity_btn()
            else:
                self.push_app_back_btn()
            sleep(2)
            cnt += 1
            if cnt >= 20:
                raise Exception('アクティビティホームへ戻れませんでした')

    def fetch_activities(self):
        '''表示されているアクティビティの履歴elementを取得

        TODO:
        複数投稿へ別々にfavが付いたときは写真別で対象ユーザが分けられるかもしれない、まだ不明
        '''
        # アクティビティへ移動
        self.back_to_activity_home()

        # イベントの数を推定し、1つずつ確認する
        event_size = len(self.find_elements_continually(By.XPATH, '//android.view.ViewGroup'))

        activities = {}
        followings, favs = [], []
        for i in range(event_size):
            captions = self.pixel.driver.find_elements_by_xpath(f'//android.view.ViewGroup[{i}]/android.widget.TextView')
            imgs = self.pixel.driver.find_elements_by_xpath(f'//android.view.ViewGroup[{i}]/android.widget.FrameLayout')

            # TODO: 必要に迫られたら実装する
            # 対象ユーザが 1人 or 2人以上 で画面描画が異なる。
            # 1人の場合はいったん保留。 表示2回目以降は、まとめられるなら2人以上パターンでまとめられる。
            # single_img = self.pixel.driver.find_elements_by_xpath(f'//android.view.ViewGroup[{i}]/android.widget.ImageView')
            if not captions:
                continue
            if not (imgs):
                continue

            if 'フォロー' in captions[0].text:
                followings.append(imgs[0])
            elif 'いいね' in captions[0].text:
                favs.append(imgs[0])

        activities['following'] = followings
        activities['fav'] = favs
        return activities

    def _follow_users_in_just_following(self, n_users=10, slide_n_times=20):
        '''アクティビティのフォロー開始通知からフォローする。

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        Return:
            int, list: フォローした人数, NG追加ユーザのname

        Condition:
            [アクティビティ] - [フォロワー] が表示されていること

        TODO:
            現状、すべてのユーザをフォローバックする
            条件分岐が必要になったらそのときに実装する
        '''
        all_btn = self.find_elements_continually(By.ID, 'com.instagram.android:id/see_all_button')
        if all_btn:
            all_btn[0].click()

        #  "フォローする" ボタンが見つかる限りクリック（"おすすめ" の "フォローする" はidが異なる）
        followed_users = 0
        additional_ng = set()
        for i in range(slide_n_times):
            follow_btns = self.driver.find_elements_by_id('com.instagram.android:id/button')
            username_btns = self.driver.find_elements_by_id('com.instagram.android:id/follow_list_username')
            if not follow_btns:
                break
            if followed_users >= n_users:
                break

            for idx in range(len(follow_btns)):
                # NGチェック (同じユーザの繰り返し参照を避ける)
                username = username_btns[idx].text
                if username in self.ng_users:
                    continue
                username_btns[idx].click()
                is_ng = self._check_ng()
                self.push_app_back_btn()
                if is_ng:
                    additional_ng.add(username)
                    continue

                if 'フォローする' in follow_btns[idx].text:
                    follow_btns[idx].click()
                    followed_users += 1
            self.slide_to_next()
        return followed_users, list(additional_ng)

    def _follow_users_in_just_fav(self, n_users=10, slide_n_times=20):
        '''アクティビティのファボ通知からフォローする。

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        Return:
            int: フォローした人数

        Condition:
            [アクティビティ] - [いいね] が表示されていること

        TODO:
            現状、すべてのユーザをフォローバックする
            条件分岐が必要になったらそのときに実装する
        '''
        followed_users = 0
        additional_ng = set()
        for i in range(slide_n_times):
            follow_btns = self.driver.find_elements_by_id('com.instagram.android:id/button')
            username_btns = self.driver.find_elements_by_id('com.instagram.android:id/follow_list_username')
            if not follow_btns:
                break
            if followed_users >= n_users:
                break

            for idx in range(len(follow_btns)):
                # NGチェック (同じユーザの繰り返し参照を避ける)
                username = username_btns[idx].text
                if username in self.ng_users:
                    continue
                username_btns[idx].click()
                is_ng = self._check_ng()
                self.push_app_back_btn()
                if is_ng:
                    additional_ng.add(username)
                    continue

                if 'フォローする' in follow_btns[idx].text:
                    follow_btns[idx].click()
                    followed_users += 1
            self.slide_to_next()
        return followed_users, additional_ng

    def _fav_users_in_just_fav(self, n_users=10, slide_n_times=20):
        '''アクティビティのファボ通知からファボ返しする。

        Args:
            n_users (int): ファボする人数
            slide_n_times (int): 下へスライドさせる最大回数

        Return:
            int: ファボした人数

        TODO:
            現状、すべてのユーザをファボ返しする
            条件分岐が必要になったらそのときに実装する

        Condition:
            [アクティビティ] - [いいね] が表示されていること
        '''
        followed_users = 0
        for i in range(slide_n_times):
            btns = self.driver.find_elements_by_id('com.instagram.android:id/row_user_imageview')
            if followed_users >= n_users:
                break
            if not btns:
                break

            for btn in btns:
                btn.click()
                fav_cnt = self._fav_latest_photo()
                self.push_app_back_btn()
                followed_users += fav_cnt
            self.slide_to_next()
        return followed_users
