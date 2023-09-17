import time
import traceback


class BattleInfo:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.game_requests = self.bot.game_requests

    def parse_battle_start(self, resp):
        battle = dict()
        try:
            # battles/total/turn battles are easy
            battle["turn"] = resp["turn"]
            battle["battle"] = int(resp["battle"]["count"])
            battle["total_battles"] = resp["battle"]["total"]

            # ougies are placed within player obj in root['player']['param']
            ougi_bars = []
            for player in resp["player"]["param"]:
                # we only want to know ougies for the frontline
                if len(ougi_bars) == 4:
                    break
                ougi_bars.append(player["recast"])

            ougies = 0
            for ougi_bar in ougi_bars:
                if ougi_bar != 100 and ougi_bar != 200:
                    continue
                ougies += 1

            battle["ougies"] = ougies

            # boss_hp is the same as player ougies above
            boss_hps = []
            for boss in resp["boss"]["param"]:
                hp_max = int(boss["hpmax"])
                current_hp = int(boss["hp"])
                hp_perc = (current_hp / hp_max) * 100
                boss_hps.append(hp_perc)

            battle["boss_hps"] = boss_hps

            return battle
        except KeyError as e:
            print("Error'd on battle info parse.")
            if "redirect" in resp.keys():
                print("Battle ended, cuz start.json returned a redirect.")
                return
            traceback.print_exc()
            print(resp)
            return

    def is_battle_resp_valid(self, battle):
        if not battle:
            return False

        if len(battle.keys()) < 2:
            return False

        return True

    def check_battle_info(self, req):
        body = self.bot.game_requests.get_resp_body(req)
        if self.is_battle_resp_valid(body):
            return self.parse_battle_start(body)

    def handle_battle_start_info(self):
        timeout = 15
        start = time.time()
        self.bot.handle.set_req_time()

        while True:
            # Fail safe
            if time.time() - start > timeout:
                print("Battle start info not found. Retrying..")
                self.bot.handle.refresh_page()
                start = time.time()

            # Don't search for battle start info if we're in supporter screen
            if self.bot.handle.supporter_screen():
                continue

            # Find battle start response
            if req := self.find_battle_start_response():
                if battle := self.check_battle_info(req[0]):
                    return battle

            # If uri in URL has 'result' in it then battle is over
            if self.bot.handle.results_screen():
                print("Battle finished, 'result' in URL.")
                return

    def find_after_confirm_response(self):
        # first one for raids, second one for quests, third one for battle start
        req_contains = ["raid_deck_data_create", "create_quest", "start.json"]
        return self.game_requests.find_request(req_contains)

    def find_attack_btn_response(self):
        req_contains = ["normal_attack_result"]
        return self.bot.game_requests.find_request(req_contains)

    # contains information of a battle start situation
    def find_battle_start_response(self):
        req_contains = ["start.json"]
        return self.bot.game_requests.find_request(req_contains)

    def find_raid_assist_response(self):
        req_contains = ["quest/assist/search/assist_list"]
        return self.bot.game_requests.find_request(req_contains)

    def find_ability_result_response(self):
        req_contains = ["ability_result.json"]
        return self.bot.game_requests.find_request(req_contains)
