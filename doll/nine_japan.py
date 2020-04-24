import random
from automata.doll.doll import Doll


class NineJapan(Doll):
    def __init__(self, doll_id):
        super().__init__(doll_id)
        self.doll_id = doll_id

    def operate(self):
        # 初期パラメータのセット
        defaults = {'actions_ff': 0,
                    'actions_unfollow': 0,
                    'actions_unfollow_no_fb': 0,
                    'fav_rate': 1.0,
                    'max_user_times': 10,
                    'my_friends': [],
                    'user_size_to_check': 100}
        for key, val in defaults.items():
            self.params.setdefault(key, val)

        # 同じfriendが連続しないようにシャッフルする
        random.shuffle(self.params['my_friends'])

        # 1. ターゲットの隣人をフォロー or fav
        if self.params['actions_ff'] > 0:
            self.facade.following.follow_friends_neighbors(self.params['actions_ff'],
                                                           self.params['my_friends'],
                                                           self.params['fav_rate'],
                                                           self.params['max_user_times'])

        # 2. 一定期間を超えたユーザをアンフォロー
        if self.params['actions_unfollow'] > 0:
            self.facade.unfollowing.unfollow_expires_users(self.params['actions_unfollow'])

        # 3. フォローバックのないアカをアンフォロー
        # ※動かなくはないけど、1. と混ぜると負荷が上がるので非推奨
        if self.params['actions_unfollow_no_fb'] > 0:
            self.facade.unfollowing.unfollow_no_followbacks(self.params['actions_unfollow_no_fb'],
                                                            self.params['user_size_to_check'])
