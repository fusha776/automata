import sqlite3
from automata.common.settings import DATABASE_PATH, LAKE_ROOT_PATH


class Model():
    '''DBのテーブル作成用クラス
    基本的に一度しか実行しないが、テーブル定義の確認や再生成のためにコード管理
    '''

    def __init__(self):
        # データベース接続とカーソル生成
        self.conn = sqlite3.connect(DATABASE_PATH)
        # 自動コミットにする場合は下記を指定（コメントアウトを解除のこと）
        # connection.isolation_level = None
        self.cursor = self.conn.cursor()

    def create_tables(self):
        dm_histories = '''CREATE TABLE IF NOT EXISTS dm_histories (
            worker_id TEXT,
            instagram_id TEXT,
            dm_message_id TEXT,
            sent_on TEXT,
            PRIMARY KEY (worker_id, instagram_id)
        )'''

        dm_messages_mst = '''CREATE TABLE IF NOT EXISTS dm_messages_mst (
            dm_message_id TEXT PRIMARY KEY,
            message TEXT,
            is_activated INTEGER
        )'''

        following_status = '''CREATE TABLE IF NOT EXISTS following_status (
            worker_id TEXT,
            instagram_id TEXT,
            has_followed INTEGER,
            is_follower INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (worker_id, instagram_id)
        )'''

        hashtag_groups_mst = '''CREATE TABLE IF NOT EXISTS hashtag_groups_mst (
            hashtag_group TEXT,
            hashtag TEXT,
            PRIMARY KEY (hashtag_group, hashtag)
        )'''

        worker_settings = '''CREATE TABLE IF NOT EXISTS worker_settings (
            worker_id TEXT PRIMARY KEY,
            description TEXT,
            login_id TEXT,
            label TEXT,
            password TEXT,
            client TEXT,
            worker_group TEXT,
            worker_group_lake_path TEXT,
            dm_message_id TEXT,
            hashtag_group TEXT,
            post_per_day INTEGER,
            dm_per_day INTEGER,
            fav_per_day INTEGER,
            follow_per_day INTEGER,
            unfollow_per_day INTEGER,
            post_per_boot INTEGER,
            dm_per_boot INTEGER,
            fav_per_boot INTEGER,
            follow_per_boot INTEGER,
            unfollow_per_boot INTEGER
        )'''

        action_counters = '''CREATE TABLE IF NOT EXISTS action_counters (
            worker_id TEXT,
            operated_on TEXT,
            post INTEGER,
            dm INTEGER,
            fav INTEGER,
            follow INTEGER,
            unfollow INTEGER,
            others INTEGER,
            summary_cnt INTEGER,
            PRIMARY KEY (worker_id, operated_on)
        )'''

        ng_users = '''CREATE TABLE IF NOT EXISTS ng_users (
            worker_group TEXT,
            instagram_id TEXT,
            created_on TEXT,
            is_permanent INTEGER,
            PRIMARY KEY (worker_group, instagram_id)
        )'''

        worker_status = '''
            CREATE TABLE IF NOT EXISTS worker_status (
            worker_id TEXT,
            last_booted_at TIMESTAMP,
            today_booted_times INTEGER,
            PRIMARY KEY (worker_id)
        )'''

        with self.conn:
            self.conn.execute(dm_histories)
            self.conn.execute(dm_messages_mst)
            self.conn.execute(following_status)
            self.conn.execute(hashtag_groups_mst)
            self.conn.execute(worker_settings)
            self.conn.execute(action_counters)
            self.conn.execute(ng_users)
            self.conn.execute(worker_status)

    def migrate(self):
        '''マスタ他のレコードを、実行するたびに洗い替えする
        '''

        worker_settings = '''INSERT OR REPLACE INTO worker_settings (
                                 worker_id, description, login_id, label, password, client, worker_group,
                                 worker_group_lake_path, dm_message_id, hashtag_group,
                                 post_per_day, dm_per_day, fav_per_day, follow_per_day, unfollow_per_day,
                                 post_per_boot, dm_per_boot, fav_per_boot, follow_per_boot, unfollow_per_boot)
                             VALUES(?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?)
        '''
        workers = [('arc_corp_1', 'DM送信 No.1（アークコーポレーション）', 'poyomaru555', 'ぽよまる', 'itsumono', '動作テスト用', 'dm_arc',
                    f'{LAKE_ROOT_PATH}\\dm_arc', 'apparel_arc', None,
                    2, 20, None, None, None,
                    1, 10, None, None, None)]

        with self.conn:
            self.conn.executemany(worker_settings, workers)


if __name__ == '__main__':
    model = Model()
    model.create_tables()
    model.migrate()

'''
worker追加のサンプルSQL
INSERT INTO worker_settings
VALUES
("nine_japan_3", "フォロー、アンフォロー、いいね", "poyomaru555", "itsumono", "動作テスト", "action_nj",
                    "c/Users/bell/python/project/instagram/appium/lake/action_nj", "None", "None",
                    0, 0, 20, 100, 20,
                    0, 0, 10, 50, 10);
'''
