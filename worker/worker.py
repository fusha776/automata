from time import sleep
from datetime import datetime
from automata.workflow.facade import Facade
# from automata.workflow.workflow import WorkFlow
# from automata.common.exception import ActionBlockException


class Worker():
    '''アクションフローを制御するクラス
    '''

    def __init__(self, worker_id, *args, **kwargs):
        self.facade = Facade(worker_id=worker_id)
        self.args = args
        self.kwargs = kwargs

    def operate(self):
        '''各ワーカー別のworkflow動作を設定する
        '''
        raise NotImplementedError

    def select_worker_id(self):
        '''当日のアクション状況と最終実行日時から以下を決定する
        * 起動する worker_id
        * 実行する各アクションの件数
        '''
        # TODO: 実装する
        # 今は手打ちで流している、自動起動のタイミングで実装が必須になるはず
        pass

    def create_worker(self, worker_id):
        '''上記で選定されたworker_id のworkerを立ち上げる
        このあたり、別のモジュールへ分けた方が良さそう
        '''
        pass

    def check_action_blocked(self):
        '''アクションブロックの発生を確認する
        ブロックのサンプルが得られるまで暫定的

        Returns:
            bool: アクションブロック中 -> True
        '''
        is_blocked = False
        el = self.facade.abilities.driver.find_elements_by_xpath('//*[contains(text(), "ブロック")]')
        if el:
            # body = self.wf.pixel.driver.find_elements_by_id('com.instagram.android:id/dialog_body') もう一度要素確認したい
            self.facade.abilities.logger.debug(f'アクションのブロックを検知 {self.wf.worker_id}: {el[0].text}.')
            is_blocked = True
        else:
            if len(el) >= 1:
                self.facade.abilities.logger.debug(f'アクションブロック以外の理由でダイアログ付エラーが発生. メッセージ: {el[0].text}')
        return is_blocked

    def run(self):
        '''定義されたアクションを実行する
        '''
        try:
            self.facade.switch_to_instagram_home()
            sleep(3)
            self.facade.abilities.modal.turn_on()
            self.operate(*self.args, **self.kwargs)
        except Exception:
            self.facade.abilities.logger.error('フロー実行中にエラーが発生', exc_info=True)
            self.facade.abilities.logger.debug(f'発生したページ: {self.facade.abilities.driver.current_url}')

            # 垢ブロックチェック
            is_blocked = self.check_action_blocked()
            if is_blocked:
                self.abilities.dao.put_blocked_mark()

            # URL が取得できないか試す
            # スクリーンショットを保存
            # w = self.facade.abilities.driver.execute_script('return document.body.scrollWidth')
            # h = self.facade.abilities.driver.execute_script('return document.body.scrollHeight')
            # self.facade.abilities.driver.set_window_size(w, h)
            ss_dir = f'./log/{self.facade.abilities.worker_id}/screenshots'
            self.facade.abilities.driver.save_screenshot(f'{ss_dir}/screenshot_{datetime.now().strftime("%Y%m%d%H%M%S")}.png')
        finally:
            # with open('./page_source.log', 'w', encoding='utf8') as f:
            #     f.write(wf.pixel.driver.page_source)
            worker_id = self.facade.abilities.worker_id
            login_id = self.facade.abilities.login_id
            self.facade.abilities.logger.debug(f'AUTOMATA is terminated. worker_id: {worker_id}, login id: {login_id}')
            self.facade.abilities.driver.close()
            self.facade.abilities.driver.quit()
