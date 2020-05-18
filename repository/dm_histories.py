class DmHistoriesRepository():
    '''DM関連repositoryの集約クラス
    interfaceは省略する

    * dm_histories

    Args:
        conn (pymysql.Connection): DBへのコネクション
        doll_id (str): 起動中のdoll id
        today (str): 処理実行日
    '''

    def __init__(self, conn, doll_id, today):
        self.conn = conn
        self.doll_id = doll_id
        self.today = today

    def add_dm_sending(self, sent_from, sent_to, msg):
        '''DMの送信を履歴へ追加する

        Args:
            sent_from (str): 送信元インスタID
            sent_to (str): 送信先インスタID
            msg (str): 送信したメッセージ

        Returns:
            dict: 集計報告用のDriver設定
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO dm_histories (
                    sent_from, sent_to, message, created_at)
                VALUES
                    (%s, %s, %s, now())
                ''', (sent_from, sent_to, msg))
            self.conn.commit()

    def load_messages(self, sent_from, sent_to, limit):
        '''指定の組み合わせでやり取りされたDMを取得する

        Args:
            sent_from (str): 送信元インスタID
            sent_to (str): 送信先インスタID
            limit (str): 取得する最大件数
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    message
                FROM
                    dm_histories
                WHERE
                    sent_from = %s and
                    sent_to = %s
                ORDER BY
                    created_at DESC
                LIMIT
                    %s
            ''', (sent_from, sent_to, limit))
            res = cursor.fetchall()
        return res
