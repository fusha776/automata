from automata.doll.doll import Doll


class NineJapan(Doll):
    def __init__(self, doll_id, *args, **kwargs):
        super().__init__(doll_id, *args, **kwargs)

    def operate(self, actions_ff=0, actions_unfollow=0, actions_unfollow_no_fb=0,
                fav_rate=1.0, max_user_times=10, my_friends=None, user_size_to_check=100):

        # 1. ターゲットの隣人をフォロー or fav
        if actions_ff > 0:
            self.facade.following.follow_friends_neighbors(actions_ff, my_friends, fav_rate, max_user_times)

        # 2. 一定期間を超えたユーザをアンフォロー
        if actions_unfollow > 0:
            self.facade.unfollowing.unfollow_expires_users(actions_unfollow)

        # 3. フォローバックのないアカをアンフォロー
        # ※動かなくはないけど、1. と混ぜると負荷が上がるので非推奨
        if actions_unfollow_no_fb > 0:
            self.facade.unfollowing.unfollow_no_followbacks(actions_unfollow_no_fb, user_size_to_check=user_size_to_check)
