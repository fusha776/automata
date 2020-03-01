import sqlite3
from automata.setting import DATABASE_PATH


class Dao():
    '''DBとのインターフェースを提供
    '''

    def __init__(self, worker_id, today):
        self.worker_id = worker_id
        self.today = today

        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()

    def fetch_worker_settings(self):
        self.cursor.execute(''' SELECT
                                    worker_group, worker_group_lake_path, dm_message_id, hashtag_group,
                                    post_per_day, dm_per_day, fav_per_day, follow_per_day, unfollow_per_day,
                                    post_per_boot, dm_per_boot, fav_per_boot, follow_per_boot, unfollow_per_boot
                                FROM
                                    worker_settings
                                WHERE
                                    worker_id = ?
                            ''', (self.worker_id,))
        return self.cursor.fetchone()

    def increase_action_count(self, cnts):
        '''アクションのカウントを進める
        '''
        keys = ('post', 'dm', 'fav', 'follow', 'unfollow', 'others', 'summary_cnt')
        self.cursor.execute(''' SELECT
                                    post, dm, fav, follow, unfollow, others, summary_cnt
                                FROM
                                    action_counters
                                WHERE
                                    worker_id = ? and
                                    operated_on = ?
                            ''', (self.worker_id, self.today))
        q_res = self.cursor.fetchone()
        if q_res:
            updated = dict(zip(keys, q_res))
        else:
            updated = dict(zip(keys, (0,) * len(keys)))

        if type(cnts) is int:
            updated['others'] += cnts
            updated['summary_cnt'] += cnts
        elif type(cnts) is dict:
            for key in cnts.keys():
                updated[key] += cnts[key]
                updated['summary_cnt'] += cnts[key]
        updated['worker_id'] = self.worker_id
        updated['operated_on'] = self.today

        with self.conn:
            self.conn.execute('''INSERT OR REPLACE INTO action_counters (
                                    worker_id, operated_on, post, dm, fav,
                                    follow, unfollow, others, summary_cnt)
                                 VALUES (:worker_id, :operated_on, :post, :dm, :fav,
                                    :follow, :unfollow, :others, :summary_cnt)
                ''', updated)
