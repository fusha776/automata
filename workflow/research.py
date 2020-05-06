from automata.common.utils import would_be_japanese
from automata.common.utils import fillna


class Research():
    '''アンフォロー追加回りを管理
    '''

    def __init__(self, abilities, account_research_repository):
        self.ab = abilities
        self.account_research_repository = account_research_repository

    def search_hashtags_popular_accounts(self, hashtag):
        '''指定されたハッシュタグの人気投稿アカを調査してレコード追加する

        Args:
            hashtag (str): 調査するハッシュタグ
        '''
        self.ab.logger.debug('start operation: 人気投稿アカをストック')
        self.ab.search.switch_to_search_home()

        pupular_accounts = []
        self.ab.logger.debug(f'次のキーワード検索 - 開始: {hashtag}')
        self.ab.search.search_tags(hashtag)

        for img_link in self.ab.search.load_popular_posts(9):
            self.ab.driver.get(img_link)
            insta_id_i = self.ab.post.estimate_insta_id()

            post_msg = self.ab.post.read_post_msg()
            if (type(post_msg) is str) and (not would_be_japanese(post_msg)):
                self.ab.logger.debug(f'投稿コメントが日本語と推定できないためskip: {insta_id_i}')
                continue
            pupular_accounts.append(insta_id_i)
        self.ab.logger.debug(f'回収したアカウント: {pupular_accounts}')
        return pupular_accounts

    def register_valid_instagrammers(self, insta_ids, research_id):
        '''緩い条件（インスタグラマー・法人として許容）を満たすアカを登録していく

        WARN:
            最後に目検が入る想定で、緩く絞る

        Args:
            insta_ids (str[]): 調査対象のインスタID
            research_id (str): 調査
'''
        checked = self.account_research_repository.load_checked_users(self.ab.doll_conf.doll_group, research_id)
        checked = {i['instagram_id'] for i in checked}

        for insta_id in (set(insta_ids) - checked):
            self.ab.profile.switch_to_user_profile(insta_id)
            is_valid, reason_msg = self.check_hojin()
            if not is_valid:
                self.ab.logger.debug(f'{insta_id} をskip: {reason_msg}')
                continue

            # 直近3投稿のfav数を取得
            img_links = self.ab.profile.get_post_links(3)
            following_cnt = self.ab.profile.pick_following_num()
            follower_cnt = self.ab.profile.pick_follower_num()
            label = self.ab.profile.pick_account_label()
            bio_msg = self.ab.profile.pick_bio_message()
            website_btn = self.ab.profile.pick_website_btn()
            website = ''
            if website_btn:
                website = website_btn.get_attribute('href')

            # 要素取得を再チェック
            if not (following_cnt and label and bio_msg):
                continue

            favs = []
            for link_i in img_links:
                self.ab.driver.get(link_i)
                fav_i = fillna(self.ab.post.read_fav_cnt())
                favs.append(fav_i)

            self.account_research_repository.add_valuable_user(
                self.ab.doll_conf.doll_group, research_id, insta_id, label, follower_cnt, following_cnt, bio_msg, website, favs)
            self.ab.logger.debug(f'調査対象アカウントを追加: {insta_id}')

    def check_hojin(self):
        follower_cnt = self.ab.profile.pick_follower_num()
        bio_msg = self.ab.profile.pick_bio_message()

        is_valid = True
        reason_msg = "it seems good."
        # 要素取得に失敗したらFalseで返却 (bool形式を除く)
        if not (follower_cnt):
            return False, "個人判定不可: フォロワー数の取得に失敗"

        elif not (bio_msg):
            # 疑わしきは回避する方針
            return False, "個人判定不可: bioの取得に失敗 or bio登録無し"

        # 所定値よりフォロワー数が少ない
        elif follower_cnt < 1000:
            is_valid = False
            reason_msg = "フォロワー数が規定値以下"

        return is_valid, reason_msg
