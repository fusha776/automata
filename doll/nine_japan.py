import random
from datetime import datetime
from automata.doll.doll import Doll


class NineJapan(Doll):
    def __init__(self, doll_id):
        super().__init__(doll_id)

    def operate(self):
        # 初期パラメータのセット
        defaults = {'actions_friend_neighbors': 0,
                    'actions_friend_following_neighbors': 0,
                    'actions_popular_post_neighbors': 0,
                    'actions_tags_search': 0,
                    'actions_unfollow': 0,
                    'actions_unfollow_no_fb': 0,
                    'fav_rate': 1.0,
                    'max_user_times': 10,
                    'search_keywords': [],
                    'my_friends': [],
                    'user_size_to_check': 100}
        for key, val in defaults.items():
            self.params.setdefault(key, val)

        # 同じfriendが連続しないようにシャッフルする
        random.shuffle(self.params['my_friends'])

        # 1. ターゲットのフォロー中のフォロー中をフォロー or fav
        if self.params['actions_friend_following_neighbors'] > 0:
            if self.params['my_friends']:
                starting_neighbors = self.facade.following.load_followings_as_userlist(random.choice(self.params['my_friends']))
            else:
                starting_neighbors = self.facade.following.load_followings_as_userlist(self.facade.abilities.login_id)
            self.facade.following.follow_friends_neighbors(self.params['actions_friend_following_neighbors'],
                                                           starting_neighbors,
                                                           self.params['fav_rate'],
                                                           self.params['max_user_times'])

        # 1. 人気投稿アカのフォロー中をフォロー or fav
        if self.params['actions_popular_post_neighbors'] > 0:
            starting_neighbors = self.facade.following.load_popular_post_userlist(random.choice(self.params['search_keywords']))
            self.facade.following.follow_friends_neighbors(self.params['actions_popular_post_neighbors'],
                                                           starting_neighbors,
                                                           self.params['fav_rate'],
                                                           self.params['max_user_times'])

        # 2. 検索結果の最新投稿アカをフォロー or fav
        if self.params['actions_tags_search'] > 0:
            self.facade.following.follow_by_searching(self.params['actions_tags_search'],
                                                      self.params['search_keywords'],
                                                      self.params['fav_rate'])

        # 3. 一定期間を超えたユーザをアンフォロー
        if self.params['actions_unfollow'] > 0:
            self.facade.unfollowing.unfollow_expires_users(self.params['actions_unfollow'])

        # 4. フォローバックのないアカをアンフォロー
        # ※動かなくはないけど、1. と混ぜると負荷が上がるので非推奨
        if self.params['actions_unfollow_no_fb'] > 0:
            self.facade.unfollowing.unfollow_no_followbacks(self.params['actions_unfollow_no_fb'],
                                                            self.params['user_size_to_check'])

    @classmethod
    def format(cls, target_day, doll_records):
        '''アクション集計レコードを受け取って、整形した出力用テキストを返却する

        Args:
            target_day (str): アクション集計日
            doll_records (Row[]): doll別の集計レコード
        '''
        def fillna(val):
            return val if val is not None else 0

        t_date = datetime.strptime(target_day, '%Y%m%d')
        ym_header = f'{t_date.month}/{t_date.day}'
        res_str = f'{ym_header}\n'

        for idx, action in enumerate(doll_records):
            # ブロックかつアクション数が一定以下なら、全てのアクションを0にする（通知ポップまでに数秒のラグがあるため）
            fav_cnt = fillna(action["fav"])
            follow_cnt = fillna(action["follow"])
            unfollow_cnt = fillna(action["unfollow"])
            report = ''
            if action['is_blocked'] == 1:
                report = '稼働中にアクションブロック発生'
                if action['summary_cnt'] <= 5:
                    fav_cnt = 0
                    follow_cnt = 0
                    unfollow_cnt = 0
                    report = 'アクションブロック中'

            res_str += f'{idx+1}.{action["label"]}\n'
            res_str += f'{action["login_id"]}\n'
            res_str += f'いいね: {fav_cnt}\n'
            res_str += f'フォロー: {follow_cnt}\n'
            res_str += f'アンフォロー: {unfollow_cnt}\n'
            res_str += f'報告: {report}\n'
            res_str += '\n'
        return res_str
