from automata.workflow.workflow import WorkFlow


def run(worker_id, actions):

    try:
        wf = WorkFlow(worker_id=worker_id)
        # Instagramを起動
        wf.pixel.switch_to_instagram_home()
        wf.pixel.switch_login_id(wf.pixel.login_id)

        # フォロワーのフォロワーをフォロー
        wf.follow_followers_friends(actions)

        # 一定期間を超えたユーザをアンフォロー
#        wf.unfollow_expires_users(2)

    finally:
        # with open('./page_source.log', 'w', encoding='utf8') as f:
        #     f.write(wf.pixel.driver.page_source)
        wf.pixel.driver.quit()
