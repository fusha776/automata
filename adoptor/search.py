from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from automata.common.utils import wait, loading
from automata.common.settings import WAIT_LOADING_SECONDS, POPULAR_POSTS_NUM_IN_SEARCH


class Search():
    '''投稿関連の動作を制御するクラス
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.doll_conf.login_id

    @loading
    @wait()
    def switch_to_search_home(self):
        '''検索トップへ遷移する
        '''
        self.driver.get(f'https://www.instagram.com/explore/')

    @loading
    @wait()
    def search_tags(self, keyword):
        '''keywordで検索して、結果へ遷移する
        実際は[検索ホーム]から始める必要はないけど、念のため正規ルートに近い画面遷移を推薦

        WARN:
            URLエンコーディングして直接飛ぶため、`#` 無しの文字列が必要です

        Args:
            keyword (str): 検索するワード. タグの場合は#付きで渡す (e.g. '#猫')

        Condition:
            [検索ホーム]
        '''
        #

        # 何回もdictを参照させて失敗してるから、チェック機構を入れよう
        if type(keyword) is not str:
            self.mediator.logger.error(f'文字列ではない検索ワードが参照されました: {keyword}')
            raise Exception

        # 念のため # 消し処理を加える
        kw_cleaned = keyword.replace('#', '')
        self.driver.get(f'https://www.instagram.com/explore/tags/{kw_cleaned}/')

    @loading
    @wait()
    def load_imgs(self):
        '''[検索結果] に表示されている画像を取得する
        一度の検索で約40件くらい取れる
        これで足りなくなったら画面スクロールの導入を検討してください
        検索対象ワードをたくさん持たせる方針の方が良いと思います

        WARN:
            上位n件は `人気投稿`, それ以降は `最新投稿` が並びます
            人気投稿をタグから弾くのがやりにくいので、上位n件を人気投稿とみなす方針でいきます

        Returns:
            str[]: 投稿詳細へのリンク

        Conditions:
            [検索結果]
        '''
        photo_frame = self.driver.find_element_by_xpath('//article')
        photos = WebDriverWait(photo_frame, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, './/a[contains(@href, "/p/")]')))
        # clickable は単数しか取得できないので、要素の確認後に取りなおす
        photos = self.driver.find_elements_by_xpath('.//a[contains(@href, "/p/")]')

        links = []
        for photo in photos[POPULAR_POSTS_NUM_IN_SEARCH:]:
            href = photo.get_attribute('href')
            links.append(href)
        return links

    @loading
    @wait()
    def fav(self):
        '''投稿をfavする

        Returns:
            bool: favに成功 -> True

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        # 写真が大きいとfavボタンとポップがぶつかってしまうので画面をずらす
        # あんまりずらすとオススメ投稿が見えるのでちょっとだけ動かす
        self.driver.execute_script('window.scrollBy(0, 100)')

        already_faved = self.driver.find_elements_by_xpath('//section/span/button/*[contains(@aria-label, "取り消す")]')
        if already_faved:
            return False

        fav_btn = self.driver.find_elements_by_xpath('//section/span/button/*[contains(@aria-label, "いいね")]')
        if not fav_btn:
            return False
        fav_btn[0].click()

        # アクションブロック確認を、アクション更新前に入れる
        self.mediator.modal.check_action_block()

        # アクション回数を更新
        self.mediator.dao.increase_action_count({'fav': 1})
        return True
