from random import random
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import JavascriptException
from automata.common.settings import ACTION_WAIT_SECONDS, WAIT_LOADING_SECONDS


def wait(func):
    '''画面遷移前に一定秒停止させる（デコレータ）
    '''
    def wrapper(*args, **kwargs):
        # ランダムに停止させる
        sleep(ACTION_WAIT_SECONDS * (1 + 0.5 * random()))
        return func(*args, **kwargs)
    return wrapper


def loading(func):
    '''画面のロード完了を一定秒待機する（デコレータ）
    '''

    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'driver'):
            try:
                WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(EC.presence_of_all_elements_located)
            except TimeoutException:
                if hasattr(self, 'mediator'):
                    # loggerが見つかれば出力
                    self.mediator.logger.debug('page loading failed.')
        return func(self, *args, **kwargs)
    return wrapper


def backup_ajax(driver):
    '''ajax通信用のブジェクトをバックアップする
    通信を再開させるときのために保管

    WARN:
        close後にbackupを取らないよう注意
    '''
    driver.execute_script("window.oSend=XMLHttpRequest.prototype.send;")


def pause_ajax(waiting_sec=3):
    '''関数を実行する間、ajaxを一時停止する（デコレータ）
    self.driver の存在しない状況下で呼び出されたらエラー

    Args:
        waiting_sec (int): closeするまでの待機時間
    '''
    def _pause_ajax(func):
        def wrapper(self, *args, **kwargs):
            sleep(waiting_sec)
            _close_ajax(self.driver)
            res = func(self, *args, **kwargs)
            _reopen_ajax(self.driver)
            return res
        return wrapper
    return _pause_ajax


def _close_ajax(driver):
    '''ajax通信をバイパスする

    (1)
    現状、特に[フォロワー, フォロー中] 他の画面で、
    スクロール表示をまたずに要素を延々と回収し続ける不具合（としか思えない事象）が存在します
    仕方ないので、自動ロードが続きそうなところは、ajaxを意図的にバイパスして乗り切ります

    (2)
    現在分かっている仕様
        * 一度ajaxを止めると、ajaxを再開させてもキャッシュが有効な場合は通信が発生しない
        * ページのキャッシュが効かない場合は、再開されていればajaxが動く
        * close から open までの間に一度でもajax通信が発生していることが停止の条件
    '''
    # ajaxのバックアップが見つからない場合は実行不可
    try:
        driver.execute_script("return window.oSend")
    except JavascriptException as e:
        raise e

    driver.execute_script("XMLHttpRequest.prototype.send = function(){console.log('stopped ajax request', arguments)};")


def _reopen_ajax(driver):
    '''ajax通信を復旧する

    オブジェクトのbackup有無を確認していないので、事前に close_ajax() が実行されている必要がある
    '''
    # ajaxのバックアップが見つからない場合は実行不可
    try:
        driver.execute_script("return window.oSend")
    except JavascriptException as e:
        raise e

    driver.execute_script("XMLHttpRequest.prototype.send=window.oSend")
