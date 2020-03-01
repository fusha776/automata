import os
from datetime import datetime
import shutil
from pathlib import Path
from glob import glob
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

        def store_used_contents(self, content_path):
            '''使用済の投稿ファイルをbackupディレクトリへ送る
            実行した worker_id を判別用に持たせる
            '''
            now = datetime.now()
            timestamp = now.strftime('%Y%m%d%H%M%S')
            ym = now.strftime('%Y%m')
            dst_path = f'{self.pixel.worker_group_lake_path}\\posted\\{ym}\\{timestamp}'
            shutil.move(content_path, dst_path)
            Path(f'{dst_path}\\{self.pixel.worker_id}').touch()

        # main
        cpath, img_path, txt_path = fetch_post_content(self)
        msg = get_message(txt_path)
        self.pixel.save_photo(img_path)
        self.pixel.post_photo(msg)
        self.pixel.dao.increase_action_count({'post': 1})
        store_used_contents(self, cpath)

        def follow_users_according_to_hashtags(self):
            '''ハッシュタグで検索をかけて、見つけたユーザをランダムにフォローする
            '''
