import time
import queue

from threading import Thread


class BattleBackgroundTask:
    def __init__(self, bot):
        self.bot = bot
        self.game_requests = self.bot.game_requests
        self.battle = self.bot.battle
        self.thread.start()
        self.queue = queue.Queue()

    @property
    def thread(self):
        return Thread(target=self.monitor_raid_battle, daemon=True)

    def is_queue_empty(self):
        return self.queue.empty()

    def get_queue(self):
        if not self.is_queue_empty():
            return self.queue.get()

    def _reset_request_time(self):
        self.bot.handle.set_req_time()

    def _get_team_abilities(self, resp: dict):
        if b_status := resp.get("status"):
            return b_status["ability"]

    def _get_used_skill(self, resp: dict):
        try:
            team = self._get_team_abilities(resp)

            for pos, npc in team.items():
                for ability, a_details in npc["list"].items():
                    a_details = a_details[0]
                    a_name = a_details["ability-name"]
                    if a_details["ability-recast"] == a_details["recaset-default"]:
                        msg = (
                            f"NPC @ Pos '{pos}' used an ability ({ability}) '{a_name}'"
                        )
                        # self.skills.put(msg)
                        print(msg)
        except AttributeError as e:
            print(e)

    def monitor_raid_battle(self):
        self._reset_request_time()
        while True:
            req = self.bot.battle.find_ability_result_response()

            if req:
                req = req[0]
                print("found ability result resp!")
                self._reset_request_time()
                print("reset timer")
                r_body = self.bot.game_requests.get_resp_body(req)
                print("body found")
                self._get_used_skill(r_body)
            time.sleep(0.2)
