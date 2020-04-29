import random
from math import ceil
from automata.common.settings import FOLLOWER_UPPER_LIMIT, HOJIN_KEYWORDS


class Following():
    '''フォロー追加回りを管理
    '''

    def __init__(self, abilities):
        self.ab = abilities

    def load_followers_as_userlist(self, target_id, rec_size=50):
        '''対象ユーザのフォロワーからユーザリストを生成

        Args:
            rec_size (int): 取得するアカの数

        Returns:
            dict[]: key -> {'insta_id', 'follow_msg'}
        '''
        self.ab.profile.switch_to_user_profile(target_id)
        self.ab.profile.switch_to_following(target_id)

        # ユーザセットを取得する
        raw_userlists = self.ab.profile.read_neighbor_datasets_on_order(rec_size, set())

        # 必要なカラムに絞る
        userlists = []
        for u in raw_userlists:
            dict_i = {'insta_id': u['insta_id'], 'follow_msg': u['follow_msg']}
            userlists.append(dict_i)

        # 上の方は何回も呼ばれるため、順番をシャッフルして返却
        random.shuffle(userlists)
        return userlists

    def follow_friends_neighbors(self, actions, my_friends=None, fav_rate=0.7, max_user_times=50):
        '''指定アカの フォロワー の フォロー中 をフォローする（ややこしい）
        指定 (my_friends) がある: 指定アカの フォロー中アカの フォロワー へアクション
        指定 (my_friends) がない: 自アカの フォロー中アカの フォロワー へアクション

        Args:
            actions (int): 実行する action の回数
            my_friends (dict[]): フォロワーの探索を開始する元ユーザのリスト
            fav_rate (float): フォローの代わりにfavする確率
            max_user_times (int): 自分のフォロワーを探索する最大回数（エラーループ防止）

        WARN:
            インスタグラムの Action Block が厳しい
            今のところの予想は以下

            * 一定時間以内の最大回数
            * 一定回数以上、連続して同じアクション？

            一回のアクションを少なくして定期的に呼び出せばいけるとは思う
            これ以上（Bot予測モデルとか異常検知とか）されてると、結構きつくなるかも
            イタチごっこしてやる
        '''
        self.ab.logger.debug('start operation: 対象ユーザの近隣を follow or fav')
        # 不要だけど、自然な動きに見せるため正しく遷移しておく
        self.ab.profile.switch_to_user_profile(self.ab.login_id)
        self.ab.profile.switch_to_following(self.ab.login_id)

        # 検索対象から除外する: automataがフォロー, 直近タッチ有り
        skipped_follow = self.ab.dao.fetch_valid_followings()
        skipped_follow = set([u['instagram_id'] for u in skipped_follow])
        skipped_touch = self.ab.dao.load_recent_touched_users()
        skipped_touch = {u['instagram_id'] for u in skipped_touch}
        checked = set([self.ab.login_id])
        checked.update(skipped_follow)
        checked.update(skipped_touch)

        # friendが渡されていれば、フォロワーを辿る開始IDをランダムに採用する
        starting_login_id = self.ab.login_id
        if my_friends:
            starting_login_id = random.choice(my_friends)['insta_id']
        starting_neighbors = self.load_followers_as_userlist(starting_login_id, max_user_times)
        users_at_least = 3  # 渡されなければ、リスク分散のために少なくとも3ユーザを辿る

        cnt = 0
        for user_i in starting_neighbors[:max_user_times]:
            if cnt >= actions:
                self.ab.logger.debug(f'必要分のアクションが完了:  稼働アクション数:{cnt} > 要求アクション数:{actions}')
                break

            # 対象ユーザのプロフィールへ移動
            self.ab.profile.switch_to_user_profile(user_i['insta_id'])

            # 非公開ならskip
            if self.ab.profile.check_private():
                continue

            # ターゲットのフォロワーへ遷移
            self.ab.profile.switch_to_followers(user_i['insta_id'])

            # 一人のフォロワーから辿れるアクション数に最大値を設定する
            actions_in_this_user = min(ceil(actions / users_at_least), actions - cnt)

            # [フォロー中 or フォロワー] に表示されているユーザに対してアクションを仕込む
            self.ab.logger.debug(f'フォロワーの探索を開始: {user_i["insta_id"]} アクション残: {cnt}/{actions}')
            followed_cnt, fav_cnt, memo = self._follow_in_neighbors(actions_in_this_user, checked, fav_rate)
            cnt += (followed_cnt + fav_cnt)
            checked.update(memo)
        self.ab.logger.debug('end operation: 対象ユーザの近隣を follow or fav')

    def _follow_in_neighbors(self, actions, checked, fav_rate=0.8):
        '''[フォロー中 or フォロワー] に表示されているユーザをフォローする

        Args:
            actions(int): フォローを押す回数
            fav_rate (float): フォローの代わりにfavする確率
            checked (set): チェック済みのインスタIDのmemo

        Returns:
            (int, int, set): フォローした数, favした回数,  チェック済みユーザ

        Conditions:
            [プロフィール] - [フォロー中 or フォロワー]
        '''
        def try_to_fav(max_fav_cnt=3):
            '''ファボを試す

            Args:
                max_fav_cnt (int): favする最大数

            Returns:
                int: favした数
            '''
            links = self.ab.profile.get_post_links()
            random.shuffle(links)
            fav_cnt = 0
            for link in links[:max_fav_cnt]:
                self.ab.driver.get(link)
                fav_cnt += int(self.ab.post.fav())
            return fav_cnt

        followed_cnt = 0
        fav_cnt = 0
        error_cnt = 0

        # ユーザセットを取得する.
        # アカウント状況未確認のため有効件数は不明
        new_users_dataset = self.ab.profile.read_neighbor_datasets_on_order(actions, checked)

        # とりあえずランダム化する（上の方は相互フォローが固まってる可能性がある）
        random.shuffle(new_users_dataset)

        for user_i in new_users_dataset:
            insta_id_i = user_i['insta_id']

            # 必要分のアクションが終わったら離脱
            if (followed_cnt + fav_cnt) >= actions:
                break
            # 失敗が続く場合は中断
            if error_cnt > 20:
                self.ab.logger.debug('復旧ムーブ: アクションエラーが続くため参照元フォロワーを変更')
                break
            # フォロー中ならskip
            if ('フォロー中' in user_i['follow_msg']):
                self.ab.dao.add_recent_touched_user(insta_id_i, None)
                continue
            elif ('リクエスト済み' in user_i['follow_msg']):
                self.ab.dao.add_recent_touched_user(insta_id_i, 1)
                continue

            # プロフィールへ
            self.ab.profile.switch_to_user_profile(insta_id_i)

            # 有効なユーザか確かめる
            is_valid, reason_msg = self.check_valid()
            if not is_valid:
                error_cnt += 1
                is_private = True if '鍵アカ' in reason_msg else False
                self.ab.dao.add_recent_touched_user(insta_id_i, int(is_private))
                self.ab.logger.debug(f'無効なユーザ: {insta_id_i}, {reason_msg}')
                continue

            # 同一アクションの連続はブロックの危険があがるので、ランダムでアクションを変える
            if random.random() < fav_rate:
                # ファボをトライする
                new_fav_cnt = try_to_fav()
                fav_cnt += new_fav_cnt
                self.ab.logger.debug(f'アクション fav: {insta_id_i}, cnt is {new_fav_cnt}')
                if new_fav_cnt:
                    error_cnt = 0
                else:
                    error_cnt += 1
            else:
                # フォローをトライする (フォローバックはしない)
                has_followed = self.ab.profile.follow(insta_id_i)
                self.ab.logger.debug(f'アクション follow: {insta_id_i}')
                if has_followed:
                    followed_cnt += 1
                    error_cnt = 0
            self.ab.dao.add_recent_touched_user(insta_id_i, 0)

        self.ab.logger.debug(f'フォロワーの探索を終了: 追加アクション計: follow -> {followed_cnt}, fav -> {fav_cnt}')
        return followed_cnt, fav_cnt, checked

    def check_valid(self):
        '''有効ユーザかチェックする

        Returns:
            bool, str: 有効なユーザ -> True, 判定理由メッセージ

        Conditions:
            [プロフィール]
        '''
        # プロフィールを取得、失敗した場合はskip
        profs = self.ab.profile.get_user_details()
        has_needed_profs = True
        has_needed_profs &= profs['follower'] is not None
        has_needed_profs &= profs['following'] is not None
        has_needed_profs &= profs['is_following'] is not None
        has_needed_profs &= profs['is_private'] is not None
        if not (has_needed_profs):
            return False, "鍵アカ or プロフィール取得失敗"

        is_valid = True
        reason_msg = "it seems good."
        # 既にフォロー済
        if profs['is_following']:
            is_valid = False
            reason_msg = "既にフォロー済"

        # プライベート
        elif profs['is_private']:
            is_valid = False
            reason_msg = "鍵アカ"

        # 法人相当： 所定値よりフォロワー数が多い
        elif profs['follower'] >= FOLLOWER_UPPER_LIMIT:
            is_valid = False
            reason_msg = "法人判定: フォロワー数が閾値超え"

        # 法人相当： フォロワー / フォロー数 > 2
        elif (profs['follower'] / (profs['following'] + 1)) > 2:
            is_valid = False
            reason_msg = "法人判定: フォロー中/フォロワー数 比率が大きい"
        return is_valid, reason_msg

    def check_kojin(self):
        '''個人かどうかチェックする

        Returns:
            bool: 法人相当と判定 -> True

        Conditions:
            [プロフィール]
        '''
        follower_cnt = self.ab.profile.pick_follower_num()
        following_cnt = self.ab.profile.pick_following_num()
        bio_msg = self.ab.profile.pick_bio_message()
        website_btn = self.ab.profile.pick_website_btn()

        # 要素取得に失敗したらFalseで返却 (bool形式を除く)
        if not (follower_cnt and following_cnt and bio_msg):
            return False, "個人判定不可: 要素取得に失敗"

        is_valid = True
        reason_msg = "it seems good."
        # 所定値よりフォロワー数が多い
        if follower_cnt >= FOLLOWER_UPPER_LIMIT:
            is_valid = False
            reason_msg = "法人判定: フォロワー数が閾値超え"

        # フォロワー / フォロー数 > 2
        elif follower_cnt/(following_cnt + 1) > 2:
            is_valid = False
            reason_msg = "法人判定: フォロー中/フォロワー数 比率が大きい"

        # 特定のキーワードをプロフ文に含んでいる
        elif any([True for h_kw in HOJIN_KEYWORDS if h_kw in bio_msg]):
            is_valid = False
            reason_msg = "法人判定: 特定キーワードをプロフ文に含んでいる"

        # 外部websiteが登録されている
        elif website_btn:
            is_valid = False
            reason_msg = "法人判定: 外部websiteが登録されている"

        return is_valid, reason_msg

    def follow_by_searching(self, actions, keywords, fav_rate=0.7):
        '''投稿検索で見つけたフォロワーをフォローする

        followは個人アカか確かめるけど、favは未確認でも良いでしょう

        Args:
            actions (int): 実行する action の回数
            keywords (str[]): 検索するキーワード ハッシュタグでも `#` は消しておく
            fav_rate (float): フォローの代わりにfavする確率
        '''
        self.ab.logger.debug('start operation: キーワード検索の最新投稿アカを follow or fav')
        self.ab.search.switch_to_search_home()

        keywords_shuffled = random.sample(keywords, len(keywords))
        followed_cnt = 0
        fav_cnt = 0
        is_enough = False
        for kw in keywords_shuffled:
            self.ab.logger.debug(f'次のキーワード検索 - 開始: {kw} アクション残: {fav_cnt + followed_cnt}/{actions}')
            self.ab.search.search_tags(kw)
            for img_link in self.ab.search.load_imgs():
                # 必要分のアクションが終わったら離脱
                if (followed_cnt + fav_cnt) >= actions:
                    is_enough = True
                    break

                self.ab.driver.get(img_link)
                insta_id_i = self.ab.post.estimate_insta_id()

                # 同一アクションの連続はブロックの危険があがるので、fav or follow をランダムで変える
                is_private = False
                if random.random() <= fav_rate:
                    # fav
                    fav_cnt += int(self.ab.post.fav())
                    self.ab.logger.debug(f'アクション fav: {insta_id_i}, cnt is 1')
                else:
                    # follow
                    self.ab.profile.switch_to_user_profile(insta_id_i)
                    # 個人アカか確かめる
                    is_valid, reason_msg = self.check_kojin()
                    print(is_valid, reason_msg)
                    if is_valid:
                        # フォローをトライする (フォローバックはしない)
                        has_followed = self.ab.profile.follow(insta_id_i)
                        self.ab.logger.debug(f'アクション follow: {insta_id_i}')
                        if has_followed:
                            followed_cnt += 1
                    else:
                        is_private = True if '鍵アカ' in reason_msg else False
                        self.ab.logger.debug(f'無効なユーザ: {insta_id_i}, {reason_msg}')
                self.ab.dao.add_recent_touched_user(insta_id_i, int(is_private))
            self.ab.logger.debug(f'次のキーワード検索 - 終了: keyword -> {kw}, follow -> {followed_cnt}, fav -> {fav_cnt}')
            if is_enough:
                break
        self.ab.logger.debug('end operation: キーワード検索の最新投稿アカを follow or fav')
