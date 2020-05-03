class ActionCountersRepository():
    '''action_counters の repositoryクラス
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

    def increase_action_count(self, cnts):
        '''アクションのカウントを進める
        '''
        updated = {'doll_id': self.doll_id, 'operated_on': self.today,
                   'post': 0, 'dm': 0, 'fav': 0, 'follow': 0, 'unfollow': 0, 'others': 0, 'summary_cnt': 0}
        if type(cnts) is int:
            updated['others'] += cnts
            updated['summary_cnt'] += cnts
        elif type(cnts) is dict:
            for key in cnts.keys():
                if key in updated:
                    updated[key] += cnts[key]
                else:
                    updated['others'] += cnts[key]
                updated['summary_cnt'] += cnts[key]

        with self.conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO
                    action_counters (doll_id, operated_on, post, dm, fav,
                                     follow, unfollow, others, summary_cnt, is_blocked)
                VALUES
                    (%(doll_id)s, %(operated_on)s,
                     %(post)s, %(dm)s, %(fav)s,
                     %(follow)s, %(unfollow)s, %(others)s, %(summary_cnt)s, 0)
                ON DUPLICATE KEY UPDATE
                    post = post + %(post)s,
                    dm = dm + %(dm)s,
                    fav = fav + %(fav)s,
                    follow = follow + %(follow)s,
                    unfollow = unfollow + %(unfollow)s,
                    others = others + %(others)s,
                    summary_cnt = summary_cnt + %(summary_cnt)s
                ''', updated)
            self.conn.commit()

    def set_blocked_mark(self):
        '''アクションブロックを検知した際に、マークを付ける
        アクション件数のレコードが存在しない場合を考慮し、先に0件更新でレコードを発生させる
        '''
        self.increase_action_count(0)
        with self.conn.cursor() as cursor:
            cursor.execute('''
                UPDATE
                    action_counters
                SET
                    is_blocked = 1
                WHERE
                    doll_id = %s and
                    operated_on = %s
            ''', (self.doll_id, self.today))
            self.conn.commit()
