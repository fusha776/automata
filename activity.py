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
        '''
        # イベントの数を推定し、1つずつ確認する
        event_size = len(self.find_elements_continually(By.XPATH, '//android.view.ViewGroup'))

        activities = {}
        followings, favs = [], []
        for i in range(event_size):
            captions = self.pixel.driver.find_elements_by_xpath(f'//android.view.ViewGroup[{i}]/android.widget.TextView')
            imgs = self.pixel.driver.find_elements_by_xpath(f'//android.view.ViewGroup[{i}]/android.widget.FrameLayout')

            # TODO: 必要に迫られたら実装する
            # 対象ユーザが 1人 or 2人以上 で画面描画が異なる。1人の場合はいったん保留
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

    def follow_users_in_just_following(self, n_users=10, slide_n_times=20):
        '''アクティビティのフォロー開始通知からフォローする。

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        Return:
            int: フォローした人数

        TODO:
            現状、すべてのユーザをフォローバックする
            条件分岐が必要になったらそのときに実装する

        Condition:
            [アクティビティ] - [フォロワー] が表示されていること
        '''
        all_btn = self.find_elements_continually(By.ID, 'com.instagram.android:id/see_all_button')
        if all_btn:
            all_btn[0].click()
        else:
            return 0

        #  "フォローする" ボタンが見つかる限りクリック（"おすすめ" の "フォローする" はidが異なる）
        followed_users = 0
        for i in range(slide_n_times):
            btns = self.driver.find_elements_by_id('com.instagram.android:id/button')
            if not btns:
                break
            if followed_users >= n_users:
                break

            for btn in btns:
                if 'フォローする' in btn.text:
                    btn.click()
                    followed_users += 1
            self.slide_to_next()
        return followed_users

    def follow_users_in_just_fav(self, n_users=10, slide_n_times=20):
        '''アクティビティのファボ通知からフォローする。

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        Return:
            int: フォローした人数

        TODO:
            現状、すべてのユーザをフォローバックする
            条件分岐が必要になったらそのときに実装する

        Condition:
            [アクティビティ] - [いいね] が表示されていること
        '''
        followed_users = 0
        for i in range(slide_n_times):
            btns = self.driver.find_elements_by_id('com.instagram.android:id/button')
            if followed_users >= n_users:
                break
            if not btns:
                break

            for btn in btns:
                if 'フォローする' in btn.text:
                    btn.click()
                    followed_users += 1
            self.slide_to_next()
        return followed_users

    def fav_users_in_just_fav(self, n_users=10, slide_n_times=20):
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
                fav_cnt = self.fav_latest_photo()
                self.push_app_back_btn()
                followed_users += fav_cnt
            self.slide_to_next()
        return followed_users
