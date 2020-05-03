import pymysql


class ConnectionFactory():
    '''DBとのコネクションを生成する
    Doll管理インスタンスでも使用するため、abilitiesとは独立させる
    '''
    @classmethod
    def get_conn(cls):
        conn = pymysql.connect(host='localhost',
                               user='root',
                               password='root',
                               db='automata',
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
        return conn
