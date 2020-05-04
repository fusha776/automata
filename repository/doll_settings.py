class DollSettingsRepository():
    '''doll_settings の repositoryクラス
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

    def load_doll_settings(self):
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
