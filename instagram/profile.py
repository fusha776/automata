import re
from random import random
from time import sleep
from selenium.webdriver.common.by import By
from appium.webdriver.common.mobileby import MobileBy
# from automata.common.settings import wait
from automata.common.settings import FOLLOWER_UPPER_LIMIT
from automata.common.exception import ActionBlockException


class Profile():
    def back_to_profile_home(self):
        cnt = 0
        while True:
            username_btn = self.driver.find_elements_by_id('com.instagram.android:id/title_view')
            if username_btn:
                return
            # まずホームボタンの再プッシュを試す
            if cnt <= 10:
                self.push_profile_btn()
            else:
                self.push_app_back_btn()
            sleep(2)
            cnt += 1
            if cnt >= 20:
                raise Exception('プロフィールホームへ戻れませんでした')

    def _follow(self, sec=5, allow_to_follow_back=False, allow_to_follow_private=False):
        '''フォローボタンを押す

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
            (bool, bool): (フォロー成功, 正常終了)
        '''
        # プライベート設定アカウントを弾く
        if (not allow_to_follow_private) and self._check_private():
            return False, True

        res = (False, False)
        btn_is_found = False
        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローする"]', sec=sec)
            if el:
                el[0].click()
                btn_is_found = True
                res = (True, True)

        if (not btn_is_found) and allow_to_follow_back:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローバックする"]', sec=sec)
            if el:
                el[0].click()
                btn_is_found = True
                res = (True, True)

        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=sec)
            if len(el) >= 2:  # following (フォロー中) で必ず1件ヒットするはず
                btn_is_found = True
                res = (False, True)

        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="リクエスト済み"]', sec=sec)
            if el:
                btn_is_found = True
                res = (False, True)

        # アクションのブロックチェックをする
        # el = self.driver.find_elements_by_id('com.instagram.android:id/default_dialog_title')
        # if el and ('ブロック' in el[0].text):
        #     body = self.driver.find_elements_by_id('com.instagram.android:id/dialog_body')
        #     print('アクションがブロックされています 検知動作: フォロー')
        #     raise ActionBlockException(f'フォロー動作時に、ブロック表示が発生しました: {el[0].text}. {body[0].text}')
        # else:
        #     if len(el) >= 1:
        #         print(el[0].text)

        return res

    def _unfollow(self, sec=10):
        '''フォロー解除ボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザの [プロフィール]

        Return:
            bool: アンフォロー成功: True, アンフォロー失敗: False
        '''
        el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=sec)
        if el:
            el[1].click()  # idx:0 は、対象ユーザのフォロー一覧を指す

        el = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_sheet_unfollow_row', sec=sec)
        if el:
            el[0].click()
            return True
        return False

    def _fetch_profile(self):
        '''ユーザの基本情報を取得する
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Return:
            dict[str or int or bool]: key -> [username, name, posts, follower, following, website, bio, is_following]

        Condition:
            対象ユーザのprofile画面が表示されていること
        '''
        def to_num(s):
            '''投稿, フォロワー, フォロー中などを数値へ変換する
            '''
            if not s:
                return None

            s = s.replace(',', '')
            if '万' in s:
                s = s.replace('万', '')
                s = float(s) * 10000
            return int(s)

        # WARN:
        # bioの `続きを読む` をタッチしようとするとき、
        # ハッシュタグがコメントに仕込まれていると、そっちをタッチしてしまう
        # このため、全文表示は諦める。 `続きを読む` だけをピンポで狙うのはかなり難しそう
        bio_el = self.find_elements_continually(By.ID, 'com.instagram.android:id/profile_header_bio_text', sec=10)
        # if bio_el:
        #     bio_el[0].click()
        #     bio_el = self.find_elements_continually(By.ID, 'com.instagram.android:id/profile_header_bio_text', sec=10)  # 再描画後を取得

        profiles = {}
        profiles['username'] = self.driver.find_elements_by_id('com.instagram.android:id/action_bar_textview_title')
        profiles['name'] = self.driver.find_elements_by_id('com.instagram.android:id/profile_header_full_name')
        profiles['posts'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_post_count')
        profiles['follower'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_followers_count')
        profiles['following'] = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_textview_following_count')
        profiles['website'] = self.driver.find_elements_by_id('com.instagram.android:id/profile_header_website')
        profiles['bio'] = bio_el

        following_btn = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=2)
        profiles['is_following'] = True if len(following_btn) >= 2 else False

        # webElement が格納されているので、値を取り出す
        for col in profiles:
            if profiles[col]:
                profiles[col] = profiles[col][0].text
            else:
                profiles[col] = None

        # 数値へ変換
        profiles['posts'] = to_num(profiles['posts'])
        profiles['follower'] = to_num(profiles['follower'])
        profiles['following'] = to_num(profiles['following'])
        return profiles

    def _check_ng(self):
        '''プロフィール情報から、NG判定を行う
        一旦、以下のルールでフォロー対象か否かを判断する
        Rule: Bio に日本語が含まれている

        Return:
            bool: 条件を満たせば True

        Condition:
            対象ユーザのprofile画面が表示されていること
        '''
        def is_japanese(s):
            return True if re.search(r'[ぁ-んァ-ン]') else False

        bio = self._fetch_profile()['bio']
        return not is_japanese(bio)

    def _send_dm(self, msg):
        '''DMを送る
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Return:
            bool: DM送信の成功可否
            exception: エラーが発生していなければ None

        Condition:
            対象ユーザのprofile画面が表示されていること
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

    def _search_following(self, insta_id):
        '''フォロー中のユーザへ検索をかけ、対象ユーザのElementを取得する

        Args:
            insta_id(str): 検索対象のインスタグラムID

        Returns:
            Element: 検索結果の対象ユーザのエレメント or None

        Conditions:
            [プロフィール] - [フォロー中]
        '''
        # idを検索
        self.find_element_continually(By.ID, 'com.instagram.android:id/row_search_edit_text').click()
        self.find_element_continually(By.ID, 'com.instagram.android:id/row_search_edit_text').send_keys(insta_id)

        # 検索結果ロード中があるため、一定期間ループさせる
        loop_cnt = 0
        while loop_cnt <= 20:
            no_result = self.driver.find_elements_by_id('com.instagram.android:id/row_no_results_textview')
            hit_users = self.driver.find_elements_by_id('com.instagram.android:id/follow_list_username')
            if no_result:
                return None

            # 結果中に完全一致が存在するかチェック
            for user in hit_users:
                if user.text == insta_id:
                    return user
            sleep(1)
            loop_cnt += 1
        return None

    def _fav_latest_photo(self):
        '''プロフィール画面から、直近投稿をファボする
        ファボ返しなどで使用

        Return:
            bool: 正常終了 -> True

        Condition:
            [プロフィール]
        '''
        res = False
        photos = self.find_elements_continually(By.XPATH, '//androidx.recyclerview.widget.RecyclerView/android.widget.ImageView', sec=10)
        if not photos:
            return res

        photos[0].click()
        if self._push_fav():
            res = True
        self.push_app_back_btn()
        return res

    def check_follow_back_status(self, instagram_ids):
        '''フォロー中のユーザのフォローバック状況を確認する

        Args:
            instagram_ids(str[]): 検索するユーザネーム（ID相当）

        Return:
            dict: {instagram_id: bool}  # フォロワーなら True
        '''
        self.back_to_profile_home()
        following_btn = self.find_elements_continually(
            By.ID, 'com.instagram.android:id/row_profile_header_following_container')
        following_btn[0].click()

        status = {}
        for instagram_id in instagram_ids:
            if self._search_following(instagram_id):
                status[instagram_id] = True
            else:
                False
        return status

    def _switch_to_followers(self):
        '''フォロワー画面へ遷移する

        Returns:
            bool: 正常終了 -> True

        Conditions:
            [プロフィールTOP] が表示されている
        '''
        for cnt_i in range(5):
            follower_btn = self.find_elements_continually(
                By.ID, 'com.instagram.android:id/row_profile_header_followers_container')
            follower_btn[0].click()

            # ちゃんと移動できたかチェック
            page_loaded = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username')

            if page_loaded:
                return True
        return False

    def _check_private(self):
        '''非公開設定になっているか確認する
        非公開だとフォロー中の表示不可など挙動が異なる

        Conditions:
            [プロフィールTOP] が表示されている
        '''
        private_btn = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_empty_profile_notice_title')
        if private_btn:
            return True
        else:
            return False

    def _switch_to_following(self):
        '''フォロー中画面へ遷移する

        Conditions:
            [プロフィールTOP] が表示されている
        '''
        for cnt_i in range(5):
            following_btn = self.find_elements_continually(
                By.ID, 'com.instagram.android:id/row_profile_header_following_container')
            following_btn[0].click()

            # ちゃんと移動できたかチェック
            page_loaded = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username')
            if page_loaded:
                return True
        return False

    def _each_recent_follower_ids(self, max_user_x_times=50):
        '''フォロワーのidを直近順で取得する
        フォロワー画面を開いたときのデフォルトが直近順

        Args:
            max_user_x_times(int): 直近のフォロワーのプロフィールへ飛ぶ回数
                エラーでループに入らないように（フェイルセーフ）、有限回数にする
                この値は、許容できるエラー落ちの回数とみなせる

        Returns:
            str[]: インスタグラムIDの配列

        Conditions:
            [プロフィール] - [フォロー中 or フォロワー]
        '''
        cnt = 0
        checked = set()
        for _ in range(max_user_x_times):
            new_users = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username')
            if not new_users:
                print('自分のフォロワー一覧が取得不可')
                return

            target = None
            for u_el in new_users:
                if u_el.text not in checked:
                    checked.add(u_el.text)
                    target = u_el
                    break

            if target is None:
                self.slide_to_next()
                continue

            print(f'yield: {target.text}')
            yield target
            cnt += 1
        print(f'each が条件抜け cnt:{cnt}, followes_cnt:{max_user_x_times}')
        return

    def _follow_in_following(self, actions=50, switch_rate=0.8):
        '''フォロー中画面に表示されているユーザをフォローする
        フォローできれば問答無用でフォローする

        WARN:
            同じ人を複数回フォローしたり、法人チェックを通したりしていない
            必要になったら実装する
            たぶんその場合はユーザIDだけ回収して、プロフまで飛んでからフォローになるはず

        Args:
            actions(int): フォローを押す回数
            switch_rate (float): フォローの代わりにfavする確率


        Returns:
            (int, int, bool): フォローした数, favした回数,  正常終了: True

        Conditions:
            [プロフィール] - [フォロー中]
        '''
        def check_valid(profs):
            '''有効ユーザかチェックする

            Args:
                profiles (dict): _fetch_profile() の出力結果相当のdict
            '''
            # profsの取得に失敗した場合はFalse。0件の場合も弾かれるけどOK
            followers = profs['follower']
            followings = profs['following']
            if not (followers and followings):
                return False

            is_valid = True
            # 既にフォロー済。取得失敗も弾かれるけどOK
            if profs['is_following']:
                return False

            # 法人相当： 所定値よりフォロワー数が多い
            if followers >= FOLLOWER_UPPER_LIMIT:
                is_valid = False

            # 法人相当： フォロワー / フォロー数 > 1.5
            if (followers / (followings + 1)) > 1.5:
                is_valid = False
            return is_valid

        def try_to_follow(self, insta_id):
            '''フォローを試す

            Returns:
                bool, bool: フォロー成功 -> True, 正常終了 -> True
            '''
            has_followed, is_ok = self._follow(sec=1)
            if not is_ok:
                print(f'緊急退避: フォロー失敗: {insta_id}')

            if has_followed:
                print(f'followed: {insta_id}')
                # ステータスを更新
                self.dao.add_following(insta_id, has_followed=1, is_follower=0)
                # アクション回数を更新
                self.dao.increase_action_count({'follow': 1})
            return has_followed, is_ok

        def try_to_fav(self):
            '''ファボを試す

            Returns:
                bool: 正常終了 -> True
            '''

            is_ok = self._fav_latest_photo()
            if is_ok:
                # アクション回数を更新
                self.dao.increase_action_count({'fav': 1})
            return is_ok

        followed_cnt = 0
        fav_cnt = 0
        checked = set()
        checked.add(self.login_id)
        not_found_cnt = 0
        while (followed_cnt + fav_cnt) < actions:
            # `フォロー中` をタッチしてプロフへ行かない機能必須だわ、これの有無で実行時間がだいぶ変わる

            # 未チェックのユーザを探す
            users = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username', sec=1)

            # ユーザリストが繰り返し取得不可なら失敗で返却
            if users is None:
                print('users list not found')
                self.slide_to_next()
                not_found_cnt += 1
                if not_found_cnt > 3:
                    print('緊急退避: ユーザリストが見つからない')
                    return followed_cnt, fav_cnt, False
                continue

            # 未チェックのユーザが入れば続行、いなければワイプスクロールして再探索
            target = None
            for u_el in users:
                if u_el.text not in checked:
                    checked.add(u_el.text)
                    target = u_el
                    break
            if target is None:
                self.slide_to_next()
                continue
            insta_id = target.text
            target.click()

            # 有効なユーザでなければskip
            profs = self._fetch_profile()
            if not check_valid(profs):
                self.push_app_back_btn()
                continue

            # 同一アクションの連続はブロックの危険があがるので、ランダムでアクションを変える
            if random() < switch_rate:
                # ファボをトライする
                is_ok = self._fav_latest_photo()
                if is_ok:
                    fav_cnt += 1
            else:
                # フォローをトライする
                has_followed, is_ok = try_to_follow(self, insta_id)
                if has_followed:
                    followed_cnt += 1

            # 処理失敗したら失敗を返却
            if not is_ok:
                return followed_cnt, fav_cnt, False

            self.push_app_back_btn()
        print('フォロワーのフォロー中探索が一周完了')
        return followed_cnt, fav_cnt, True

    def switch_login_id(self, new_id):
        '''指定されたユーザへスイッチする
        スイッチできなかったらエラー落ちでいい。そのまま放置するとアクション計算が狂ってしまうため。

        Args:
            new_id(str): スイッチ先のインスタグラムID
        '''
        self.back_to_profile_home()
        opt_btn = self.find_elements_continually(By.ID, 'com.instagram.android:id/title_view')
        opt_btn[0].click()
        sleep(2)  # モーダルの表示を待つ
        switch_btn = self.find_elements_by_text_continually(new_id)
        switch_btn[0].click()

    def unfollow_by_id(self, insta_id):
        '''指定されたIDのユーザをアンフォローする

        Args:
            insta_id(str): インスタグラムID

        Returns:
            bool: アンフォローに成功 -> True
        '''
        is_successful = False
        self.back_to_profile_home()
        self._switch_to_following()
        target_el = self._search_following(insta_id)

        if target_el:  # 対象ユーザがフォロー中から見つかった場合
            target_el.click()
            is_successful = self._unfollow()

        self.push_app_back_btn()
        return is_successful

    def _unfollow_if_no_followback(self, insta_id):
        '''フォロバを確認し、フォロバがなければアンフォローする

        Args:
            insta_id (str): 対象ユーザのインスタグラムID

        Returns:
            (bool, bool): (フォローを解除した -> True, 正常終了 -> True)

        Conditions:
            [プロフィール]
        '''
        self._switch_to_following()
        not_found_cnt = 0
        users = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username', sec=1)

        if users is None:
            print('users list not found')
            self.slide_to_next()
            not_found_cnt += 1
            if not_found_cnt > 3:
                print('緊急退避: ユーザリストが見つからない')
                return False, False

            # フォロバ有りの場合はそのまま返却
            if users[0].text == self.login_id:
                self.push_app_back_btn()
                return False, True

            # フォロバが無い場合はアンフォロー
            self.push_app_back_btn()
            if self._unfollow():
                self.dao.update_following(insta_id, has_followed=0, is_follower=0)
                self.pixel.dao.increase_action_count({'unfollow': 1})
                return True, True
            else:
                return False, False
