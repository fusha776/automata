import os
import json
import pathlib
from time import sleep
from datetime import datetime
from automata.workflow.facade import Facade
from automata.common.settings import DOLL_PARAMS_DIR
# from automata.workflow.workflow import WorkFlow
# from automata.common.exception import ActionBlockException


class Doll():
    '''アクションフローを制御するクラス
    '''

    def __init__(self, doll_id):
        self.doll_id = doll_id

    def operate(self):
        '''各doll別のworkflow動作を設定する
        '''
        raise NotImplementedError

    def setup(self):
        '''doll_id を参照してDollを起動する
        * Abilityの生成
        * JSONパラメータのロード

        パラメータファイルは `実装class名.json` でガチガチに命名規約が決まってるので注意
        '''
        self.facade = Facade(doll_id=self.doll_id)

        with open(f'{DOLL_PARAMS_DIR}/{self.__class__.__name__}.json', 'r', encoding='utf8') as f:
            self.params = json.load(f)[self.doll_id]

    def check_chips_and_params(self):
        '''JSON指定の login id が、起動した doll_settings の login id と一致しているか確認する
        login id が変わった際にパラメータ変更が反映されていないエラーをチェック

        パラメータもDB管理するためには動作が固まっている必要がありますが、
        これはDollによって変動することが予想されるため、DB と JSON を併用して整合性チェックを入れます
        '''
        param_id = self.params['login_id']
        db_id = self.facade.abilities.login_id
        if param_id != db_id:
            self.facade.abilities.logger.error(f'DB と JSON で Doll の login id 設定が不一致しました. JSON: {param_id}, DB: {db_id}')
            return False
        return True

    def run(self):
        '''定義されたアクションを実行する
        '''
        try:
            self.setup()
            if self.check_chips_and_params():
                # Instagram Home へ移動
                self.facade.switch_to_instagram_home()
                self.facade.abilities.modal.turn_on()

                # 前日ブロック中なら再ログインする
                self.check_block_status()

                # 処理を開始
                self.operate()
        except Exception:
            self.facade.abilities.logger.error('フロー実行中にエラーが発生', exc_info=True)
            self.facade.abilities.logger.debug(f'発生したページ: {self.facade.abilities.driver.current_url}')

            # スクリーンショットを保存
            ss_dir = f'./log/{self.facade.abilities.doll_id}/screenshots'
            self.facade.abilities.driver.save_screenshot(f'{ss_dir}/screenshot_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')

            # htmlの保存（※保留中、動作が安定してきたら追加するかも）
            # with open('./page_source.log', 'w', encoding='utf8') as f:
            #     f.write(wf.pixel.driver.page_source)
        finally:
            self.facade.abilities.close()

    def check_block_status(self):
        '''前日ブロックだったら再ログインする
        '''
        is_blocked = self.facade.abilities.dao.load_block_status()['is_blocked']  # bool(1) -> True
        if is_blocked:
            self._relogin()

    def _relogin(self):
        '''ブロック状態のリセットのため、ログアウト - ログイン を行う
        '''
        # ログアウト
        # たまに失敗するみたいだけど理由不明.
        # ブラウザキャッシュを消して対処した方が良いかも、でもそれだと多重ログインでブロックされやすくなるかも
        self.facade.abilities.profile.switch_to_user_profile(self.facade.abilities.login_id)
        self.facade.abilities.profile.logout()

        # 再ログイン
        self.facade.switch_to_instagram_home()

        # ここまで成功したらDB更新
        self.facade.abilities.logger.debug(f'ブロック状態のため再ログインを実施')
        self.facade.abilities.dao.reset_blocked_mark()

    @classmethod
    def save_results(cls, dao, logger, target_day, doll_group):
        '''アクションの集計を出力する
        '''
        actions = dao.load_daily_action_results(doll_group, target_day)
        msg = cls.format(target_day, actions)

        pathlib.Path(f'./results/{target_day}').mkdir(parents=True, exist_ok=True)
        result_path = f'./results/{target_day}/{doll_group}_{target_day}.txt'
        if not os.path.exists(result_path):
            with open(result_path, 'w', encoding='utf8') as f:
                f.write(msg)
                logger.info('result is saved.')
        else:
            logger.info('result was already saved.')

    @classmethod
    def format(cls, target_day, doll_records):
        '''レコードを受け取って出力テキストへ整形する

        Args:
            target_day (str): アクション集計対象日
            doll_records (Row[]): アクションが集計されたdoll毎のレコード. 取得できるカラムは以下.

            login_id,　label, client, doll_group,
            post, dm, fav, follow, unfollow, others, summary_cnt, is_blocked}
        '''
        raise NotImplementedError
