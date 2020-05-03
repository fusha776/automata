import os
import pathlib
from automata.common.utils import generate_logger
from automata.doll.nine_japan import NineJapan

from automata.repository.doll_query import DollQuery


class Collector():
    '''アクション回数の集計クラス

    Args:
        conn (Connection): DBへのコネクション。渡されなければ生成する。
        target_day (str): アクション集計対象日
    '''

    def __init__(self, conn, target_day, today):
        self.logger = generate_logger('collector', today)
        self.target_day = target_day

        self.conn = conn
        self.doll_query = DollQuery(self.conn, 'condoctor', today)

    def save(self):
        self.make_action_results(NineJapan, 'nine_japan')

    def make_action_results(self, doll_class, doll_group):
        '''アクションの集計を呼び出す
        詳細な実装は各Doll実装に組み込んで実行制御を管理する
        '''
        actions = self.doll_query.load_daily_action_results(doll_group, self.target_day)
        msg = doll_class.format(self.target_day, actions)

        pathlib.Path(f'./results/{self.target_day}').mkdir(parents=True, exist_ok=True)
        result_path = f'./results/{self.target_day}/{doll_group}_{self.target_day}.txt'
        if not os.path.exists(result_path):
            with open(result_path, 'w', encoding='utf8') as f:
                f.write(msg)
                self.logger.info(f'{doll_group} results is saved.')
        else:
            self.logger.info(f'{doll_group} results was already saved.')
