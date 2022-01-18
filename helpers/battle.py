import json
from selenium.common.exceptions import WebDriverException


class BattleInfo:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.game_requests = self.bot.game_requests

    def transform_response(self, request_id):
        while True:
            try:
                resp_body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                resp_body = json.loads(resp_body['body'])
                return resp_body
            except WebDriverException:
                print("Battle start response didn't load, retrying.")
                continue

    def parse_battle_start_info(self, resp):
        battle = dict()

        # battles/total battles are easy
        battle['battle'] = resp['battle']['count']
        battle['total_battles'] = resp['battle']['total']

        # ougies are placed within player obj in root['player']['param']
        ougi_bars = []
        for player in resp['player']['param']:
            # we only want to know ougies for the frontline
            if len(ougi_bars) == 4:
                break
            ougi_bars.append(player['recast'])

        ougies = 0
        for ougi_bar in ougi_bars:
            if ougi_bar != 100 and ougi_bar != 200:
                continue
            ougies += 1

        battle['ougies'] = ougies

        # turn is self explanatory
        battle['turn'] = resp['turn']

        # boss_hp is the same as player ougies above
        boss_hps = []
        for boss in resp['boss']['param']:
            hp_max = int(boss['hpmax'])
            current_hp = int(boss['hp'])
            hp_perc = (current_hp / hp_max) * 100
            boss_hps.append(hp_perc)

        battle['boss_hps'] = boss_hps

        return battle

    def get_battle_start_info(self):
        while True:
            request_ids = self.game_requests.find_battle_start_response()
            if request_ids:
                # everything returned from request searching is in a list
                # and starting request of a battle will obviously
                # happen only once
                request_id = request_ids[0]
                response = self.transform_response(request_id)
                battle = self.parse_battle_start_info(response)
                return battle
