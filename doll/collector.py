import os
import pathlib
from datetime import datetime
from automata.common.utils import create_logger
from automata.common.settings import REPORTING_DIR
from automata.doll.nine_japan import NineJapan
from automata.doll.utils import fillna
from automata.repository.doll_query import DollQuery


class Collector():
    '''アクション回数の集計クラス

    Args:
        conn (Connection): DBへのコネクション。渡されなければ生成する。
        target_day (str): アクション集計対象日
    '''

    def __init__(self, conn, today):
        self.logger = create_logger('collector', today)
        self.today = today

        self.conn = conn
        self.doll_query = DollQuery(self.conn, 'condoctor', self.today)

    def save(self):
        '''当日の結果を保存
        '''
        self.make_action_results(NineJapan, 'nine_japan')

    def save_interim(self):
        '''途中経過を保存
        '''
        self.make_interim_results('nine_japan')

    def make_action_results(self, doll_class, doll_group):
        '''アクションの集計を保存する
        詳細な実装は各Doll実装に組み込んで実行制御を管理する
        '''
        actions = self.doll_query.load_daily_action_results(doll_group, self.today)
        msg = doll_class.format(self.today, actions)

        pathlib.Path(f'{REPORTING_DIR}/{self.today}').mkdir(parents=True, exist_ok=True)
        result_path = f'{REPORTING_DIR}/{self.today}/{doll_group}_{self.today}.txt'
        if not os.path.exists(result_path):
            with open(result_path, 'w', encoding='utf8') as f:
                f.write(msg)
                self.logger.info(f'{doll_group} result report is saved.')
        else:
            self.logger.info(f'{doll_group} result report was already saved.')

    def make_interim_results(self, doll_group):
        '''途中経過確認用に、省略版の集計レポートを作成する
        '''
        doll_records = self.doll_query.load_daily_action_results(doll_group, self.today)
        t_date = datetime.strptime(self.today, '%Y%m%d')

        interim_msg = f'{t_date.month}/{t_date.day}\n'
        for idx, action in enumerate(doll_records):
            summary_cnt = fillna(action['summary_cnt'])
            block_msg = 'blocked' if action['is_blocked'] == 1 else ''
            interim_msg += f'{action["login_id"]}: {summary_cnt} {block_msg}\n'

        pathlib.Path(f'{REPORTING_DIR}/{self.today}').mkdir(parents=True, exist_ok=True)
        interim_path = f'{REPORTING_DIR}/{self.today}/{doll_group}_interim.txt'
        if not os.path.exists(interim_path):
            with open(interim_path, 'w', encoding='utf8') as f:
                f.write(interim_msg)
                self.logger.info(f'{doll_group} interim report is saved.')
        else:
            self.logger.info(f'{doll_group} interim report was already saved.')
