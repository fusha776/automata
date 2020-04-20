from automata.common.utils import wait, loading


class Post():
    '''投稿関連の動作を制御するクラス
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.worker_conf.login_id

    @loading
    @wait
    def fav(self):
        '''投稿をfavする

        Returns:
            bool: favに成功 -> True

        Conditions:
            [投稿写真 or 投稿動画]
        '''
        already_faved = self.driver.find_elements_by_xpath('//section/span/button/*[contains(@aria-label, "取り消す")]')
        if already_faved:
            return False

        fav_btn = self.driver.find_elements_by_xpath('//section/span/button/*[contains(@aria-label, "いいね")]')
        if fav_btn:
            fav_btn[0].click()
            # アクション回数を更新
            self.mediator.dao.increase_action_count({'fav': 1})
            return True
        return False
