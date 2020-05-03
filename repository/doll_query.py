class DollQuery():
    '''複数テーブルに対する参照を管理するクラス
    もっとたくさんクエリが必要になってきたら分割を考える
    interfaceは省略する

    Args:
        conn (pymysql.Connection): DBへのコネクション
        doll_id (str): 起動中のdoll id
        today (str): 処理実行日
    '''

    def __init__(self, conn, doll_id, today):
        self.conn = conn
        self.doll_id = doll_id
        self.today = today

    def load_daily_action_results(self, doll_group, target_day):
        '''指定日のアクション結果を取得する

        Args:
            doll_group (str): 集計対象のdoll group. まとめて一括集計される
            target_day (str; yyyymmdd): 集計するアクションの日付

        Returns:
            dict[]: 対象の doll group に属するdoll の当日のアクション集計
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

    def load_next_sleeping_doll(self):
        '''起動条件を満たす停止中のdollから、最終起動時間が一番古いdollを呼び出す
        要求action回数一応渡しているけど、現状Dollの具象クラスに埋め込みにしてる

        Returns:
            dict: 対象の doll group に属するdoll の当日のアクション集計
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                WITH today_actions as (
                    SELECT
                        doll_id, post, dm, fav, follow,
                        unfollow, others, summary_cnt, is_blocked
                    FROM
                        action_counters
                    WHERE
                        operated_on = %s
                )

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
                        LEFT JOIN today_actions t3 ON t1.doll_id = t3.doll_id
                WHERE
                    t1.is_running = 0 and
                    t2.fav_per_day + t2.follow_per_day + t2.unfollow_per_day > ifnull(t3.fav, 0) + ifnull(t3.follow, 0) + ifnull(t3.unfollow, 0)
                ORDER BY
                    t1.last_booted_at
                ''', (self.today,))
            res = cursor.fetchone()
        return res
