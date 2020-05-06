class AccountResearchRepository():
    '''account_research の repositoryクラス
    interfaceは省略する

    Args:
        conn (pymysql.Connection): DBへのコネクション
        doll_id (str): 起動中のdoll id
        today (str): 処理実行日
    '''

    def __init__(self, conn, doll_id, today):
        self.conn = conn
        self.doll_id = doll_id
        self.today = today

    def add_valuable_user(self, doll_group, research_id, insta_id, label, follower, following, bio, website, favs):
        '''フォロー中を追加する
        '''
        recent_favs = [0]*5
        for i in range(len(favs)):
            recent_favs[i] = favs[i]

        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO account_research
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ''', (doll_group, research_id, self.doll_id, insta_id, label, follower, following, bio, website, *recent_favs))
            self.conn.commit()

    def load_checked_users(self, doll_group, research_id):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                SELECT
                    instagram_id
                FROM
                    account_research
                WHERE
                    doll_group = %s and
                    research_id = %s
            ''', (doll_group, research_id))
            res = cursor.fetchall()
        return res
