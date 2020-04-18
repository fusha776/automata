from automata.apimediator.abilities import Abilities
from automata.workflow.following import Following


class Facade():
    '''ワークフローを制御するクラス

    各画面内で完結する動作でも、
    業務フローに依存したらadaptorではなくworkflowで管理
    '''

    def __init__(self, worker_id):
        self.abilities = Abilities(worker_id)

        # 各フローの移譲先を取得
        self.following = Following(self.abilities)

    def switch_to_instagram_home(self):
        self.abilities.web.switch_to_instagram_home()
