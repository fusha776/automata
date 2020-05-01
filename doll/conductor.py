from datetime import datetime
from automata.adoptor.abilities import Abilities
from automata.doll.collector import Collector
from automata.common.settings import HOUR_SLEEPING_FROM, HOUR_SLEEPING_TO, BOOTING_INTERVAL_SECONDS, DOLLS_PARALLEL_LIMIT

# 文字列 -> クラス の取得で使用しています
from automata.doll.nine_japan import NineJapan


class Conductor():
    '''バッチの実行を受け付け、どのdollを実行するか管理するクラス

    Args:
        test_doll_id (str): 指定があれば、起動条件を無視して対象Dollを起動する
        test_doll_chips (str): テストDoll用の実装クラス名
    '''

    def __init__(self, test_doll_id=None, test_doll_chips=None):
        self.today = datetime.now().strftime('%Y%m%d')
        self.test_doll_id = test_doll_id
        self.test_doll_chips = test_doll_chips
        self.ab = Abilities('conductor')
        self.ab.setup_master()

    def activate_doll(self):
        '''dollを起動して実行する
        actionの要求回数はいったんDoll JSON で管理

        WARN:
            sqlite3は同時接続に強くないらしいので、使い終わったらconnを早めに閉じておく
        '''
        doll_id, class_name = self.select_doll()
        active_dolls = self.ab.dao.load_active_dolls()
        self.ab.dao.conn.close()

        if len(active_dolls) >= DOLLS_PARALLEL_LIMIT:
            self.ab.logger.info('active dolls has reached parallel limit.')
            return

        if not doll_id:
            self.ab.logger.info('there is no doll to activate.')
            return

        self.ab.logger.info(f'doll {doll_id} starts up.')
        os_chip = self.load_dolls_os_chip(class_name)
        os_chip(doll_id).run()

    def select_doll(self):
        '''一時的にDBへつなぎ、当日のアクション状況と最終実行日時から起動するdollを決定する

        TODO:
            フェイルセーフ的に一定時間以上経過してたら無理やり起動させてみたいけど、
            いったん保留にしておく（この場合、cron側の長時間稼働kill設定と合わせる必要がある）
        '''
        def load_next_doll_except_daily_blocked():
            '''当日ブロック中のDollを避けて次に起動するDollを取得する
            '''
            next_doll = self.ab.dao.load_next_sleeping_doll()
            if not next_doll:
                return None

            # 当日ブロック有りならskip
            if ((next_doll['is_blocked'] == 1) and
                    next_doll['last_booted_at'].strftime('%Y%m%d') == self.today):
                # 最終起動時間を更新し、別のDollを呼び出す
                self.ab.dao.update_last_booted_dt(next_doll['doll_id'])
                return load_next_doll_except_daily_blocked()

            # 有効なDollを取得
            return next_doll

        # デバッグ動作なら即返却
        if self.test_doll_id and self.test_doll_chips:
            return self.test_doll_id, self.test_doll_chips

        now_dt = datetime.now()
        doll = load_next_doll_except_daily_blocked()

        # 起動条件を満たしていなければ終了
        if not doll:
            return None, None
        if HOUR_SLEEPING_FROM <= now_dt.hour <= HOUR_SLEEPING_TO:
            return None, None
        if (now_dt - doll['last_booted_at']).total_seconds() < BOOTING_INTERVAL_SECONDS:
            return None, None
        return doll['doll_id'], doll['doll_class']

    def load_dolls_os_chip(self, class_name):
        '''dollのクラスを取得する
        '''
        return globals()[class_name] if class_name else None

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
