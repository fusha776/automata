class DollStatusRepository():
    '''doll_status の repositoryクラス
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

    def lock_doll(self):
        '''dollのステータスを起動中にする

        * 起動ロック中にする（同時起動を止める）
        * 最終起動日と当日の起動回数を更新する
        '''
        with self.conn.cursor() as cursor:
            # 最終実行日時を更新値で評価しないように独立して実行する
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    today_booted_times =
                        CASE
                            WHEN DATE_FORMAT(last_booted_at, %s) = %s THEN today_booted_times + 1
                            ELSE 1
                        END,
                    is_running = 1
                WHERE
                    doll_id = %s
                ''', ('%Y%m%d', self.today, self.doll_id))

            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = now()
                WHERE
                    doll_id = %s
                ''', (self.doll_id,))
            self.conn.commit()

    def unlock_doll(self):
        '''dollのステータスを停止中にする
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = now(),
                    is_running = 0
                WHERE
                    doll_id = %s
                ''', (self.doll_id,))
            self.conn.commit()

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
                    is_blocked, is_needed_to_relogin
                FROM
                    doll_status
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            res = cursor.fetchone()
        return res

    def set_blocked_mark(self):
        '''アクションブロックを検知した際に、マークを付ける
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    is_blocked = 1
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            self.conn.commit()

    def reset_blocked_mark(self):
        '''DBの論理blockを解除して起動可能ステータスにする
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    is_blocked = 0,
                    is_needed_to_relogin = 0
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            self.conn.commit()

    def check_natural_unblock(self):
        '''自然ブロック解除を試す
        失敗したときのために、再ログインフラグをセットする
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    is_blocked = 0,
                    is_needed_to_relogin = 1
                WHERE
                    doll_id = %s
            ''', (self.doll_id,))
            self.conn.commit()

    def update_booted_dt(self, target_doll_id):
        '''最終起動日時を更新する

        Args:
            target_doll_id (str): 対象のDoll ID
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    doll_status
                SET
                    last_booted_at = now()
                WHERE
                    doll_id = %s
                ''', (target_doll_id,))
            self.conn.commit()
