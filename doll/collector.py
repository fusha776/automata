from automata.doll.nine_japan import NineJapan


class Collector():
    '''アクション回数の集計クラス

    Args:
        target_day (str): アクション集計対象日
    '''

    def __init__(self, target_day):
        self.target_day = target_day

    def save_action_results(self):
        '''アクションの集計を呼び出す
        詳細な実装は各Doll実装に組み込んで実行制御を管理する
        '''
        NineJapan.save_results(self.target_day, 'nine_japan')
