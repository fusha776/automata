import random
import re
import os
import pathlib
from logging import getLogger, StreamHandler, FileHandler, Formatter, DEBUG
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automata.common.settings import ACTION_WAIT_SECONDS, WAIT_LOADING_SECONDS
from automata.common.settings import CHROMEDRIVER_PATH, CHROME_CACHE_SIZE, WAIT_SECONDS
from automata.common.settings import LOGGING_DIR


def wait(waiting_seconds=ACTION_WAIT_SECONDS):
    def _wait(func):
        '''画面遷移前に一定秒停止させる（デコレータ）
        '''
        def wrapper(*args, **kwargs):
            # ランダムに停止させる
            sleep(waiting_seconds * (1 + 0.5 * random.random()))
            return func(*args, **kwargs)
            sleep(waiting_seconds * (1 + 0.5 * random.random()))
        return wrapper
    return _wait


def loading(func):
    '''画面のロード完了を一定秒待機する（デコレータ）
    非同期処理で画面生成されるから、ロードとページ生成の完了が一致しない点がやりにくい
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


def would_be_japanese(msg, omit_hashtags=True):
    '''文字列が日本語で書かれているか推定する

    判定基準：
        ハッシュタグを除去した後の文字列に、ひらがな or カタカナ を1文字以上含む
        何文字以上にするかは悩みどころ

    Args:
        msg (str): 判定対象の文字列
        omit_hashtags (bool): True -> ハッシュタグ相当 (# が出現した以降の文字列) を除去する
    '''
    if omit_hashtags:
        msg_cleaned = msg.split('#')[0]
    else:
        msg_cleaned = msg

    hit_words = re.findall(r'[ぁ-んァ-ン]', msg_cleaned)
    return len(hit_words) >= 1


@loading
@wait()
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
            close_ajax(self.driver)
            res = func(self, *args, **kwargs)
            reopen_ajax(self.driver)
            return res
        return wrapper
    return _pause_ajax


def close_ajax(driver):
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


def reopen_ajax(driver):
    '''ajax通信を復旧する

    オブジェクトのbackup有無を確認していないので、事前に backup_ajax() が実行されている必要がある
    '''
    # ajaxのバックアップが見つからない場合は実行不可
    try:
        driver.execute_script("return window.oSend")
    except JavascriptException as e:
        raise e

    driver.execute_script("XMLHttpRequest.prototype.send=window.oSend")


def create_logger(doll_id, today):
    '''所定フォーマットのロガーと出力先を生成
    '''
    def create_dir_and_log():
        '''必要なディレクトリ, 当日のログファイルが無ければ生成

        Returns:
            str: 当日のログファイルのpath
        '''
        log_dir = f'{LOGGING_DIR}/{doll_id}'
        ss_dir = f'{LOGGING_DIR}/{doll_id}/screenshots'
        pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(ss_dir).mkdir(parents=True, exist_ok=True)
        log_path = f'{log_dir}/replay_{today}.log'
        if not os.path.exists(log_path):
            pathlib.Path(log_path).touch()
        return log_path

    log_path = create_dir_and_log()
    fmt = "%(asctime)s %(levelname)s [%(name)s] :%(message)s"
    handler = StreamHandler()
    handler.setFormatter(Formatter(fmt))
    handler.setLevel(DEBUG)
    file_handler = FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(Formatter(fmt))
    file_handler.setLevel(DEBUG)

    logger = getLogger(doll_id)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def create_driver(browser_data_dir, device_name):
    '''Chromeを起動し、Driverインスタンスを返却する

    Args:
        browser_data_dir (str): 使用する Chrome Profile のパス
        device_name (str): 使用するデバイス名。 e.g. 'Pixel 2'
    '''
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={browser_data_dir}')  # 同一のデータディレクトリは複数ブラウザで参照できない点に注意
    options.add_argument(f'--disk-cache-size={CHROME_CACHE_SIZE}')
    if device_name:
        options.add_experimental_option('mobileEmulation', {'deviceName': device_name})
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
    driver.implicitly_wait(WAIT_SECONDS)  # find_element等の最大待ち時間

    # 途中でajaxをバイパス制御するため、xhrのバックアップ実行（ブラウザ側で保管）
    backup_ajax(driver)
    return driver


def fillna(val):
    return val if val is not None else 0


def to_num(s):
    '''投稿, フォロワー, フォロー中, favなどを数値へ変換する
    '''
    if not s:
        return None
    s = s.replace(',', '')

    if ('NaN' in s):
        s = 0
    elif '万' in s:
        s = s.replace('万', '')
        s = float(s) * 10000
    return int(s)


def swipe_random(driver, max_swipe=4):
    '''画面をランダムにスワイプする
    bot対策で画面スワイプを収集しているらしい
    '''
    # マウスを画面中央へ移動
    main_el = driver.find_element_by_tag_name('main')
    chains = ActionChains(driver)
    chains.move_to_element(main_el).perform()
    for i in range(max_swipe):
        print(f"for in {i}")
        # スワイプの方向を上下どちらにするか決める
        direction = 1
        if random.random() < 0.3:
            direction = -1
        st_x, st_y = random.randint(-100, 100), random.randint(min(150 * direction, 250 * direction),
                                                               max(150 * direction, 250 * direction))
        en_x, en_y = random.randint(-100, 100), random.randint(min(-1 * 150 * direction, -1 * 250 * direction),
                                                               max(-1 * 150 * direction, -1 * 250 * direction))
        chains = ActionChains(driver)
        chains \
            .move_to_element(main_el) \
            .move_by_offset(st_x, st_y) \
            .click_and_hold() \
            .move_by_offset(- 1 * st_x + en_x, -1 * st_y + en_y) \
            .release() \
            .perform()
        sleep(random.random())
        if random.random() < 0.3:
            break
