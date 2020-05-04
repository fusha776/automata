##########
# Chrome #
##########

# chrome webdriver のパス
CHROMEDRIVER_PATH = 'd:/python/project/insta/driver/chromedriver.exe'

# ブラウザのキャッシュサイズ. 大きすぎるとDisk容量を食べる
CHROME_CACHE_SIZE = 52428800

###############
# DB & Params #
###############

# データレイクのルート
LAKE_ROOT_PATH = 'd:/python/project/insta/lake'

# パラメータjsonが格納されたディレクトリ
DOLL_PARAMS_DIR = 'd:/python/project/insta/doll_params'


###############
# 画面動作制御 #
###############

# 次の動作までの停止時間の目安（秒）
#
# 結構重要そうなパラメータ
# 多重ブラウザに対応したらもう少し大きくしよう
#
# 3秒だとそこそこAPI制限エラーが出る
#
ACTION_WAIT_SECONDS = 5

# 全操作に紐づける画面制御の待機時間
WAIT_SECONDS = 2

# 画面のロード完了に紐づける待機時間
WAIT_LOADING_SECONDS = 20

# これ以上フォロワー数があるユーザを法人とみなす
FOLLOWER_UPPER_LIMIT = 10000

# フォロワー or フォロー中をロードする最大数（大きいとAPI制限の引っかかりやすさが跳ね上がる）
LOADING_NEIGHBORS_LIMIT = 50

# [検索結果] で、人気投稿の表示される件数（リンク取得からskipする画像の件数）
POPULAR_POSTS_NUM_IN_SEARCH = 9

# プロフコメントに含まれていたら法人相当とみなす文字列
HOJIN_KEYWORDS = ['院', '店', '屋', '公式', '副業', '収入', 'フォロワー', '仕事', '稼', '予約', '営業']

###############
# フォロー管理 #
###############

# アンフォローせずにフォローバックを待つ日数
KEEPING_DAYS = 14

# F-back有無を問わず、フォローしてからアンフォローするまでの日数
FLLOWING_ALIVE_DAYS = 5

# 直近アクション有りユーザをキャッシュする数
CACHED_TOUCHED_USER_SIZE = 5000

NG_USER_SIZE = 1000  # 廃止予定


###########
# 起動制御 #
###########

# automataの起動停止時間帯（ブロック回避）
# from <= hour <= to 形式
HOUR_SLEEPING_FROM, HOUR_SLEEPING_TO = 16, 23

# 起動間隔を空ける時間（秒）
BOOTING_INTERVAL_SECONDS = 60 * 60 * 2

# Dollの最大並列数（Instagramのブロック回避？で念のため）
DOLLS_PARALLEL_LIMIT = 5
