class FollowiingStatusRepository():
    '''following_status の repositoryクラス
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

    def add_following(self, insta_id, has_followed=1, is_follower=0):
        '''フォロー中を追加する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO following_status (
                    doll_id, instagram_id, has_followed, is_follower, created_at, updated_at)
                VALUES
                    (%s, %s, %s, %s, now(), now())
                ''', (self.doll_id, insta_id, has_followed, is_follower))
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
                    500
            ''', (self.doll_id,))
            res = cursor.fetchall()
        return res
