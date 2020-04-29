from automata.adoptor.abilities import Abilities
from automata.doll.nine_japan import NineJapan


class Collector():
    '''アクション回数の集計クラス

    Args:
        target_day (str): アクション集計対象日
    '''

    def __init__(self, target_day):
        self.target_day = target_day
        self.ab = Abilities('collector')
        self.ab.setup_master()

    def save_action_results(self):
        '''アクションの集計を呼び出す
        詳細な実装は各Doll実装に組み込んで実行制御を管理する
        '''
        NineJapan.save_results(self.ab.dao, self.ab.logger, self.target_day, 'nine_japan')

        # sqlite3は同時接続に強くないらしいので、使い終わったら接続を早めに閉じておく
        self.ab.dao.conn.close()
