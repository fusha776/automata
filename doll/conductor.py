from datetime import datetime
from automata.dao.dao import Dao
from automata.common.settings import HOUR_SLEEPING_FROM, HOUR_SLEEPING_TO, BOOTING_INTERVAL_SECONDS

from automata.doll.nine_japan import NineJapan


class Conductor():
    '''バッチの実行を受け付け、どのdollを実行するか管理するクラス
    '''

    def __init__(self):
        self.now_dt = datetime.now()
        self.dao = Dao('root', self.now_dt.strftime('%Y%m%d'))
        self.doll_id, class_name = self.select_doll()
        self.os_chip = self.load_dolls_os_chip(class_name)
        self.dao.conn.close()

    def select_doll(self):
        '''一時的にDBへつなぎ、当日のアクション状況と最終実行日時から起動するdollを決定する

        TODO:
            フェイルセーフ的に一定時間以上経過してたら無理やり起動させてみたいけど、
            いったん保留にしておく（この場合、cron側の長時間稼働kill設定と合わせる必要がある）
        '''
        doll = self.dao.load_next_sleeping_doll()
        # 起動条件を満たしていなければ終了
        if not doll:
            return None, None
        # if HOUR_SLEEPING_FROM <= self.now_dt.hour <= HOUR_SLEEPING_TO:
        #     return None, None
        # if (self.now_dt - doll['last_booted_at']).seconds < BOOTING_INTERVAL_SECONDS:
        #     return None, None
        return doll['doll_id'], doll['doll_class']

    def load_dolls_os_chip(self, class_name):
        '''一時的にDBへつなぎ、dollのクラスを取得する
        '''
        return globals()[class_name] if class_name else None

    def activate_doll(self):
        '''dollを起動して実行する
        actionの要求回数はいったんDoll JSON で管理
        '''
        if self.doll_id:
            self.os_chip(self.doll_id).run()
        else:
            print('no doll is made activated.')
