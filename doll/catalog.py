from automata.doll.doll import Doll


class Catalog(Doll):
    '''所定のハッシュタグから人気投稿を探し、該当アカにリポスト許可を取って転載する
    '''

    def __init__(self, doll_id, conn, today):
        super().__init__(doll_id, conn, today)

    def operate(self):
        # いったんアカ探索はおいておいて、その後の動作を確認する
        # self.facade.message.send_message('gardenbell776', 'はらへり')
        self.facade.message.load_message()

    @classmethod
    def format(cls, target_day, doll_records):
        pass
