import pymysql
from automata.common.settings import LAKE_ROOT_PATH


class Model():
    '''DBのテーブル作成用クラス
    基本的に一度しか実行しないが、テーブル定義の確認や再生成のためにコード管理
    '''

    def __init__(self):
        # データベース接続とカーソル生成
        self.conn = pymysql.connect(host='localhost',
                                    user='root',
                                    password='root',
                                    db='automata',
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)

        # 自動コミットにする場合は下記を指定（コメントアウトを解除のこと）
        # connection.isolation_level = None

    def create_tables(self):
        dm_messages_mst = '''CREATE TABLE IF NOT EXISTS dm_messages_mst (
            dm_message_id VARCHAR PRIMARY KEY,
            message VARCHAR,
            is_activated TINYINT
        )'''

        following_status = '''CREATE TABLE IF NOT EXISTS following_status (
            doll_id VARCHAR(32),
            instagram_id VARCHAR(32),
            has_followed TINYINT,
            is_follower TINYINT,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (doll_id, instagram_id)
        )'''

        hashtag_groups_mst = '''CREATE TABLE IF NOT EXISTS hashtag_groups_mst (
            hashtag_group VARCHAR,
            hashtag VARCHAR,
            PRIMARY KEY (hashtag_group, hashtag)
        )'''

        doll_settings = '''CREATE TABLE IF NOT EXISTS doll_settings (
            doll_id VARCHAR(32) PRIMARY KEY,
            description VARCHAR(255),
            login_id VARCHAR(32),
            label VARCHAR(32),
            password VARCHAR(32),
            client VARCHAR(32),
            browser_data_dir VARCHAR(128),
            profile_dir VARCHAR(64),
            device_name VARCHAR(32),
            doll_class VARCHAR(32),
            doll_group VARCHAR(32),
            doll_group_lake_path VARCHAR(128),
            dm_message_id VARCHAR(32),
            hashtag_group VARCHAR(32),
            post_per_day SMALLINT,
            dm_per_day SMALLINT,
            fav_per_day SMALLINT,
            follow_per_day SMALLINT,
            unfollow_per_day SMALLINT,
            post_per_boot SMALLINT,
            dm_per_boot SMALLINT,
            fav_per_boot SMALLINT,
            follow_per_boot SMALLINT,
            unfollow_per_boot SMALLINT
        )'''

        action_counters = '''CREATE TABLE IF NOT EXISTS action_counters (
            doll_id VARCHAR(32),
            operated_on VARCHAR(8),
            post SMALLINT,
            dm SMALLINT,
            fav SMALLINT,
            follow SMALLINT,
            unfollow SMALLINT,
            others SMALLINT,
            summary_cnt SMALLINT,
            is_blocked TINYINT,
            PRIMARY KEY (doll_id, operated_on)
        )'''

        ng_users = '''CREATE TABLE IF NOT EXISTS ng_users (
            doll_group VARCHAR(32),
            instagram_id VARCHAR(32),
            created_on VARCHAR(8),
            is_permanent TINYINT,
            PRIMARY KEY (doll_group, instagram_id)
        )'''

        doll_status = '''
            CREATE TABLE IF NOT EXISTS doll_status (
            doll_id VARCHAR(32) PRIMARY KEY,
            last_booted_at DATETIME,
            today_booted_times TINYINT,
            is_running TINYINT,
            is_blocked TINYINT,
            is_needed_to_relogin TINYINT
        )'''

        recent_touched_histories = '''
            CREATE TABLE IF NOT EXISTS recent_touched_histories (
            doll_id VARCHAR(32),
            instagram_id VARCHAR(32),
            is_private TINYINT,
            checked_at DATETIME,
            PRIMARY KEY (doll_id, instagram_id)
        )'''

        reporter_settings = '''CREATE TABLE IF NOT EXISTS reporter_settings (
            doll_id VARCHAR(32) PRIMARY KEY,
            login_id VARCHAR(32),
            password VARCHAR(32),
            browser_data_dir VARCHAR(128),
            device_name VARCHAR(32),
            monitor_room VARCHAR(16)
        )'''

        report_mappings = '''CREATE TABLE IF NOT EXISTS report_mappings (
            doll_group VARCHAR(32) PRIMARY KEY,
            channel VARCHAR(32),
            destination VARCHAR(32),
            created_at DATETIME,
            updated_at DATETIME
        )'''

        reporting_histories = '''CREATE TABLE IF NOT EXISTS reporting_histories (
            doll_group VARCHAR(32),
            reported_on VARCHAR(8),
            channel VARCHAR(32),
            destination VARCHAR(32),
            created_at DATETIME,
            PRIMARY KEY (doll_group, reported_on)
       )'''

        account_research = '''CREATE TABLE IF NOT EXISTS account_research (
            doll_group VARCHAR(32),
            research_id VARCHAR(32),
            doll_id VARCHAR(32),
            instagram_id VARCHAR(32),
            label VARCHAR(128),
            follower MEDIUMINT,
            following SMALLINT,
            bio VARCHAR(255),
            website TEXT,
            recent_fav_1 MEDIUMINT,
            recent_fav_2 MEDIUMINT,
            recent_fav_3 MEDIUMINT,
            recent_fav_4 MEDIUMINT,
            recent_fav_5 MEDIUMINT,
            created_at DATETIME,
            PRIMARY KEY (doll_group, research_id, instagram_id)
            ) DEFAULT CHARSET=utf8mb4
       '''

        research_work = '''CREATE TABLE IF NOT EXISTS research_work (
            research_id VARCHAR(32),
            instagram_id VARCHAR(32),
            label VARCHAR(128),
            follower MEDIUMINT,
            following SMALLINT,
            bio VARCHAR(255),
            website TEXT,
            recent_fav_1 MEDIUMINT,
            recent_fav_2 MEDIUMINT,
            recent_fav_3 MEDIUMINT,
            recent_fav_4 MEDIUMINT,
            recent_fav_5 MEDIUMINT,
            created_at DATETIME,
            PRIMARY KEY (research_id, instagram_id)
            ) DEFAULT CHARSET=utf8mb4
       '''
        dm_histories = '''CREATE TABLE IF NOT EXISTS dm_histories (
            id INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
            sent_from VARCHAR(32),
            sent_to VARCHAR(32),
            message TEXT,
            created_at DATETIME
        )'''

        _ = dm_messages_mst, hashtag_groups_mst, ng_users  # 現在未使用テーブル、Lintのエラー避け
        with self.conn.cursor() as cursor:
            cursor.execute(following_status)
            cursor.execute(doll_settings)
            cursor.execute(action_counters)
            cursor.execute(doll_status)
            cursor.execute(recent_touched_histories)
            cursor.execute(reporter_settings)
            cursor.execute(report_mappings)
            cursor.execute(reporting_histories)
            cursor.execute(account_research)
            cursor.execute(research_work)
            cursor.execute(dm_histories)
            # cursor.execute(dm_messages_mst)
            # cursor.execute(hashtag_groups_mst)
            # cursor.execute(ng_users)

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

        with self.conn.cursor() as cursor:
            cursor.executemany(doll_settings, dolls)


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
