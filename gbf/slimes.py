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

from selenium import common as selenium_err


class Slimes:
    def __init__(self, game_handler):
        self.driver = game_handler.driver
        self.Press = Press(game_handler)
        self.Wait = Wait(game_handler)
        self.Popup = Popup(game_handler)
        self.Actions = Action(game_handler, self.Wait)
        self.queue = Skills(game_handler, self.Press, self.Popup)
        self.total_ranks = 0
        self.total_exp = 0
        self.total_fights = 0
        self.start_time = time.time()

    def handle_to_slimes(self):
        self.Press.quest_button_main_menu()
        self.Wait.for_loading_screen()
        resume = self.Popup.resume_quest()
        if resume is True:
            self.Press.usual_cancel()
            time.sleep(1)
        self.Press.special_quests()
        self.Press.slime_special_quest()
        self.Press.slime_option_3()
        self.handle_not_enough_ap()

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
        # fight_start = time.time()

        while mobs_alive is True:
            strainer = ss('div', attrs={'class': 'prt-targeting-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            mob_hps = parser.find_all('span', 'txt-gauge-value')
            mob_hps = [int(hp.text) for hp in mob_hps]

            # advice = self.Popup.fight_advice()
            # if advice:
            #     self.Press.fight_advice()

            # if time.time() - fight_start > 20:
            #     self.driver.refresh()
            #     self.Wait.for_loading_screen()

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
        second_queue_from_config = os.getenv("QUEUE_SECOND_FIGHT")
        queues = [first_queue_from_config, second_queue_from_config]
        for queue in queues:
            print('running', queue)
            self.wait_before_fight()
            self.queue.do_queue(queue)
            self.finish_fight()
            self.Press.results_button()

    def handle_pre_fight_support_summons(self):
        self.Wait.for_loading_screen()
        self.Press.support_element(5)
        self.Press.first_support_summon()
        self.Press.confirm_support_summon()

    def convert_gains_to_int(self, gain):
        to_remove_chars = " +)sEXP"
        extracted_numbers = str(gain)[-5:].strip(to_remove_chars)
        return int(extracted_numbers)

    def convert_seconds_to_hms_format(self, seconds):
        seconds = round(seconds, 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def handle_after_fight(self):
        self.Wait.for_loading_screen()
        print(self.Popup.after_fight_xp(), 'xp after fight')
        parser = bs(self.driver.page_source, features="lxml")
        gains = parser.find('div', {'class': 'prt-exp-gain'}).find_all('span')

        for gain in gains:
            if gain is not None:
                gain_name = str(gain['class'])
                gain = self.convert_gains_to_int(gain.text)
                if 'rank' in gain_name:
                    self.total_ranks += gain
                elif 'exp' in gain_name:
                    self.total_exp += gain

        self.total_fights += 1
        run_time = time.time() - self.start_time
        hours, minutes, seconds = self.convert_seconds_to_hms_format(run_time)
        print(f"Total fights: {self.total_fights}, EXP: {self.total_exp}, Rank points: {self.total_ranks}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {round(run_time / self.total_fights, 2)}s")
        self.Press.usual_ok()

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

    def slime_blast(self):
        while True:
            self.do_slime_blasting(repeat=True if self.total_fights > 0 else False)

    def do_slime_blasting(self, repeat=False):
        # HANDLE PATH TO SLIME QUEST
        if repeat is False:
            self.handle_to_slimes()

        # SUPPORT SUMMONS
        self.handle_pre_fight_support_summons()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()