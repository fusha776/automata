class ReporterSettingsRepository():
    '''reporter関連repositoryの集約クラス
    interfaceは省略する

    * reporter_settings
    * report_mappings
    * reporting_histories

    Args:
        conn (pymysql.Connection): DBへのコネクション
        doll_id (str): 起動中のdoll id
        today (str): 処理実行日
    '''

    def __init__(self, conn, doll_id, today):
        self.conn = conn
        self.doll_id = doll_id
        self.today = today

    def load_reporter_settings(self):
        '''集計報告用のDriver設定を取得する

        Returns:
            dict: 集計報告用のDriver設定
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    login_id,
                    password,
                    browser_data_dir,
                    device_name,
                    monitor_room
                FROM
                    reporter_settings
            ''')
            res = cursor.fetchone()
        return res

    def load_report_mappings(self, doll_group):
        '''対象の Doll Group に対する、集計報告先の設定を取得する

        Returns:
            dict: 集計報告用のDriver設定
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    channel,
                    destination
                FROM
                    report_mappings
                WHERE
                    doll_group = %s
            ''', (doll_group,))
            res = cursor.fetchone()
        return res

    def load_history(self, doll_group, target_day):
        '''対象日の対象 doll group のレポート送信履歴を取得する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    channel,
                    destination
                FROM
                    reporting_histories
                WHERE
                    doll_group = %s and
                    reported_on = %s
            ''', (doll_group, target_day))
            res = cursor.fetchone()
        return res

    def register_sent_report(self, doll_group, channel, destination):
        '''送信済みレコードを生成する
        '''
        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO
                    reporting_histories
                VALUES
                    (%s, %s, %s, %s, now())
                ''', (doll_group, self.today, channel, destination))
            self.conn.commit()
