from random import random
from time import sleep

###########
# 動作制御 #
###########

# 画面制御の待機時間
WAIT_SECONDS = 30

# これ以上フォロワー数があるユーザを法人とみなす
FOLLOWER_UPPER_LIMIT = 10000


######
# DB #
######

# テーブルのルート
DATABASE_PATH = 'c:\\Users\\bell\\python\\project\\instagram\\appium\\table\\automata_db.sqlite3'

# データレイクのルート
LAKE_ROOT_PATH = 'c:\\Users\\bell\\python\\project\\instagram\\appium\\lake'


###############
# フォロー管理 #
###############

# アンフォローせずにフォローバックを待つ日数
KEEPING_DAYS = 14

# F-back有無を問わず、フォローしてからアンフォローするまでの日数
FLLOWING_ALIVE_DAYS = 5

# NGユーザをあらかじめキャッシュする数
NG_USER_SIZE = 5000
