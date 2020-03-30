import os
from datetime import datetime, timedelta
from glob import glob
from random import random
from time import sleep
import chardet
from automata.instagram.instagram import InstagramPixel
from automata.common.settings import KEEPING_DAYS, FLLOWING_ALIVE_DAYS
from automata.common.settings import wait


class WorkFlow():
    '''instagram インスタンスを生成し、
    業務フローに沿って稼働させる

    TODO:
        Workerクラスを作って、workerの設定を定義する
        仮想端末を自動で起動する機能を実装させる
        今は一台しか稼働させず、立ち上げっぱなしの前提なので後ろ倒し可能
    '''

    def __init__(self, worker_id, post_timetable='any'):
        # これはたぶん起動時の引数になる
        self.worker_id = worker_id
        self.post_timetable = post_timetable
        self.pixel = InstagramPixel(worker_id)
        print('worker is loaded.')

    def switch_to_instagram_home(self):
        '''インスタグラムのhomeへ移動する
        '''
        self.pixel.switch_to_instagram_home()

    def post_routine(self):
        '''指定時間にデータレイクを参照して投稿する
        '''

        def fetch_post_content(self):
            '''投稿時間設定から、投稿画像とコメントを取得
            '''
            # 指定時間 > any の順で、投稿ファイルセットを探す
            contents_paths = glob(f'{self.pixel.worker_group_lake_path}\\stock\\{self.post_timetable}\\*')
            if not contents_paths:
                contents_paths = glob(f'{self.pixel.worker_group_lake_path}\\stock\\any\\*')

            # 画像とコメントがセットになっている、作成日の一番古いファイルセットを返却
            fileset, img_files, txt_files = None, None, None
            time_creation = float('inf')
            for cpath in contents_paths:
                img_files = [p for p in glob(f'{cpath}\\*') if p.split('.')[-1] in ['jpg', 'jpeg', 'png']]
                txt_files = glob(f'{cpath}\\*.txt')

                if not (img_files and txt_files):
                    continue

                if os.path.getctime(cpath) < time_creation:
                    fileset = {'cpath': cpath, 'img_path': img_files[0], 'txt_path': txt_files[0]}
                    time_creation = os.path.getctime(cpath)

            if not (fileset):
                raise Exception('投稿できるファイルセットがありませんでした')
            return fileset['cpath'], fileset['img_path'], fileset['txt_path']

        def get_message(fpath):
            '''エンコードを簡易判別し、pathを開いてテキストを読み込む
            '''
            with open(fpath, 'rb') as fb:
                b_txt = fb.read()
            enc = chardet.detect(b_txt)['encoding']
            if enc != 'utf-8':
                enc = 'sjis'

            with open(fpath, 'r', encoding=enc) as f:
                msg = f.read()
            if msg:
                return msg
            raise Exception('投稿ファイルセットの中にあるコメントの中身がブランクです')

        # main
        cpath, img_path, txt_path = fetch_post_content(self)
        msg = get_message(txt_path)
        self.pixel.save_photo(img_path)
        self.pixel.post_photo(msg)
        # DB更新
        self.pixel.dao.increase_action_count({'post': 1})
        self.pixel.dao.store_used_contents(cpath)

    def push_fav_according_to_hashtags(self, hashtag, fav_x_times=5, skip_rate=0.40):
        '''ハッシュタグで検索をかけて、見つけた投稿をランダムにファボする

        Args:
            hashtag (str): タグ検索をかけるキーワード
            skip_rate (int): 画像をスキップする確率。全てクリックせずに肉入りらしさを出す。
        '''
        fav_cnt = 0
        img_each = self.pixel.search(hashtag)
        for img in img_each:
            if fav_cnt >= fav_x_times:
                break
            if random() < skip_rate:
                continue

            img.click()
            sleep(2 + 3 * random())
            self.pixel._push_fav()
            sleep(3 + 5 * random())
            self.pixel.push_app_back_btn()
            fav_cnt += 1
        # DB更新
        self.pixel.dao.increase_action_count({'fav': fav_cnt})

    def follow_users_according_to_hashtags(self, hashtag, follow_x_times=5, skip_rate=0.90):
        '''ハッシュタグで検索をかけて、見つけたユーザをランダムにフォローする

        Args:
            hashtag (str): タグ検索をかけるキーワード
            skip_rate (int): 画像をスキップする確率。全てクリックせずに肉入りらしさを出す。
        '''
        following_cnt = 0
        img_each = self.pixel.search(hashtag)
        for img in img_each:
            if following_cnt >= follow_x_times:
                break
            if random() < skip_rate:
                continue

            img.click()
            sleep(2 + 3 * random())
            self.pixel._go_to_profile()
            sleep(4 + 3 * random())
            has_successed = self.pixel._follow()
            profiles = self.pixel._fetch_profile()
            sleep(3 + 5 * random())
            self.pixel.push_app_back_btn()
            sleep(1 + 1 * random())
            self.pixel.push_app_back_btn()
            if has_successed:
                following_cnt += 1
                self.pixel.dao.add_following(profiles['username'])

        # アクション回数を更新
        self.pixel.dao.increase_action_count({'follow': following_cnt})

    def follow_back_in_just_following(self, n_users=10, slide_n_times=20):
        '''フォローバックする

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        アクティビティの履歴から見るため、精度は荒い
        アクティビティ経由のフォロワー表示は、フォロー日降順で並んでいて便利
        '''
        followings = self.pixel._fetch_activities()['followings']
        if not followings:
            return

        followings[0].click()  # 複数見つかっても、1つ巡回すれば事足りる
        following_cnt, additional_ng = self.pixel._follow_users_in_just_following(n_users, slide_n_times)
        self.pixel.push_app_back_btn()
        # アクション回数を更新
        self.pixel.dao.increase_action_count({'follow': following_cnt})
        # NGユーザを追加
        self.pixel.dao.add_ng_users({'follow': following_cnt})

    def follow_in_just_favs(self, n_users=10, slide_n_times=20):
        '''ファボした人をフォローする

        Args:
            n_users (int): フォローする人数
            slide_n_times (int): 下へスライドさせる最大回数

        アクティビティの履歴から見るため、精度は荒い
        '''
        favs = self.pixel.fetch_activities()['favs']
        if not favs:
            return

        favs[0].click()  # 複数見つかっても、1つ巡回すれば事足りる
        following_cnt = self.pixel._follow_users_in_just_fav(n_users, slide_n_times)
        self.pixel.push_app_back_btn()
        # アクション回数を更新
        self.pixel.dao.increase_action_count({'follow': following_cnt})

    def fav_back_in_just_favs(self):
        '''ファボした人へファボ返しする (未実装)

        Args:
            n_users (int): ファボ返しする人数
            slide_n_times (int): 下へスライドさせる最大回数

        アクティビティの履歴から見るため、精度は荒い
        '''
        favs = self.pixel.fetch_activities()['favs']
        if not favs:
            return
        favs[0].click()  # 複数見つかっても、1つ巡回すれば事足りる

    def dmを送るやつ(self):
        pass

    def check_following_and_unfollow(self):
        '''フォロー開始から一定期間経過してフォローバックがなければ、アンフォローする
        '''
        # フォロー状況をチェックする
        following_only = self.pixel.dao.fetch_following_only()
        status = self.pixel.check_follow_back_status(following_only.keys())

        alive_from = datetime.now() - timedelta(days=KEEPING_DAYS)
        unfollow_cnt = 0
        for id_i in following_only:
            # フォローバックを確認
            if status[id_i]:
                self.pixel.dao.update_following(id_i, has_followed=1, is_follower=1)
                continue

            # フォローバック無しで一定期間以上経過
            if following_only[id_i] < alive_from:
                self.pixel.unfollow_by_id(id_i)
                self.pixel.dao.update_following(id_i, has_followed=0, is_follower=0)
                unfollow_cnt += 1

        # アクション回数を更新
        self.pixel.dao.increase_action_count({'unfollow': unfollow_cnt})

    def unfollow_expires_users(self, actions):
        '''フォローしてから一定期間を超えたユーザをアンフォローする

        Args:
            actions (int): 実行する action の回数
        '''

        def fetch_users_to_unfollow(self):
            users_and_days = self.pixel.dao.fetch_valid_followings()
            expires_date = datetime.now() - timedelta(days=FLLOWING_ALIVE_DAYS)

            users_to_unfollow = []
            for user in users_and_days:
                if user['updated_at'] < expires_date:
                    users_to_unfollow.append(user['instagram_id'])
            return users_to_unfollow

        users_to_unfollow = fetch_users_to_unfollow(self)
        unfollow_cnt = 0
        unfollowed_ids = []
        for id_i in users_to_unfollow:
            if unfollow_cnt >= actions:
                break
            is_successful = self.pixel.unfollow_by_id(id_i)
            if is_successful:
                unfollowed_ids.append(id_i)
                unfollow_cnt += 1

        # アクション回数を更新
        for id_i in unfollowed_ids:
            self.pixel.dao.save_unfollow(id_i)
        self.pixel.dao.increase_action_count({'unfollow': unfollow_cnt})

    def follow_followers_friends(self, actions):
        '''自分のフォロワーがフォロー中のユーザをフォローする（ややこしい）

        Args:
            actions (int): 実行する action の回数
        '''
        self.pixel.back_to_profile_home()
        self.pixel._switch_to_followers()

        cnt = 0
        for my_follower in self.pixel._each_recent_follower_ids():
            print(f'each in. my follower:{my_follower.text}')
            if cnt >= actions:
                print(f'break in cnt:{cnt} > actions:{actions}')
                break
            my_follower.click()
            wait()

            # 非公開ユーザなら飛ばす
            if self.pixel._check_private():
                self.pixel.push_app_back_btn()  # 自分のフォロワー画面へ移動
                continue

            self.pixel._switch_to_following()
            wait()
            new_users, is_successful = self.pixel._follow_in_following(actions - cnt)
            cnt += len(new_users)
            wait()

            # 画面を元に戻す
            self.pixel.back_to_profile_home()
            self.pixel._switch_to_followers()
            # self.pixel.push_app_back_btn()  # フォロワーのプロフTOPへ移動
            # wait()
            # self.pixel.push_app_back_btn()  # 自分のフォロワー画面へ移動

        # # テーブルを更新
        # for id_i in followed_users:
        #     self.pixel.dao.add_following(id_i, has_followed=1, is_follower=0)

        # # アクション回数を更新
        # self.pixel.dao.increase_action_count({'follow': cnt})
