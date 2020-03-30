from automata.workflow.workflow import WorkFlow
import sys


def run():

    try:
        wf = WorkFlow(worker_id='arc_corp_1')
        # wf.pixel.driver.quit()
        # sys.exit()

        # with open('./page_source.log', 'w') as f:
        #     f.write(wf.pixel.driver.page_source)
        # sys.exit()

        # Instagramを起動
        wf.pixel.switch_to_instagram_home()

        # フォロワーのフォロワーをフォロー
#        wf.follow_followers_friends(3)

        # 一定期間を超えたユーザをアンフォロー
        wf.unfollow_expires_users(2)

    finally:
        with open('./page_source.log', 'w', encoding='utf8') as f:
            f.write(wf.pixel.driver.page_source)
        wf.pixel.driver.quit()
