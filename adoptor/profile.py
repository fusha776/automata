from time import sleep
from automata.common.utils import wait, loading
from automata.common.utils import pause_ajax


class Profile():
    '''[プロフィール] の動作を制御するクラス
    '''

    def __init__(self, mediator):
        self.mediator = mediator
        self.driver = self.mediator.driver
        self.login_id = self.mediator.worker_conf.login_id

    @loading
    @wait
    def switch_to_user_profile(self, insta_id):
        '''指定されたインスタグラムID の[プロフィール]へ遷移する
        アカ削除済等で遷移できないケースがある

        WARN:
            URL直書きで飛べるけど、変なアクセスに見られないように注意が必要かも

        Args:
            insta_id (str): インスタグラムID
        '''
        self.driver.get(f'https://www.instagram.com/{insta_id}/?hl=ja')
        # if self.driver.find_elements_by_xpath('//*[contains(text(), "このページはご利用いただけません")]'):
        #     return False
        # return True

    @loading
    @wait
    def switch_to_following(self, insta_id):
        '''[フォロー中] へ移動する
        URL直打ちは弾かれる

        Conditions:
            [プロフィール]
        '''
        following_btn = self.driver.find_element_by_xpath(f'//a[@href="/{insta_id}/following/"]')
        following_btn.click()

    @loading
    @wait
    def switch_to_followers(self, insta_id):
        '''[フォロワー] へ移動する
        URL直打ちは弾かれる

        Conditions:
            [プロフィール]
        '''
        following_btn = self.driver.find_element_by_xpath(f'//a[@href="/{insta_id}/followers/"]')
        following_btn.click()

    @loading
    @wait
    def follow(self, insta_id, insert_into_table=True):
        '''フォローする

        Args:
            insta_id (str): プロフィールから取るより早くて安全
            insert_into_table (bool): following_status テーブルへレコード追加する

        Returns:
            bool: フォロー成功 -> True

        Conditions:
            [プロフィール]
        '''
        has_followed = False
        el = self.pick_follow_btn()
        if el:
            el.click()
            has_followed = True

        # アクション更新
        if has_followed:
            # ステータスを更新
            if insert_into_table:
                self.mediator.dao.add_following(insta_id, has_followed=1, is_follower=0)
            # アクション回数を更新
            self.mediator.dao.increase_action_count({'follow': 1})
        return has_followed

    @loading
    @wait
    def follow_back(self, insta_id, insert_into_table=True):
        '''フォローバックする

        Args:
            insta_id (str): プロフィールから取るより早くて安全
            insert_into_table (bool): following_status テーブルへレコード追加する

        Returns:
            bool: フォローバック成功 -> True

        Conditions:
            [プロフィール]
        '''
        has_followed = False
        el = self.pick_followback_btn()
        if el:
            el.click()
            has_followed = True

        # アクション更新
        if has_followed:
            # ステータスを更新
            if insert_into_table:
                self.mediator.dao.add_following(insta_id, has_followed=1, is_follower=0)
            # アクション回数を更新
            self.mediator.dao.increase_action_count({'follow': 1})
        return has_followed

    @loading
    @wait
    def unfollow(self, insta_id, stop_private=False):
        '''指定されたインスタIDをアンフォローする


        WARN:
            鍵アカの場合はちょっと考えてない... automataは現状鍵アカをスルーする方針

        Args:
            insta_id (str): 画面からもインスタID取れるけど、もらった方が早い
            stop_private (bool): 鍵アカのアンフォロー止める -> True

        Returns:
            bool: アンフォローに成功 -> True
        '''
        unfollow_btn = self.pick_unfollow_btn()
        if unfollow_btn:
            # フォローボタンが見つかった場合はアンフォロー
            unfollow_btn.click()
            if stop_private:
                if self.mediator.modal.check_unfollow_dialog_if_private():
                    self.mediator.logger.debug(f'鍵アカのためアンフォローを中止: {insta_id}')
                    return False
            self.mediator.modal.press_unfollow_at_profile_home()
            self.mediator.logger.debug(f'アクション unfollow: {insta_id}')
        elif self.pick_follow_btn():
            # フォローボタンが見つかった場合： 相手先から解除された
            self.mediator.logger.debug(f'アクション unfollow: 相手から解除された. フォロー中リストから削除: {insta_id}')
        elif self.pick_followback_btn():
            # フォローバックボタンが見つかった場合： 相手先から解除された？
            self.mediator.logger.debug(f'アクション unfollow: 削除された？（フォローバックボタンを確認）. フォロー中リストから削除: {insta_id}')
        else:
            # その他： 理由不明。画面呼び出しの失敗 or リクエスト中？
            self.mediator.logger.debug(f'アクション unfollow: 要素の取得失敗 or リクエスト中 のためskip: {insta_id}')
            return False

        self.mediator.dao.delete_following(insta_id)
        self.mediator.dao.increase_action_count({'unfollow': 1})
        return True

    def read_neighbor_datasets(self, waiting_sec=5):
        '''一定時間待機でデータロードしてから、ユーザ名とフォロー状況のdictを返却する

        Args:
            waiting_sec (int): ajax停止前に待機する秒数
        '''
        sleep(waiting_sec)
        return self._read_neighbor_datasets()

    def read_neighbor_datasets_on_order(self, min_rec_size, retry_cnt=5):
        '''ユーザリストが指定サイズを超えるまで待機してから、ユーザ名とフォロー状況のdictを返却する

        WARN:
            一定回数繰り返しても取得できるユーザ数が変わらなければそこで中断

        Args:
            min_rec_size (int): 最低限ほしいユーザリストの件数
            retry_cnt (int): ユーザ数が変わらなくても画面ロードを待つリトライ回数
        '''
        cnt_size_is_same = 0
        rec_size, pre_rec_size = 0, 0
        while (rec_size < min_rec_size) and (cnt_size_is_same <= retry_cnt):
            sleep(1)
            users = self.driver.find_elements_by_xpath('//li')
            if users:
                rec_size = len(users)
            if rec_size == pre_rec_size:
                cnt_size_is_same += 1
            else:
                pre_rec_size = rec_size
                cnt_size_is_same = 0
            self.mediator.logger.debug(f'ユーザリスト now loading: ロード件数 -> {rec_size}')
        return self._read_neighbor_datasets()

    @pause_ajax(waiting_sec=0)
    def _read_neighbor_datasets(self):
        '''表示されているユーザに対して、ユーザIDと名前ボタン、フォローボタンを取得する
        都度ロードされていくので完了まで待つのは現実的ではないし、API制限でブロックされそう

        WARN:
            画面やユーザデータのロード待ちは関数外実行の前提で動きます

        Returns:
            dict: key -> {インスタID, フォローボタンのテキスト, ユーザ名のelement, フォローボタンのelement}

        Conditions:
            [プロフィール] - [フォロワー or フォロー中]
        '''
        # 要素リストを取得
        users = self.driver.find_elements_by_xpath('//li')
        if users is None:
            users = []
        user_cnt = len(users)
        self.mediator.logger.debug(f'ユーザリストの取得: 件数 -> {user_cnt}')

        res = []
        for i in range(user_cnt):
            user = self.driver.find_elements_by_xpath('//li')[i]
            el_fbtns = user.find_elements_by_xpath('.//button')

            # ストーリー有無によって、aタグの数が異なる
            id_btn = None
            for el in user.find_elements_by_xpath('.//a'):
                insta_id = el.get_attribute('title')
                if insta_id:
                    id_btn = el
                    break

            if not (id_btn and el_fbtns):
                continue

            res.append({'insta_id': insta_id,
                        'follow_msg': el_fbtns[0].text,
                        'id_btn': id_btn,
                        'follow_btn': el_fbtns[0]})
        return res if res else None

    @loading
    def get_user_details(self):
        '''ユーザの基本情報を取得する
        ブロック他へファジーに対応するため、ボタンが見つからない場合を考慮

        WARN:
            鍵アカは現状、 フォロー中数, フォロワー数 が取れない（タグ構成が異なる）

        Return:
            dict[str or int or bool]: key -> [username, name, posts, follower, following, website, bio, is_following]

        Condition:
            [プロフィール]
        '''
        def to_num(s):
            '''投稿, フォロワー, フォロー中などを数値へ変換する
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

        profiles = {}
        profiles['insta_id'] = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/header/section/div[1]/h2')
        profiles['name'] = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/h1')
        profiles['posts'] = self.driver.find_elements_by_xpath("//span[contains(text(), '投稿')]/span")
        profiles['follower'] = self.driver.find_elements_by_xpath("//a[contains(text(), 'フォロワー')]/span")
        profiles['following'] = self.driver.find_elements_by_xpath("//a[contains(text(), 'フォロー中')]/span")
        profiles['website'] = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/a')
        profiles['bio'] = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/div[1]/span')

        # webElement が格納されているので、値を取り出す
        for col in profiles:
            if profiles[col]:
                profiles[col] = profiles[col][0].text
            else:
                profiles[col] = None

        # 一部を数値へ変換
        profiles['posts'] = to_num(profiles['posts'])
        profiles['follower'] = to_num(profiles['follower'])
        profiles['following'] = to_num(profiles['following'])

        # フォロー状況フラグを取得
        profiles['is_following'] = False
        profiles['is_only_followed'] = False
        profiles['is_not_touched'] = False
        profiles['has_requested'] = False

        fbtn_base = self.driver.find_elements_by_xpath('//header/section')
        if fbtn_base:
            if fbtn_base[0].find_elements_by_xpath('.//button[contains(text(), "メッセージを送信")]'):
                profiles['is_following'] = True
            if fbtn_base[0].find_elements_by_xpath('.//button[contains(text(), "リクエスト済み")]'):
                profiles['has_requested'] = True
            if self.pick_follow_btn():
                profiles['is_not_touched'] = True
            if self.pick_followback_btn():
                profiles['is_only_followed'] = True

        # プライペートフラグを取得
        profiles['is_private'] = self.check_private()

        return profiles

    @loading
    def check_private(self):
        '''鍵アカかどうか調べる
        ブラウザ版は英語表記にならなそう

        Returns:
            bool: 鍵アカ -> True

        Conditions:
            [プロフィール]
        '''
        msg_jp = self.driver.find_elements_by_xpath('//*[contains(text(), "このアカウントは非公開")]')
        return bool(msg_jp)

    @loading
    def pick_follow_btn(self):
        '''フォローボタンを取得する

        Return:
            element: フォローボタンのelement

        Conditions:
            [プロフィール]
        '''
        res = None
        fbtn_base = self.driver.find_elements_by_xpath('//header/section')
        if fbtn_base:
            res = fbtn_base[0].find_elements_by_xpath('.//button[contains(text(), "フォローする")]')
        return res[0] if res else None

    @loading
    def pick_followback_btn(self):
        '''フォローバックボタンを取得する

        Return:
            element: フォローバックボタンのelement

        Conditions:
            [プロフィール]
        '''
        res = None
        fbtn_base = self.driver.find_elements_by_xpath('//header/section')
        if fbtn_base:
            res = fbtn_base[0].find_elements_by_xpath('.//button[contains(text(), "フォローバックする")]')
        return res[0] if res else None

    @loading
    def pick_unfollow_btn(self):
        '''アンフォローボタンを取得する

        Return:
            element: アンフォローボタンのelement

        Conditions:
            [プロフィール]        
        '''
        res = None
        fbtn_base = self.driver.find_elements_by_xpath('//header/section')
        if fbtn_base:
            res = fbtn_base[0].find_elements_by_xpath('.//span[contains(@aria-label, "フォロー中")]')
        return res[0] if res else None

    @loading
    def get_post_links(self, max_size=10):
        '''投稿写真へのリンクを取得する

        Conditions:
            [プロフィール]
        '''
        photo_frame = self.driver.find_element_by_xpath('//article')
        photos = photo_frame.find_elements_by_xpath('.//a[contains(@href, "/p/")]')  # /p/ を付けないとオススメ垢のリンクがヒットする

        links = []
        for photo in photos[:max_size]:
            href = photo.get_attribute('href')
            links.append(href)
        return links
