#################
# Chrome Driver #
#################

# chrome webdriver のパス
CHROMEDRIVER_PATH = 'c:/Users/bell/python/project/insta/driver/chromedriver.exe'


######
# DB #
######

# テーブルのルート
DATABASE_PATH = 'c:/Users/bell/python/project/insta/storage/tables/automata_db.sqlite3'

# データレイクのルート
LAKE_ROOT_PATH = 'c:/Users/bell/python/project/instagram/appium/lake'


###########
# 動作制御 #
###########

# 次の動作までの停止時間の目安（秒）
ACTION_WAIT_SECONDS = 3

# 全操作に紐づける画面制御の待機時間
WAIT_SECONDS = 2

# 画面のロード完了に紐づける待機時間
WAIT_LOADING_SECONDS = 20

# これ以上フォロワー数があるユーザを法人とみなす
FOLLOWER_UPPER_LIMIT = 10000


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
