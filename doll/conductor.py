from datetime import datetime
from automata.apimediator.abilities import Abilities
from automata.doll.collector import Collector
from automata.common.settings import HOUR_SLEEPING_FROM, HOUR_SLEEPING_TO, BOOTING_INTERVAL_SECONDS

# 文字列 -> クラス の取得で使用しています
from automata.doll.nine_japan import NineJapan


class Conductor():
    '''バッチの実行を受け付け、どのdollを実行するか管理するクラス

    Args:
        test_mode (bool): True -> 起動条件を無視してdollを起動（テスト動作向け）
    '''

    def __init__(self, test_mode=False):
        self.today = datetime.now().strftime('%Y%m%d')
        self.test_mode = test_mode
        self.ab = Abilities('conductor')
        self.ab.setup_master()

    def select_doll(self):
        '''一時的にDBへつなぎ、当日のアクション状況と最終実行日時から起動するdollを決定する

        TODO:
            フェイルセーフ的に一定時間以上経過してたら無理やり起動させてみたいけど、
            いったん保留にしておく（この場合、cron側の長時間稼働kill設定と合わせる必要がある）
        '''
        now_dt = datetime.now()
        doll = self.ab.dao.load_next_sleeping_doll()
        if self.test_mode:
            return doll['doll_id'], doll['doll_class']
        # 起動条件を満たしていなければ終了
        if not doll:
            return None, None
        if HOUR_SLEEPING_FROM <= now_dt.hour <= HOUR_SLEEPING_TO:
            return None, None
        if (now_dt - doll['last_booted_at']).seconds < BOOTING_INTERVAL_SECONDS:
            return None, None
        return doll['doll_id'], doll['doll_class']

    def load_dolls_os_chip(self, class_name):
        '''dollのクラスを取得する
        '''
        return globals()[class_name] if class_name else None

    def activate_doll(self):
        '''dollを起動して実行する
        actionの要求回数はいったんDoll JSON で管理

        WARN:
            sqlite3は同時接続に強くないらしいので、使い終わったらconnを早めに閉じておく
        '''
        doll_id, class_name = self.select_doll()
        self.ab.dao.conn.close()

        if doll_id:
            self.ab.logger.info(f'doll {doll_id} starts up.')
            os_chip = self.load_dolls_os_chip(class_name)
            os_chip(doll_id).run()
        else:
            self.ab.logger.info('no doll is made activated.')

    def count_results(self):
        '''所定の時間になったら、当日のリザルトを集計する
        '''
        now_dt = datetime.now()
        # 活動時間ならskip
        if not (HOUR_SLEEPING_FROM <= now_dt.hour <= HOUR_SLEEPING_TO):
            return

        # アクションを集計
        collector = Collector(self.today)
        collector.save_action_results()

    def execute(self):
        '''dollの生成と結果カウントを実行する
        '''
        self.activate_doll()
        self.count_results()
