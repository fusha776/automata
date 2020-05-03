from automata.common.settings import CACHED_TOUCHED_USER_SIZE


class RecentTouchedHistoriesRepository():
    '''recent_touched_histories の repositoryクラス
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

    def add_recent_touched_user(self, insta_id, is_private):
        '''直近で何らかのアクションを取ったユーザを追加する
        同じユーザへ何度も当たらないための処置（鍵アカのskipとかにも使えます）
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO
                    recent_touched_histories
                VALUES
                    (%s, %s, %s, now())
                ON DUPLICATE KEY UPDATE
                    checked_at = now()
                ''', (self.doll_id, insta_id, is_private)
            )
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
