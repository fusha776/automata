from automata.workflow.workflow import WorkFlow
from automata.common.exception import ActionBlockException


def run(worker_id, actions_ff, actions_unfollow, switch_rate=0.8):

    try:
        wf = WorkFlow(worker_id=worker_id)
        # Instagramを起動
        wf.pixel.switch_to_instagram_home()
        wf.pixel.switch_login_id(wf.pixel.login_id)

        # フォロワーのフォロワーに対して、フォロー or fav
        wf.follow_followers_friends(actions_ff, switch_rate)

        # 一定期間を超えたユーザをアンフォロー
        wf.unfollow_expires_users(actions_unfollow)
    except ActionBlockException as e:
        print(e)
        print(f'login_id: {wf.pixel.login_id} # アクションがブロックされたため終了')
    finally:
        # with open('./page_source.log', 'w', encoding='utf8') as f:
        #     f.write(wf.pixel.driver.page_source)
        wf.pixel.driver.quit()
