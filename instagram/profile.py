import re
from random import random, shuffle
from time import sleep
from selenium.webdriver.common.by import By
from appium.webdriver.extensions.android.nativekey import AndroidKey
from automata.common.settings import FOLLOWER_UPPER_LIMIT
# from automata.common.exception import ActionBlockException


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

    def _follow(self, insta_id, sec=5, allow_to_follow_back=True):
        '''フォローボタンを押す

        Args:
            insta_id (str): 対象ユーザのインスタグラムID
            allow_to_follow_back (bool): フォローバック可否

        Condition:
            対象ユーザのprofile画面が表示されていること

        Return:
            (bool, bool): (フォロー成功, 正常終了)
        '''

        # プライベートのフォローを許すと、プライベートの場合のアンフォローを組み込む必要が生じる
        # 検索画面からするしかないと思うけど、処理が重くなるから相当な覚悟が必要
        # どうしても必要に迫られたら、アンフォロー処理と同時に改修する
        allow_to_follow_private = False

        # プライベート設定アカウントを弾く
        if (not allow_to_follow_private) and self._check_private():
            print('private設定のため skip')
            return False, True

        has_followed = False
        is_ok = False
        btn_is_found = False
        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローする"]', sec=sec)
            if el:
                el[0].click()
                btn_is_found = True
                has_followed = True
                is_ok = True

        if (not btn_is_found) and allow_to_follow_back:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローバックする"]', sec=sec)
            if el:
                el[0].click()
                btn_is_found = True
                has_followed = True
                is_ok = True

        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=sec)
            if len(el) >= 2:  # following (フォロー中) で必ず1件ヒットするはず
                btn_is_found = True
                has_followed = False
                is_ok = True

        if not btn_is_found:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="リクエスト済み"]', sec=sec)
            if el:
                btn_is_found = True
                has_followed = False
                is_ok = True

        if has_followed:
            print(f'followed: {insta_id}')
            # ステータスを更新
            self.dao.add_following(insta_id, has_followed=1, is_follower=0)
            # アクション回数を更新
            self.dao.increase_action_count({'follow': 1})

        # アクションのブロックチェックをする
        # el = self.driver.find_elements_by_id('com.instagram.android:id/default_dialog_title')
        # if el and ('ブロック' in el[0].text):
        #     body = self.driver.find_elements_by_id('com.instagram.android:id/dialog_body')
        #     print('アクションがブロックされています 検知動作: フォロー')
        #     raise ActionBlockException(f'フォロー動作時に、ブロック表示が発生しました: {el[0].text}. {body[0].text}')
        # else:
        #     if len(el) >= 1:
        #         print(el[0].text)

        return has_followed, is_ok

    def _unfollow(self, insta_id, sec=10):
        '''フォロー解除ボタンを押す
        ブロック他へファジーに対応するため、ボタンが見つからない場合はskip

        Condition:
            対象ユーザの [プロフィール]

        Return:
            bool: アンフォロー成功: True, アンフォロー失敗: False
        '''
        has_unfollowed = False
        # プライベートアカへのフォロリク解除から試す
        el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="リクエスト済み"]', sec=1)
        if el:
            el[0].click()
            has_unfollowed = True

        # 通常のアンフォロー
        if not has_unfollowed:
            el = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=sec)
            if el:
                el[1].click()  # idx:0 は、対象ユーザのフォロー一覧を指す

            el = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_sheet_unfollow_row', sec=sec)
            if el:
                el[0].click()
                has_unfollowed = True

        if has_unfollowed:
            print(f'unfollow and delete: {insta_id}')
            self.dao.delete_following(insta_id)
            self.dao.increase_action_count({'unfollow': 1})
        return has_unfollowed

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
        # webElement が格納されているので、値を取り出す
        for col in profiles:
            if profiles[col]:
                profiles[col] = profiles[col][0].text
            else:
                profiles[col] = None

        # フォロー中フラグを取得
        following_btn = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォロー中"]', sec=3)
        profiles['is_following'] = False
        if following_btn and len(following_btn) >= 2:
            profiles['is_following'] = True

        # フォローバック（フォローされている）フラグを取得
        followed_btn = self.find_elements_continually(By.XPATH, '//android.widget.TextView[@text="フォローバックする"]', sec=3)
        profiles['is_only_followed'] = False
        if followed_btn:
            profiles['is_only_followed'] = True

        # プライペートフラグを取得
        profiles['is_private'] = self._check_private()

        # 一部を数値へ変換
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
        self.driver.keyevent(AndroidKey.ENTER)

        # 検索結果ロード中があるため、一定期間ループさせる
        loop_cnt = 0
        while loop_cnt <= 10:
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
            (bool, bool): 新規ファボ数 -> True, 正常終了 -> True

        Condition:
            [プロフィール]
        '''
        is_empty = self.find_elements_continually(By.ID, 'com.instagram.android:id/empty_state_view_image', sec=1)
        if is_empty:
            # 写真投稿がないケース. photos で element が1つしか取れないケースで見てもいいかも(英語版を未チェックのため)
            return 0, True

        photos = self.find_elements_continually(
            By.XPATH, '//androidx.recyclerview.widget.RecyclerView/android.widget.LinearLayout/android.widget.ImageView', sec=10)
        if not photos:
            print('投稿写真が見つかりませんでした')
            return 0, False

        # 取得できそうな写真の数をチェック
        photo_index = list(range(len(photos)))
        shuffle(photo_index)
        fav_cnt = 0
        is_ok = True
        for f_i in photo_index[:3]:  # 一人当たり最大3件ファボする
            photos = self.find_elements_continually(
                By.XPATH, '//androidx.recyclerview.widget.RecyclerView/android.widget.LinearLayout/android.widget.ImageView', sec=10)
            # fav or 取得 のどちらかでも失敗したら中断
            if not (is_ok and photos):
                is_ok = False
                break

            photos[f_i].click()
            has_fav, is_ok = self._push_fav()
            fav_cnt += 1 if has_fav else 0
            self.push_device_back_btn()
        return fav_cnt, is_ok

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
        private_btn_jpn = self.driver.find_elements_by_id('com.instagram.android:id/row_profile_header_empty_profile_notice_title')
        private_btn_en = self.driver.find_elements_by_id('com.instagram.android:id/empty_state_view_title')
        if private_btn_jpn or private_btn_en:
            return True
        else:
            return False

    def _switch_to_following(self):
        '''フォロー中画面へ遷移する

        Returns:
            bool: 遷移成功 -> True

        Conditions:
            [プロフィールTOP]
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
            # profsの取得に失敗した場合はFalse
            has_needed_profs = True
            has_needed_profs &= profs['follower'] is not None
            has_needed_profs &= profs['following'] is not None
            has_needed_profs &= profs['is_following'] is not None
            has_needed_profs &= profs['is_private'] is not None
            if not (has_needed_profs):
                return False

            is_valid = True
            # 既にフォロー済
            if profs['is_following']:
                is_valid = False

            # プライベート
            elif profs['is_private']:
                is_valid = False

            # 法人相当： 所定値よりフォロワー数が多い
            elif profs['follower'] >= FOLLOWER_UPPER_LIMIT:
                is_valid = False

            # 法人相当： フォロワー / フォロー数 > 1.5
            elif (profs['follower'] / (profs['following'] + 1)) > 1.5:
                is_valid = False
            return is_valid

        def try_to_follow(self, insta_id):
            '''フォローを試す

            Returns:
                bool, bool: フォロー成功 -> True, 正常終了 -> True
            '''
            has_followed, is_ok = self._follow(insta_id, sec=1)
            if not is_ok:
                print(f'緊急退避: フォロー失敗: {insta_id}')

            # if has_followed:
            #     print(f'followed: {insta_id}')
            #     # ステータスを更新
            #     self.dao.add_following(insta_id, has_followed=1, is_follower=0)
            #     # アクション回数を更新
            #     self.dao.increase_action_count({'follow': 1})
            return has_followed, is_ok

        def try_to_fav(self):
            '''ファボを試す

            Returns:
                bool: 正常終了 -> True
            '''

            fav_cnt, is_ok = self._fav_latest_photo()
            print(f'fav in. cnt: {fav_cnt}')
            if fav_cnt > 0:
                # アクション回数を更新
                self.dao.increase_action_count({'fav': fav_cnt})
            return fav_cnt, is_ok

        def read_user_not_checked_yet(self, checked):
            '''表示中のユーザ一覧から、未チェックのuser element を取得する

            Args:
                checked (set): チェック済の instagram_id を保存するset

            Returns:
                element or None: 未チェックのuser element, 見つからない場合はNone
            '''
            for i in range(3):
                users = self.find_elements_continually(By.ID, 'com.instagram.android:id/follow_list_username', sec=1)
                if not users:
                    # リストが取得不可の場合はスライドしてもう一回試す
                    self.slide_to_next()
                    continue

                # 未チェックのユーザが見つかれば返却、いなければワイプスクロールして再探索
                for u_el in users:
                    if u_el.text not in checked:
                        return u_el
                self.slide_to_next()
                continue
            # 最後まで見つからない場合
            return None

        followed_cnt = 0
        fav_cnt = 0
        skipped_cnt = 0
        checked = set()
        checked.add(self.login_id)
        # `フォロー中` をタッチしてプロフへ行かない機能必須だわ、これの有無で実行時間がだいぶ変わる
        while (followed_cnt + fav_cnt) < actions:
            # 未チェックのユーザを探す
            target = read_user_not_checked_yet(self, checked)

            # ユーザリストが繰り返し取得不可なら失敗で返却
            if target is None:
                print('緊急退避: ユーザリストが見つからない')
                return followed_cnt, fav_cnt, False

            # 対象ユーザのelementが取得できたらmemoを更新して続行
            insta_id = target.text
            checked.add(insta_id)
            target.click()

            # 有効なユーザでなければskip、連続するなら元ユーザを変更する
            profs = self._fetch_profile()
            if not check_valid(profs):
                self.push_device_back_btn()
                skipped_cnt += 1
                if skipped_cnt >= 10:
                    return followed_cnt, fav_cnt, True
                continue
            skipped_cnt = 0

            # 同一アクションの連続はブロックの危険があがるので、ランダムでアクションを変える
            if random() < switch_rate:
                # ファボをトライする
                new_fav_cnt, is_ok = try_to_fav(self)
                fav_cnt += new_fav_cnt
            else:
                # フォローをトライする
                print('follow in')
                has_followed, is_ok = try_to_follow(self, insta_id)
                if has_followed:
                    followed_cnt += 1

            # 処理失敗したら失敗を返却
            if not is_ok:
                print('アクションのトライに失敗')
                return followed_cnt, fav_cnt, False

            self.push_device_back_btn()
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
            is_successful = self._unfollow(insta_id)
            self.push_device_back_btn()
        else:
            # 見つからない場合： 相手先から解除されたか、リクエスト中か
            # リストから外してカウントアップしてしまう
            print(f'was removed so delete: {insta_id}')
            self.dao.delete_following(insta_id)
            self.dao.increase_action_count({'unfollow': 1})
            is_successful = True

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
                self.push_device_back_btn()
                return False, True

            # フォロバが無い場合はアンフォロー
            self.push_device_back_btn()
            if self._unfollow():
                self.dao.update_following(insta_id, has_followed=0, is_follower=0)
                self.pixel.dao.increase_action_count({'unfollow': 1})
                return True, True
            else:
                return False, False
