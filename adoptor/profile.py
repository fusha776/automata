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
        URL直書きで飛べるけど、変なアクセスに見られないように注意が必要かも

        Args:
            insta_id (str): インスタグラムID
        '''
        self.driver.get(f'https://www.instagram.com/{insta_id}/?hl=ja')

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
    def follow(self, allow_to_follow_back=False):
        '''フォローする

        Args:
            allow_to_follow_back (bool): フォローバック可否

        Returns:
            bool: フォロー成功 -> True

        Conditions:
            [プロフィール]
        '''
        profs = self.get_user_details()
        insta_id = profs['insta_id']

        # プロフィール取得失敗
        if not insta_id:
            self.mediator.logger.debug('フォロー skip: プロフィール取得失敗')
            return False

        has_followed = False
        btn_is_found = False
        if not btn_is_found:
            el = self.pick_follow_btn()
            if el:
                el[0].click()
                btn_is_found = True
                has_followed = True

        if (not btn_is_found) and allow_to_follow_back:
            el = self.pick_followback_btn()
            if el:
                el[0].click()
                btn_is_found = True
                has_followed = True

        # アクション更新
        if has_followed:
            self.mediator.logger.debug(f'followed: {insta_id}')
            # ステータスを更新
            self.mediator.dao.add_following(insta_id, has_followed=1, is_follower=0)
            # アクション回数を更新
            self.mediator.dao.increase_action_count({'follow': 1})
        return has_followed

    @pause_ajax(waiting_sec=3)
    def get_user_parts(self):
        '''表示されているユーザに対して、ユーザIDと名前ボタン、フォローボタンを取得する
        都度ロードされていくので、完了まで待つのは現実的ではなさそう
        一度で結構大量に取れる

        Returns:
            dict: key -> {インスタID, フォローボタンのテキスト, ユーザ名のelement, フォローボタンのelement}

        Conditions:
            [プロフィール] - [フォロワー or フォロー中]
        '''
        # 要素リストの読み込みを少し待つ（読み込みはpause_ajax内でwait）

        res = []
        users = self.driver.find_elements_by_xpath('//li')
        for i in range(len(users)):
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
            鍵アカは現状、 フォロー数, フォロワー数 が取れない（タグ構成が異なる）

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
        profiles['follower'] = self.driver.find_elements_by_xpath("//a[contains(text(), 'フォロー中')]/span")
        profiles['following'] = self.driver.find_elements_by_xpath("//a[contains(text(), 'フォロワー')]/span")
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

        fbtn_base = self.driver.find_element_by_xpath('//header/section')
        if fbtn_base.find_elements_by_xpath('.//button[contains(text(), "メッセージを送信")]'):
            profiles['is_following'] = True
        if fbtn_base.find_elements_by_xpath('.//button[contains(text(), "リクエスト済み")]'):
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

        Conditions:
            [プロフィール]
        '''
        fbtn_base = self.driver.find_element_by_xpath('//header/section')
        res = fbtn_base.find_elements_by_xpath('.//button[contains(text(), "フォローする")]')
        return res[0] if res else None

    @loading
    def pick_followback_btn(self):
        '''フォローバックボタンを取得する

        Conditions:
            [プロフィール]
        '''
        fbtn_base = self.driver.find_element_by_xpath('//header/section')
        res = fbtn_base.find_elements_by_xpath('.//button[contains(text(), "フォローバックする")]')
        return res[0] if res else None

    @loading
    def get_post_links(self, max_size=10):
        '''投稿写真へのリンクを取得する

        Conditions:
            [プロフィール]
        '''
        photo_frame = self.driver.find_element_by_xpath('//article')
        photos = photo_frame.find_elements_by_xpath('.//a')

        links = []
        for photo in photos[:max_size]:
            href = photo.get_attribute('href')
            links.append(href)
        return links
