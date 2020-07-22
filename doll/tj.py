from automata.doll.doll import Doll


class TJ(Doll):
    '''所定のハッシュタグから人気投稿を探し、該当アカの詳細を回収する

    WARN:
        動画投稿のfav数はスマホから参照できない点に注意
    '''

    def __init__(self, doll_id, conn, today):
        super().__init__(doll_id, conn, today)

    def operate(self):
        for hashtag in self.params['search_keywords']:
            insta_ids = self.facade.research.search_hashtags_popular_accounts(hashtag)
            self.facade.research.register_valid_instagrammers(insta_ids, 'kinniku_diet')
        self.facade.research.register_valid_instagrammers(insta_ids, 'kinniku_diet')

    @classmethod
    def format(cls, target_day, doll_records):
        pass
