from time import sleep
from automata.worker.worker import Worker


class NineJapan(Worker):

    def __init__(self, worker_id, *args, **kwargs):
        super().__init__(worker_id, *args, **kwargs)

    def operate(self, actions_ff=0, actions_unfollow=0, actions_unfollow_no_fb=0, fav_rate=0.7, max_user_times=50):

        print('ope in')
        # フォロワーのフォロワーに対して、フォロー or fav
        if actions_ff > 0:
            self.facade.following.follow_followers_friends(actions_ff, fav_rate, max_user_times)

        # # 一定期間を超えたユーザをアンフォロー
        # if actions_unfollow > 0:
        #     self.wf.unfollow_expires_users(actions_unfollow)

        # # フォローバックのないアカをアンフォロー
        # if actions_unfollow_no_fb > 0:
        #     self.wf.unfollow_no_followbacks(actions_unfollow_no_fb, max_user_x_times=max_user_x_times)
