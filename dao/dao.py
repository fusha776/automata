import pymysql
from datetime import datetime
import shutil
from pathlib import Path
from automata.common.settings import NG_USER_SIZE, CACHED_TOUCHED_USER_SIZE


class Dao():
    '''DB, データレイクとのインターフェースを提供

    Args:
        doll_id (str): 起動するdollのid
        today (str): 実行日 yyyymmdd
    '''

    def __init__(self, doll_id, today):
        self.doll_id = doll_id
        self.today = today

        self.conn = pymysql.connect(host='localhost',
                                    user='root',
                                    password='root',
                                    db='automata',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)

    def store_used_contents(self, content_path):
        '''使用済の投稿ファイルをbackupディレクトリへ送る
        実行した doll_id を判別用に持たせる
        '''
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')
        ym = now.strftime('%Y%m')
        dst_path = f'{self.pixel.doll_group_lake_path}\\posted\\{ym}\\{timestamp}'
        shutil.move(content_path, dst_path)
        Path(f'{dst_path}\\{self.pixel.doll_id}').touch()

    def fetch_doll_settings(self):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    login_id, password, browser_data_dir, profile_dir, device_name, doll_class,
                    doll_group, doll_group_lake_path, dm_message_id, hashtag_group,
                    post_per_day, dm_per_day, fav_per_day, follow_per_day, unfollow_per_day,
                    post_per_boot, dm_per_boot, fav_per_boot, follow_per_boot, unfollow_per_boot
                FROM
                    doll_settings
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            res = cursor.fetchone()
        return res

    def read_doll_status(self):
        '''dollの現在の起動状況を取得する
        初回起動なら登録用レコードを登録してから返却する
        '''
        def record_doll(last_booted_at):
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO doll_status
                        (doll_id, last_booted_at, today_booted_times, is_running, is_blocked)
                    VALUES
                        (%s, %s, 0, 0, 0)
                    ON DUPLICATE KEY UPDATE
                        doll_id = doll_id
                    ''', (self.doll_id, last_booted_at))
                self.conn.commit()

        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    last_booted_at, today_booted_times, is_running, is_blocked
                FROM
                    doll_status
                WHERE
                    doll_id = %s
                ''', (self.doll_id,))
            q_res = cursor.fetchone()

        # 初回起動ならレコードを登録
        if not q_res:
            q_res = {'last_booted_at': datetime.now(),
                     'today_booted_times': 0,
                     'is_running': 0,
                     'is_blocked': 0}
            record_doll(q_res['last_booted_at'])
        return q_res

    def lock_doll_status(self):
        '''dollのステータスを起動中にする

        * 起動ロック中にする（同時起動を止める）
        * 最終起動日と当日の起動回数を更新する
        '''
        q_res = self.read_doll_status()

        # 起動回数のcount up. 日付が変わっていたらリセット
        now_dt = datetime.now()
        booted_cnt = q_res['today_booted_times']
        if now_dt.day != q_res['last_booted_at'].day:
            booted_cnt = 0
        booted_cnt += 1

        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = %s,
                    today_booted_times = %s,
                    is_running = 1
                WHERE
                    doll_id = %s
                ''', (now_dt, booted_cnt, self.doll_id))
            self.conn.commit()

    def unlock_doll_status(self):
        '''dollのステータスを停止中にする
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = %s,
                    is_running = 0
                WHERE
                    doll_id = %s
                ''', (datetime.now(), self.doll_id,))
            self.conn.commit()

    def update_last_booted_dt(self, target_doll_id):
        '''最終起動日時を更新する

        Args:
            target_doll_id (str): 対象のDoll ID
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = %s
                WHERE
                    doll_id = %s
                ''', (datetime.now(), target_doll_id))
            self.conn.commit()

    def increase_action_count(self, cnts):
        '''アクションのカウントを進める
        '''
        updated = {'post': 0, 'dm': 0, 'fav': 0, 'follow': 0, 'unfollow': 0, 'others': 0, 'summary_cnt': 0}
        if type(cnts) is int:
            updated['others'] += cnts
            updated['summary_cnt'] += cnts
        elif type(cnts) is dict:
            for key in cnts.keys():
                if key in updated:
                    updated[key] += cnts[key]
                else:
                    updated['others'] += cnts[key]
                updated['summary_cnt'] += cnts[key]
        updated['doll_id'] = self.doll_id
        updated['operated_on'] = self.today

        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO
                    action_counters (doll_id, operated_on, post, dm, fav,
                                     follow, unfollow, others, summary_cnt, is_blocked)
                VALUES
                    (%(doll_id)s, %(operated_on)s,
                     %(post)s, %(dm)s, %(fav)s,
                     %(follow)s, %(unfollow)s, %(others)s, %(summary_cnt)s, 0)
                ON DUPLICATE KEY UPDATE
                    post = post + %(post)s,
                    dm = dm + %(dm)s,
                    fav = fav + %(fav)s,
                    follow = follow + %(follow)s,
                    unfollow = unfollow + %(unfollow)s,
                    others = others + %(others)s,
                    summary_cnt = summary_cnt + %(summary_cnt)s
                ''', updated)
            self.conn.commit()

    def add_following(self, instagram_id, has_followed=1, is_follower=0):
        '''フォローを追加する
        '''
        now_timestamp = datetime.now()
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO following_status (
                    doll_id, instagram_id, has_followed, is_follower, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                ''', (self.doll_id, instagram_id, has_followed, is_follower, now_timestamp, now_timestamp))
            self.conn.commit()

    def save_unfollow(self, insta_id):
        '''アンフォローを記録する
        '''
        now_timestamp = datetime.now()
        with self.conn.cursor() as cursor:
            cursor.execute('''UPDATE
                                     following_status
                                 SET
                                     has_followed = 0,
                                     updated_at = %s
                                 WHERE
                                     doll_id = %s and
                                     instagram_id = %s
                              ''', (now_timestamp, self.doll_id, insta_id))
            self.conn.commit()

    def delete_following(self, insta_id):
        '''フォロー状況から該当ユーザを削除する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                DELETE FROM
                    following_status
                WHERE
                    doll_id = %s and
                    instagram_id = %s
            ''', (self.doll_id, insta_id))
            self.conn.commit()

    def fetch_following_only(self):
        '''フォローのみ状態のユーザを抽出する

        Return:
            dict: {instagram_id: updated_at}
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    instagram_id, updated_at
                FROM
                    following_status
                WHERE
                    doll_id = %s and
                    has_followed = 1 and
                    is_follower = 0
            ''', (self.doll_id,))
            q_res = cursor.fetchall()
        users = {}
        if q_res:
            users = dict(q_res)
        return users

    def update_following(self, instagram_id, has_followed, is_follower):
        '''フォロー状態を更新する
        '''
        now_timestamp = datetime.now()
        with self.conn.cursor() as cursor:
            cursor.execute('''UPDATE
                                     following_status
                                 SET
                                     has_followed = %s,
                                     is_follower =  %s,
                                     updated_at = %s
                                 WHERE
                                     doll_id = %s and
                                     instagram_id = %s
                              ''', (has_followed, is_follower, now_timestamp, self.doll_id, instagram_id))
            self.conn.commit()

    def fetch_ng_users(self):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    instagram_id
                FROM
                    ng_users t1 INNER JOIN doll_settings t2 ON
                        t1.doll_group = t2.doll_group
                WHERE
                    t2.doll_id = %s
                ORDER BY
                    created_on DESC
                LIMIT
                    %s
            ''', (self.doll_id, NG_USER_SIZE))
            res = cursor.fetchall()
        return res

    def add_ng_users(self, doll_group, ng_users):
        today = datetime.now().strftime('%Y%m%d')
        qs = []
        for insta_id in ng_users:
            qs.append((doll_group, insta_id, today, 0))

        with self.conn.cursor() as cursor:
            cursor.executemany('''INSERT INTO
                                     ng_users
                                 VALUES
                                     (%s, %s, %s, %s, %s, %s)
                                  ''', qs)
            self.conn.commit()

    def fetch_valid_followings(self):
        '''現在有効なフォロー中ユーザをすべて取得する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    instagram_id,
                    updated_at
                FROM
                    following_status
                WHERE
                    has_followed = 1 and
                    doll_id = %s
                ORDER BY
                    updated_at ASC
                LIMIT
                    200
            ''', (self.doll_id,))
            res = cursor.fetchall()
        return res

    def load_daily_action_results(self, doll_group, target_day):
        '''指定日のアクション結果を取得する

        Args:
            target_day (str; yyyymmdd): アクション結果を取得する日付
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                WITH valid_actions as (
                    SELECT
                        doll_id, post, dm, fav, follow,
                        unfollow, others, summary_cnt, is_blocked
                    FROM
                        action_counters
                    WHERE
                        operated_on = %s
                )

                SELECT
                    t1.login_id,
                    t1.label, t1.client, t1.doll_group,
                    t2.post, t2.dm, t2.fav, t2.follow,
                    t2.unfollow, t2.others, t2.summary_cnt, t2.is_blocked
                FROM
                    doll_settings t1 LEFT JOIN
                    valid_actions t2 ON
                        t1.doll_id = t2.doll_id
                WHERE
                    t1.doll_group = %s
                ORDER BY
                    t1.doll_id
            ''', (target_day, doll_group))
            res = cursor.fetchall()
        return res

    def put_blocked_mark(self):
        '''アクションブロックを検知した際に、マークを付ける
        '''
        # アクション件数のレコードが存在しない場合を考慮し、0件更新してレコードを発生させる
        self.increase_action_count(0)

        # アクションブロックフラグを付与
        with self.conn.cursor() as cursor:
            # アクション集計
            cursor.execute('''
                UPDATE
                    action_counters
                SET
                    is_blocked = 1
                WHERE
                    doll_id = %s and
                    operated_on = %s
            ''', (self.doll_id, self.today))

            # Doll ステータス
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    is_blocked = 1
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            self.conn.commit()

    def load_recent_touched_users(self, size=CACHED_TOUCHED_USER_SIZE):
        '''直近で何らかのアクションを取ったアカを取得する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    instagram_id
                FROM
                    recent_touched_histories
                WHERE
                    doll_id = %s
                ORDER BY
                    checked_at DESC
                LIMIT
                    %s
            ''', (self.doll_id, size))
            res = cursor.fetchall()
        return res

    def add_recent_touched_user(self, insta_id, is_private):
        '''直近で何らかのアクションを取ったユーザを追加する
        同じユーザへ何度も当たらないための処置（鍵アカのskipとかにも使えます）
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO
                    recent_touched_histories
                VALUES
                    (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    checked_at = %s
                ''', (self.doll_id, insta_id, is_private, datetime.now(), datetime.now())
            )
            self.conn.commit()

    def load_next_sleeping_doll(self):
        '''起動条件を満たす停止中のdollから、最終起動時間が一番古いdollを呼び出す
        要求action回数一応渡しているけど、現状Dollの具象クラスに埋め込みにしてる
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    t1.doll_id,
                    t2.doll_class,
                    t2.fav_per_day,
                    t2.follow_per_day,
                    t2.unfollow_per_day,
                    t1.last_booted_at,
                    t1.is_blocked
                FROM
                    doll_status t1
                        LEFT JOIN doll_settings t2 ON t1.doll_id = t2.doll_id
                        LEFT JOIN action_counters t3 ON t1.doll_id = t3.doll_id
                WHERE
                    t1.is_running = 0 and
                    t2.fav_per_day + t2.follow_per_day + t2.unfollow_per_day > ifnull(t3.fav, 0) + ifnull(t3.follow, 0) + ifnull(t3.unfollow, 0)
                ORDER BY
                    t1.last_booted_at
                ''')
            res = cursor.fetchone()
        return res

    def load_active_dolls(self):
        '''起動中のDollを取得する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    doll_id
                FROM
                    doll_status
                WHERE
                    is_running = 1
            ''')
            res = cursor.fetchall()
        return res

    def load_block_status(self):
        '''Dollのブロック状態を取得する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    is_blocked
                FROM
                    doll_status
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            res = cursor.fetchone()
        return res

    def reset_blocked_mark(self):
        '''DBの論理blockを解除して起動可能ステータスにする
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    is_blocked = 0
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            self.conn.commit()
