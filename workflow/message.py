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

    def load_message(self, insta_id):
        '''指定されたIDから送信されたメッセージをDBへ登録
        '''
        self.ab.logger.debug('start operation: DM返信を取得')
        self.ab.dm.switch_to_dm_home()
        self.ab.dm.register_dm(insta_id)
