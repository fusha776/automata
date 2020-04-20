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

    def unfollow_no_followbacks(self, actions, max_user_x_times=300):
        '''フォロバ無しのアカウントを、フォロワー一覧の表示順で外していく

        フォローバック確認：
            相手先のフォロー中を表示し、自分が一番上に来ていたらフォロバ有り

        Args:
            actions (int): 実行する action の回数
            max_user_x_times (int): フォローバックを確認する最大のフォロワー数
        '''
        self.ab.logger.debug('start operation: フォロバ無しアカをアンフォロー')
        self.pixel.back_to_profile_home()
        self.pixel._switch_to_following()
        savepoint_users = []
