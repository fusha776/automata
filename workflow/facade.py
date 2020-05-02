from time import sleep
from automata.adoptor.abilities import Abilities
from automata.workflow.following import Following
from automata.workflow.unfollowing import Unfollowing


class Facade():
    '''ワークフローを制御するクラス

    各画面内で完結する動作でも、
    業務フローに依存したらadaptorではなくworkflowで管理
    '''

    def __init__(self, doll_id):
        # インスタンス生成でdollの起動処理が走る
        self.abilities = Abilities(doll_id)
        self.abilities.setup_doll()

        # 各フローの移譲先を取得
        self.following = Following(self.abilities)
        self.unfollowing = Unfollowing(self.abilities)

    def switch_to_instagram_home(self):
        self.abilities.web.switch_to_instagram_home()
