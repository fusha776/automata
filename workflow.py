import os
from glob import glob
from random import random
from time import sleep
import chardet
from automata.instagram import InstagramPixel


class WorkFlow():
    '''instagram インスタンスを生成し、
    業務フローに沿って稼働させる

    TODO:
        Workerクラスを作って、workerの設定を定義する
        仮想端末を自動で起動する機能を実装させる
        今は一台しか稼働させず、立ち上げっぱなしの前提なので後ろ倒し可能
    '''

    def __init__(self):
        # これはたぶん起動時の引数になる
        worker_id = 'arc_corp_1'
        self.post_timetable = 'any'

        self.pixel = InstagramPixel(worker_id)
        print('is launched.')

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
            self.pixel.push_fav()
            sleep(3 + 5 * random())
            self.pixel.push_app_back_btn()
            fav_cnt += 1
        # DB更新
        self.pixel.dao.increase_action_count({'fav': fav_cnt})

    def follow_users_according_to_hashtags(self, hashtag, follow_x_times=5, skip_rate=0.90):
        '''ハッシュタグで検索をかけて、見つけたユーザをランダムにフォローする
        フォロー状況テーブルも更新する

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
            self.pixel.go_to_profile()
            sleep(4 + 3 * random())
            has_successed = self.pixel.follow()
            profiles = self.pixel.fetch_profile()
            sleep(3 + 5 * random())
            self.pixel.push_app_back_btn()
            sleep(1 + 1 * random())
            self.pixel.push_app_back_btn()
            if has_successed:
                following_cnt += 1
                self.pixel.dao.add_following(profiles['username'])

        # アクション回数を更新
        self.pixel.dao.increase_action_count({'follow': following_cnt})

    def follow_back_from_activities(self):
        '''フォローバックする

        アクティビティの履歴から見るため、精度は荒い
        '''

    def ファボ返し(self):
        pass

    def dmを送るやつ(self):
        pass
