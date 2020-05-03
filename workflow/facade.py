from automata.adoptor.abilities import Abilities
from automata.workflow.following import Following
from automata.workflow.unfollowing import Unfollowing

from automata.repository.following_status import FollowiingStatusRepository
from automata.repository.recent_touched_histories import RecentTouchedHistoriesRepository


class Facade():
    '''ワークフローを制御するクラス

    各画面内で完結する動作でも、
    業務フローに依存したらadaptorではなくworkflowで管理
    '''

    def __init__(self, doll_id, conn, today):
        # インスタンス生成でdollの起動処理が走る
        self.abilities = Abilities(doll_id, conn, today)
        self.abilities.setup_doll()

        # 各フローの移譲先を取得
        following_status = FollowiingStatusRepository(conn, doll_id, today)
        recent_touched_histories = RecentTouchedHistoriesRepository(conn, doll_id, today)
        self.following = Following(self.abilities, following_status, recent_touched_histories)
        self.unfollowing = Unfollowing(self.abilities, following_status, recent_touched_histories)

    def switch_to_instagram_home(self):
        self.abilities.web.switch_to_instagram_home()
