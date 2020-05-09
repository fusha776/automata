class Message():
    '''DM回りを管理
    '''

    def __init__(self, abilities):
        self.ab = abilities

    def send_message(self, insta_id, msg):
        '''指定されたIDへ指定されたメッセージを送信
        '''
        self.ab.logger.debug('start operation: DM送信')
        self.ab.dm.switch_to_dm_home()
        self.ab.dm.send_dm(insta_id, msg)

    def load_message(self, target_id=None):
        '''指定されたIDから送信されたメッセージをDBへ登録
        画面表示順に上から読み込んでいき、新規投稿が無くなった段階でストップ

        Args:
            target_id (str): 指定があった場合は、そのインスタIDだけ確認する
        '''
        self.ab.logger.debug('start operation: DM返信を取得')
        self.ab.dm.switch_to_dm_home()

        if target_id:
            insta_ids = [target_id]
        else:
            insta_ids = self.ab.dm.read_estimated_insta_ids()
        for insta_id in insta_ids:
            new_cnt = self.ab.dm.register_dm(insta_id)

            if new_cnt == 0:
                print('0件更新のためbreak')
                break
            self.ab.dm.switch_to_dm_home()
