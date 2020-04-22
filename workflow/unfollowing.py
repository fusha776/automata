from datetime import datetime, timedelta
from random import random, shuffle
from automata.common.settings import FLLOWING_ALIVE_DAYS


class Unfollowing():
    '''アンフォロー追加回りを管理
    '''

    def __init__(self, abilities):
        self.ab = abilities

    def unfollow_expires_users(self, actions):
        '''フォローしてから一定期間を超えたユーザをアンフォローする

        Args:
            actions (int): 実行する action の回数
        '''

        def fetch_users_to_unfollow():
            '''アンフォロー対象のユーザリストを生成

            Returns:
                str[]: アンフォロー対象のインスタID
            '''
            users_and_days = self.ab.dao.fetch_valid_followings()
            expires_date = datetime.now() - timedelta(days=FLLOWING_ALIVE_DAYS)

            users_to_unfollow = []
            for user in users_and_days:
                if user['updated_at'] < expires_date:
                    users_to_unfollow.append(user['instagram_id'])
            return users_to_unfollow

        self.ab.logger.debug('start operation: 一定期間を超えたユーザをアンフォロー')
        users_to_unfollow = fetch_users_to_unfollow()
        unfollow_cnt = 0
        for id_i in users_to_unfollow[:actions]:
            self.ab.profile.switch_to_user_profile(id_i)
            unfollow_cnt += int(self.ab.profile.unfollow(id_i))

        self.ab.logger.debug(f'アンフォローを終了: 追加アクション計: unfollow -> {unfollow_cnt}/{actions}')
        self.ab.logger.debug('end operation: 一定期間を超えたユーザをアンフォロー')

    def unfollow_no_followbacks(self, actions, user_size_to_check=100):
        '''フォロバ無しのアカウントを、フォロワー一覧の表示順で外していく

        WARN:
            自動フォロー系と混ぜるな危険！！
            アクション履歴も共用してるし、自動・手動でフォロー状況管理の同期も取ってない

        フォローバック確認：
            相手先のフォロー中を表示し、自分が一番上に来ていたらフォロバ有り

        Args:
            actions (int): 実行する action の回数 ※1回確認するのに unfollow + follow で最大2回必要な点に注意
            user_size_to_check (int): フォローバックを確認する最大のフォロワー数（[フォロー中] の表示順）
        '''
        self.ab.logger.debug('start operation: フォロバ無しをアンフォロー')
        self.ab.profile.switch_to_user_profile(self.ab.login_id)
        self.ab.profile.switch_to_following(self.ab.login_id)

        # 新規確認のユーザ集合を必要分を保証するように回収する
        touched_users = self.ab.dao.load_recent_touched_users()
        touched_users = {u['instagram_id'] for u in touched_users}
        new_usersets = self.ab.profile.read_neighbor_datasets_on_order(user_size_to_check, touched_users)
        new_usersets = {u['insta_id'] for u in new_usersets}

        # 確認対象アカのフォローバックを確認する
        followed_cnt, unfollowed_cnt = 0, 0
        for insta_id_i in new_usersets:
            # 必要分のアクションが終わったら離脱
            if (unfollowed_cnt + followed_cnt) >= actions:
                break

            # 対象アカのプロフィールへ
            self.ab.profile.switch_to_user_profile(insta_id_i)

            # まず普通にアンフォロー
            unfollowed = self.ab.profile.unfollow(insta_id_i, stop_private=True)
            if unfollowed:
                unfollowed_cnt += 1
            else:
                self.ab.logger.debug(f'鍵アカをskip: {insta_id_i}')
                self.ab.dao.add_recent_touched_user(insta_id_i, 1)
                continue

            # フォローバックされてたら再フォローする
            has_followed_back = self.ab.profile.follow_back(insta_id_i, insert_into_table=False)
            if has_followed_back:
                followed_cnt += 1
                self.ab.logger.debug(f'フォロバ有りを再フォロー: {insta_id_i}')
            else:
                self.ab.logger.debug(f'フォロバ無しをリム: {insta_id_i}')

            # 確認済アカとしてテーブルへ追加する処理
            self.ab.dao.add_recent_touched_user(insta_id_i, None)

        self.ab.logger.debug(f'end operation: フォロバ無しをアンフォロー: 追加アクション計: follow -> {followed_cnt}, unfollow -> {unfollowed_cnt}')
        return followed_cnt, unfollowed_cnt
