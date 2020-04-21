import sqlite3
from automata.common.settings import DATABASE_PATH


class Session():
    '''DB, データレイクとのインターフェースを提供 (static変数)
    '''
    conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
