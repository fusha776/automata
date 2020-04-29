import sqlite3
from automata.common.settings import DATABASE_PATH, LAKE_ROOT_PATH


class Model():
    '''DBのテーブル作成用クラス
    基本的に一度しか実行しないが、テーブル定義の確認や再生成のためにコード管理
    '''

    def __init__(self):
        # データベース接続とカーソル生成
        self.conn = sqlite3.connect(DATABASE_PATH)

        self.conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row

        # 自動コミットにする場合は下記を指定（コメントアウトを解除のこと）
        # connection.isolation_level = None
        self.cursor = self.conn.cursor()

    def create_tables(self):
        dm_histories = '''CREATE TABLE IF NOT EXISTS dm_histories (
            doll_id TEXT,
            instagram_id TEXT,
            dm_message_id TEXT,
            sent_on TEXT,
            PRIMARY KEY (doll_id, instagram_id)
        )'''

        dm_messages_mst = '''CREATE TABLE IF NOT EXISTS dm_messages_mst (
            dm_message_id TEXT PRIMARY KEY,
            message TEXT,
            is_activated INTEGER
        )'''

        following_status = '''CREATE TABLE IF NOT EXISTS following_status (
            doll_id TEXT,
            instagram_id TEXT,
            has_followed INTEGER,
            is_follower INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (doll_id, instagram_id)
        )'''

        hashtag_groups_mst = '''CREATE TABLE IF NOT EXISTS hashtag_groups_mst (
            hashtag_group TEXT,
            hashtag TEXT,
            PRIMARY KEY (hashtag_group, hashtag)
        )'''

        doll_settings = '''CREATE TABLE IF NOT EXISTS doll_settings (
            doll_id TEXT PRIMARY KEY,
            description TEXT,
            login_id TEXT,
            label TEXT,
            password TEXT,
            client TEXT,
            browser_data_dir TEXT,
            profile_dir TEXT,
            device_name TEXT,
            doll_class TEXT,
            doll_group TEXT,
            doll_group_lake_path TEXT,
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
            doll_id TEXT,
            operated_on TEXT,
            post INTEGER,
            dm INTEGER,
            fav INTEGER,
            follow INTEGER,
            unfollow INTEGER,
            others INTEGER,
            summary_cnt INTEGER,
            is_blocked INTEGER,
            PRIMARY KEY (doll_id, operated_on)
        )'''

        ng_users = '''CREATE TABLE IF NOT EXISTS ng_users (
            doll_group TEXT,
            instagram_id TEXT,
            created_on TEXT,
            is_permanent INTEGER,
            PRIMARY KEY (doll_group, instagram_id)
        )'''

        doll_status = '''
            CREATE TABLE IF NOT EXISTS doll_status (
            doll_id TEXT PRIMARY KEY,
            last_booted_at TIMESTAMP,
            today_booted_times INTEGER,
            is_running INTEGER,
            is_blocked INTEGER
        )'''

        recent_touched_histories = '''
            CREATE TABLE IF NOT EXISTS recent_touched_histories (
            doll_id TEXT,
            instagram_id TEXT,
            is_private INTEGER,
            checked_at TIMESTAMP,
            PRIMARY KEY (doll_id, instagram_id)
        )'''

        with self.conn:
            _ = dm_histories, dm_messages_mst, hashtag_groups_mst, ng_users  # 現在未使用テーブル、Lintのエラー避け
            # self.conn.execute(dm_histories)
            # self.conn.execute(dm_messages_mst)
            self.conn.execute(following_status)
            # self.conn.execute(hashtag_groups_mst)
            self.conn.execute(doll_settings)
            self.conn.execute(action_counters)
            # self.conn.execute(ng_users)
            self.conn.execute(doll_status)
            self.conn.execute(recent_touched_histories)

    def migrate(self):
        '''マスタ他のレコードを、実行するたびに洗い替えする
        '''

        doll_settings = '''INSERT OR REPLACE INTO doll_settings (
                                 doll_id, description, login_id, label, password, client,
                                 browser_data_dir, profile_dir, device_name,
                                 doll_group, doll_group_lake_path, dm_message_id, hashtag_group,
                                 post_per_day, dm_per_day, fav_per_day, follow_per_day, unfollow_per_day,
                                 post_per_boot, dm_per_boot, fav_per_boot, follow_per_boot, unfollow_per_boot)
                             VALUES(?, ?, ?, ?, ?, ?,
                                    ?, ?, ?,
                                    ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?)
        '''
        dolls = [('arc_corp_1', 'DM送信 No.1（アークコーポレーション）', 'poyomaru555', 'ぽよまる', 'itsumono_pass', 'client動作テスト用',
                  "c:/Users/bell/python/project/insta/chrome_profiles", "Profile 1", "Pixel 2",
                  'dm_arc', f'{LAKE_ROOT_PATH}/dm_arc', 'apparel_arc', None,
                  2, 20, None, None, None,
                  1, 10, None, None, None)]

        with self.conn:
            self.conn.executemany(doll_settings, dolls)


if __name__ == '__main__':
    model = Model()
    model.create_tables()
    model.migrate()

'''
doll追加のサンプルSQL
INSERT INTO doll_settings
VALUES
("nine_japan_3", "フォロー、アンフォロー、いいね", "poyomaru555", "ぽよまる", "itsumono_pass", "厚いクライアント",
 "d:/python/project/insta/chromes/poyomaru", "Profile 2", "Pixel 2", "DollClass",
 "action_nj", "c/Users/bell/python/project/instagram/appium/lake/action_nj", "None", "None",
 0, 0, 20, 100, 20, 0, 0, 10, 50, 10);
'''
