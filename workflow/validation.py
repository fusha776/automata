class Validation():
    '''アカウントのステータスチェック等を管理
    '''

    def __init__(self, abilities):
        self.ab = abilities

    def check_reaching_my_following_limit(self):
        '''自アカのフォロー数が最大数に近づいているか確認する

        * Instagramでは、1アカでフォロー可能なアカウント数は最大7,500に制限されている

        Returns:
            bool: フォロー可能残150件 (2%) を切った -> True
        '''
        self.ab.profile.switch_to_user_profile(self.ab.login_id)
        following_cnt = self.ab.profile.pick_following_num()
        if following_cnt >= 7500 * 0.98:
            self.ab.logger.warning(f'自アカのフォロー数が最大値に接近しています. 現在のフォロー数: {following_cnt}/7500')
            return True
        return False
