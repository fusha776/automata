from random import random, randint, shuffle
from automata.common.settings import FOLLOWER_UPPER_LIMIT


class Following():
    '''フォロー追加回りを管理
    '''

    def __init__(self, abilities):
        self.ab = abilities

    def load_my_followers_as_userlist(self):
        '''自分のフォロワーからユーザリストを生成

        Returns:
            dict: key -> {'insta_id', 'follow_msg'}
        '''
        self.ab.profile.switch_to_user_profile(self.ab.login_id)
        self.ab.profile.switch_to_following(self.ab.login_id)

    def follow_followers_friends(self, actions, fav_rate=0.8, max_user_times=50):
        '''自分のフォロワーがフォロー中のユーザをフォローする（ややこしい）

        Args:
            actions (int): 実行する action の回数
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
        self.ab.profile.switch_to_user_profile(self.ab.login_id)
        self.ab.profile.switch_to_following(self.ab.login_id)

        # automataがフォローしたリストを検索対象から除外する
        skipped = self.ab.dao.fetch_valid_followings()
        skipped = set([i['instagram_id'] for i in skipped])

        # ユーザセットを取得する
        users_dataset = self.ab.profile.get_user_parts()

        # 上の方は何回も呼ばれるから、乱数ベースで下の方へずらす（その場しのぎ）
        skipping_cnt = randint(50, 200)
        users_dataset = users_dataset[(-1) * skipping_cnt:]
        users_dataset = users_dataset[:max_user_times]

        cnt = 0
        checked = set([self.ab.login_id])
        for user_i in users_dataset:
            if cnt >= actions:
                self.ab.logger.debug(f'必要分のアクションが完了:  稼働アクション数:{cnt} > 要求アクション数:{actions}')
                break

            # 非公開でないユーザを探す
            self.ab.profile.switch_to_user_profile(user_i['insta_id'])
            if self.ab.profile.check_private():
                continue

            # 自分のフォロワーのフォロー中へ遷移
            self.ab.profile.switch_to_following(user_i['insta_id'])

            # 一人のフォロワーから辿れるアクション数に最大値を設定する
            self.ab.logger.debug(f'フォロワーの探索を開始: {user_i["insta_id"]} アクション残: {cnt}/{actions}')
            actions_in_this_user = min(7, actions - cnt)

            followed_cnt, fav_cnt, memo = self.follow_in_following(actions_in_this_user, checked, fav_rate)
            cnt += (followed_cnt + fav_cnt)
            checked.update(memo)

    def follow_in_following(self, actions, checked, fav_rate=0.8):
        '''フォロー中画面に表示されているユーザをフォローする

        Args:
            actions(int): フォローを押す回数
            fav_rate (float): フォローの代わりにfavする確率
            checked (set): チェック済みのインスタIDのmemo

        Returns:
            (int, int, set): フォローした数, favした回数,  チェック済みユーザ

        Conditions:
            [プロフィール] - [フォロー中]
        '''
        def check_valid():
            '''有効ユーザかチェックする

            Returns:
                bool: 有効なユーザ -> True
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

            # 法人相当： フォロワー / フォロー数 > 1.5
            elif (profs['follower'] / (profs['following'] + 1)) > 1.5:
                is_valid = False
                reason_msg = "法人判定: フォロー中/フォロワー数 比率が大きい"
            return is_valid, reason_msg

        def try_to_fav():
            '''ファボを試す (最大3つ)

            Returns:
                int: favした数
            '''
            links = self.ab.profile.get_post_links()
            shuffle(links)
            fav_cnt = 0
            for link in links[:3]:
                self.ab.driver.get(link)
                fav_cnt += int(self.ab.post.fav())
            return fav_cnt

        followed_cnt = 0
        fav_cnt = 0
        error_cnt = 0

        # ユーザセットを取得する
        users_dataset = self.ab.profile.get_user_parts()

        # 上の方は相互フォローが固まってるから飛ばす（暫定処置）
        users_dataset = users_dataset[-50:]

        for user_i in users_dataset:
            insta_id_i = user_i['insta_id']

            # 必要分のアクションが終わったら離脱
            if (followed_cnt + fav_cnt) >= actions:
                break
            # 失敗が続く場合は中断
            if error_cnt > 20:
                self.ab.logger.debug('復旧ムーブ: アクションエラーが続くため参照元フォロワーを変更')
                break
            # チェック済ならskip
            if insta_id_i in checked:
                continue
            # フォロー中ならskip
            if ('フォロー中' in user_i['follow_msg']) or ('リクエスト済み' in user_i['follow_msg']):
                continue

            # キャッシュしてプロフィールへ
            checked.add(insta_id_i)
            self.ab.profile.switch_to_user_profile(insta_id_i)

            # 有効なユーザか確かめる
            is_valid, reason_msg = check_valid()
            if not is_valid:
                error_cnt += 1
                self.ab.logger.debug(f'is invalid: {insta_id_i}, {reason_msg}')
                continue

            # 同一アクションの連続はブロックの危険があがるので、ランダムでアクションを変える
            if random() < fav_rate:
                # ファボをトライする
                new_fav_cnt = try_to_fav()
                fav_cnt += new_fav_cnt
                self.ab.logger.debug(f'アクション fav: {insta_id_i}, cnt is {new_fav_cnt}')
                if new_fav_cnt:
                    error_cnt = 0
                else:
                    error_cnt += 1
            else:
                # フォローをトライする
                has_followed = self.ab.profile.follow(insta_id_i)
                self.ab.logger.debug(f'アクション follow: {insta_id_i}')
                if has_followed:
                    followed_cnt += 1
                    error_cnt = 0
                else:
                    error_cnt += 1

        self.ab.logger.debug(f'フォロワーの探索を終了: 追加アクション計: follow -> {followed_cnt}, fav -> {fav_cnt}')
        return followed_cnt, fav_cnt, checked
