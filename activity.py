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
        activities = {}
        events = self.find_elements_continually(By.ID, 'com.instagram.android:id/row_container', sec=10)

        followings, favs = [], []
        for event in events:
            captions = event.find_elements_by_xpath('//android.widget.TextView')
            imgs = event.find_elements_by_xpath('//android.widget.ImageView')
            if not captions:
                continue
            if not imgs:
                continue

            if 'フォロー' in captions[0].text:
                followings.append(imgs[0])
            elif 'いいね' in captions[0].text:
                favs.append(imgs[0])

        activities['following'] = followings
        activities['fav'] = favs
        return activities
