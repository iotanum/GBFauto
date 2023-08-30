import json
import time
import traceback

import selenium.common.exceptions
from selenium.common.exceptions import WebDriverException


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

    def is_parsed_battle_info_valid(self, battle):
        if not battle:
            return False

        if len(battle.keys()) < 2:
            return False

        return True

    def get_battle_start_info(self):
        timeout = 10
        start = time.time()

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
            if req_id := self.game_requests.find_battle_start_response():
                resp = self.bot.game_requests.get_resp_body(req_id)
                battle = self.parse_battle_start(resp)
                if self.is_parsed_battle_info_valid(battle):
                    return battle

            # If uri in URL has 'result' in it then battle is over
            if self.bot.handle.results_screen():
                print("Battle finished, 'result' in URL.")
                return

    def get_summon_confirm_info(self):
        filter_uri_contains = ["raid_deck_data_create", "user_action_point"]
        resp_body = None

        while True:
            for filter_uri in filter_uri_contains:
                request_id = self.game_requests.find_generic_request(filter_uri)
                print(request_id, filter_uri, "testetstestest")
                if request_id:
                    resp_body = self.bot.game_requests.get_resp_body(request_id)
                    print(resp_body, "pleaseplaepslapelsae")
                    return resp_body

            if not self.bot.handle.supporter_screen():
                break

        return resp_body
