from helpers.buttons import Press
from helpers.screens import Wait
from helpers.popups import Popup
from helpers.skill_queue import Skills
from helpers.actions import Action

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import os
import time
import random
import re

from selenium import common as selenium_err

from dotenv import load_dotenv

load_dotenv('config.env')
SUPPORT_ELEMENT = os.getenv('SUPPORT_ELEMENT')
PICKING_YOURSELF = int(os.getenv('PICKING_SUPPORT_YOURSELF'))


class GW:
    def __init__(self, game_handler):
        self.driver = game_handler.driver
        self.Press = Press(game_handler)
        self.Wait = Wait(game_handler)
        self.Popup = Popup(game_handler)
        self.Actions = Action(game_handler, self.Wait)
        self.queue = Skills(game_handler, self.Press, self.Popup)
        ###########################
        self.gw_raid_type_num = None
        self.gw_raid_type = None
        self.gw_raid_diff_num = None
        self.gw_raid_diff = None
        ###########################
        self.total_rank_points = 0
        self.total_exp = 0
        self.total_honors = 0
        self.total_tokens = 0
        self.total_fights = 0
        self.start_time = time.time()

    # TODO
    def handle_to_gw(self):
        self.Press.guild_wars()
        self.Wait.for_loading_screen()
        self.Press.gw_raid_type(self.gw_raid_type_num)
        if self.gw_raid_type == 'Dimorphodon (Easiest)':
            self.Press.gw_dimorphodon_diff(self.gw_raid_diff_num)
        elif self.gw_raid_type == 'EX (Normal)':
            self.Press.gw_ex_diff(self.gw_raid_diff_num)
        else:
            # For Cybele, since she doesn't have any diffs
            self.Press.usual_ok()

    def remove_battle_scene_element(self):
        try:
            elem = self.driver.find_element_by_class_name('btn-scene-next')
            self.driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", elem)
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def finish_fight(self):
        mobs_alive = True

        # remove the battle scene/advice element from the fight, less clutter
        self.remove_battle_scene_element()

        while mobs_alive is True:
            strainer = ss('div', attrs={'class': 'prt-targeting-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            mob_hps = parser.find_all('span', 'txt-gauge-value')
            mob_hps = [int(hp.text) for hp in mob_hps]

            if not all(hp == 0 for hp in mob_hps):
                try:
                    self.Press.attack_button()
                    self.Wait.fight_main_mask()
                except (selenium_err.exceptions.NoSuchElementException, selenium_err.exceptions.WebDriverException):
                    pass
            else:
                mobs_alive = False

    def wait_before_fight(self):
        self.Wait.for_loading_screen()
        self.Wait.quest_advencment_screen()
        self.Wait.for_fight_ready_screen()
        self.Wait.fight_main_mask()

    def handle_fight(self):
        first_queue_from_config = os.getenv("QUEUE_FIRST_FIGHT")
        self.wait_before_fight()
        self.queue.do_queue(first_queue_from_config)
        self.finish_fight()
        self.Press.results_button()

    def handle_support_manual_pick(self):
        print("Waiting till you pick your supports...")
        while True:
            url = str(self.driver.current_url)
            if "#raid" in url:
                break

    def handle_pre_fight_support_summons(self):
        self.Wait.for_loading_screen()
        if PICKING_YOURSELF == 1:
            self.handle_support_manual_pick()
        else:
            self.Press.support_element(SUPPORT_ELEMENT)
            # TODO
            self.Press.first_support_summon()
            self.Press.confirm_support_summon()

    def convert_gain_to_int(self, gain):
        regex_num_pattern = r'\d+'
        gains = re.findall(regex_num_pattern, gain)
        gain = [int(s) for s in gains]
        return sum(gain)

    def convert_seconds_to_hms_format(self, seconds):
        seconds = round(seconds, 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def count_after_fight_exp(self):
        print(self.Popup.after_fight_xp(), 'xp after fight')

        parser = bs(self.driver.page_source, features="lxml")
        gains = parser.find('div', {'class': 'prt-exp-gain'}).find_all('span')

        for gain in gains:
            if gain is not None:
                gain_name = str(gain['class'])
                gain = self.convert_gain_to_int(gain.text)
                if 'rank' in gain_name:
                    self.total_rank_points += gain
                elif 'exp' in gain_name:
                    self.total_exp += gain

        self.Press.usual_ok()

    def count_after_fight_event_items(self):
        self.Popup.event_items()

        parser = bs(self.driver.page_source, features="lxml")
        gains = parser.find_all('div', {'class': 'prt-event-point'})

        for gain in gains:
            if gain is not None:
                gain_name = str(gain.text)
                gain_num = self.convert_gain_to_int(gain_name)
                if 'tokens' in gain_name:
                    self.total_tokens += gain_num
                elif 'honors' in gain_name:
                    self.total_honors += gain_num

        self.Press.usual_ok()

    def handle_after_fight(self):
        self.Wait.for_loading_screen()
        self.count_after_fight_exp()
        self.count_after_fight_event_items()

        self.total_fights += 1
        run_time = time.time() - self.start_time
        hours, minutes, seconds = self.convert_seconds_to_hms_format(run_time)
        print(f"Total fights: {self.total_fights}, EXP: {self.total_exp}, Rank points: {self.total_rank_points},\n"
              f"Honors: {self.total_honors}, Tokens: {self.total_tokens},\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {round(run_time / self.total_fights, 2)}s")

        # TODO
        # If after pressing a button certain popup appears
        # ignore and/or handle other popups accordingly
        rank_up = self.Popup.new_rank()
        if rank_up is True:
            print("New rank!")
            self.Press.usual_ok()

        extended_mastery = self.Popup.extended_mastery()
        if extended_mastery is True:
            print("New extended mastery!")
            time.sleep(2)
            self.driver.find_element_by_id('cjs-lp-rankup').click()

        self.Wait.for_loot_screen()
        self.Press.play_again_quest()

        achievement = self.Popup.achievement()
        if achievement is True:
            print('New achievement!')
            self.Press.usual_close()

        friend_request = self.Popup.friend_request()
        if friend_request is True:
            self.Press.usual_cancel()

        self.handle_not_enough_ap()

    def handle_not_enough_ap(self):
        self.Wait.for_loading_screen()
        not_enough_ap = self.Popup.not_enough_x()
        if not_enough_ap is True:
            potion_amount = random.randint(1, 5)
            self.Actions.use_potions_or_pills(potion_amount)
            self.Wait.for_loading_screen()
            self.Press.usual_ok()

    def gw(self, raid_type_num, raid_type, raid_diff_num, raid_diff):
        self.gw_raid_type_num = raid_type_num
        self.gw_raid_type = raid_type
        self.gw_raid_diff_num = raid_diff_num
        self.gw_raid_diff = raid_diff

        while True:
            self.do_gw(repeat=True if self.total_fights > 0 else False)

    def do_gw(self, repeat=False):
        # HANDLE PATH TO GW
        if repeat is False:
            self.handle_to_gw()

        # SUPPORT SUMMONS
        self.handle_pre_fight_support_summons()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()
