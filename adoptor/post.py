from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from automata.common.settings import WAIT_LOADING_SECONDS
from automata.common.utils import wait, loading


class Post():
    '''投稿関連の動作を制御するクラス
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.doll_conf.login_id

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

    @loading
    @wait()
    def estimate_insta_id(self):
        '''投稿画面から投稿者のインスタIDを推定する
        htmlの変更に強くするためにもネストの深いタグを辿ることは回避したいので、浅い検索条件から推定する

        条件:
            リンクにテキストが含まれるaタグの中で出現回数最大のリンク

        Returns:
            str: インスタID

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        a_cnts = {}
        anchors = WebDriverWait(self.driver, WAIT_LOADING_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, '//a')))
        # clickable は単数しか取得できないので、要素の確認後に取りなおす
        anchors = self.driver.find_elements_by_xpath('//a')
        for a in anchors:
            link = a.get_attribute('href')
            tag_text = a.text

            # テキストがブランクならskip
            if not tag_text:
                continue

            if tag_text not in a_cnts:
                a_cnts[tag_text] = 0
            if tag_text in link:
                a_cnts[tag_text] += 1
        return max(a_cnts, key=a_cnts.get)
