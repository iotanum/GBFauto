from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import os
import time
import random

from selenium import common as selenium_err


class SpecialQuests:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        #######################
        self.sub_option_num = None
        self.sub_option = None
        self.sub_option_diff_num = None
        self.sub_option_diff = None

    def handle_to_special_quests(self):
        # JS my way to special quest page
        # relative path'ing
        self.driver.execute_script("window.location.href = '#quest/extra'")
        self.bot.wait.for_loading_screen()
        # resume = self.bot.popup.resume_quest()
        # if resume is True:
        #     self.bot.press.usual_retreat()
        #     self.bot.press.usual_ok()
        #     self.bot.press.usual_ok()
        #     self.bot.wait.for_loading_screen()

        # TODO
        self.bot.press.specific_treasure_quest(self.sub_option_num)

        # Since every app update (update varies from 5h to 24h) all of the quest ids
        # gets updated to whatever
        quest_ids = self.get_quest_ids()
        quest_id = self.get_required_quest_id(quest_ids, self.sub_option_diff_num)

        self.bot.press.treasure_quest_diff(quest_id)
        self.handle_not_enough_ap()

    def get_quest_ids(self):
        # wait until special quest sub diff popup appears
        self.bot.popup.special_quest_popup()
        parser = bs(self.driver.page_source, 'lxml')

        elems = parser.find_all('div', {'data-chapter-id': True})
        quest_ids = [elem['data-chapter-id'] for elem in elems]

        # return a list of ids in an order from top to bottom
        return quest_ids

    def get_required_quest_id(self, quest_ids, sub_option_diff_num):
        # list item by index starts from 0
        return quest_ids[sub_option_diff_num - 1]

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
                    self.bot.press.attack_button()
                    self.bot.wait.for_fight_main_mask()
                except (selenium_err.exceptions.NoSuchElementException, selenium_err.exceptions.WebDriverException):
                    pass
            else:
                mobs_alive = False

    def wait_before_fight(self, in_fight=False):
        if in_fight is True:
            self.bot.wait.for_quest_advencment_screen(start=True)
        self.bot.wait.for_loading_screen()
        self.bot.wait.for_quest_advencment_screen()
        self.bot.wait.for_fight_ready_screen()
        self.bot.wait.for_fight_main_mask()

    def handle_fight(self):
        # Count the number of fights that X special quest has
        num_of_fights = self.count_quest_fight_parts()
        first_queue_from_config = os.getenv("QUEUE_FIRST_FIGHT")
        second_queue_from_config = os.getenv("QUEUE_SECOND_FIGHT")
        third_queue_from_config = os.getenv('QUEUE_THIRD_FIGHT')
        queues = [first_queue_from_config, second_queue_from_config, third_queue_from_config]
        for fight_num, queue in enumerate(queues, 1):
            # Don't need to wait on first iteration since getting the number of fights already did that
            self.wait_before_fight(in_fight=True)
            print(f"Fight #{fight_num}.")
            self.bot.queue.do_queue(queue)
            self.finish_fight()
            self.bot.wait.for_fight_main_mask()
            self.bot.press.results_button()
            if fight_num == num_of_fights:
                self.bot.wait.for_fight_end_screen()
                break

    def count_quest_fight_parts(self):
        self.bot.wait.for_quest_advencment_screen(start=True)
        parser = bs(self.driver.page_source, 'lxml')

        progress_bar = parser.find('div', {'class': 'prt-position'})
        quest_parts = progress_bar.find_all('div', {'class': ['lis-spot']})

        if quest_parts == 0:
            quest_parts = 1

        return len(quest_parts)

    def handle_pre_fight_support_summons(self):
        self.bot.wait.for_loading_screen()
        self.bot.press.support_element(5)
        time.sleep(0.5)
        self.bot.press.first_support_summon()
        self.bot.press.confirm_support_summon()

    def convert_seconds_to_hms_format(self):
        seconds = round(self.bot.run_time(), 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def handle_after_fight(self):
        self.bot.wait.for_loading_screen()

        self.bot.handle.after_fight_popups()

        hours, minutes, seconds = self.convert_seconds_to_hms_format()
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {round(self.bot.run_time() / self.bot.total_fights, 2)}s")

        self.bot.wait.for_loot_screen()
        self.bot.press.play_again_quest()

        self.bot.handle.after_fight_popups()

        self.handle_not_enough_ap()

    def handle_not_enough_ap(self):
        self.bot.wait.for_loading_screen()
        not_enough_ap = self.bot.popup.not_enough_x()
        if not_enough_ap is True:
            potion_amount = random.randint(1, 5)
            self.bot.action.use_potions_or_pills(potion_amount)
            self.bot.wait.for_loading_screen()
            self.bot.press.usual_ok()

    def special_quests(self, sub_option_num, sub_option, sub_option_diff_num, sub_option_diff):
        # Assign user input to class vars
        self.sub_option_num = sub_option_num
        self.sub_option = sub_option
        self.sub_option_diff_num = sub_option_diff_num
        self.sub_option_diff = sub_option_diff

        while True:
            self.do_special_quests(repeat=True if self.bot.total_fights > 0 else False)

    def do_special_quests(self, repeat=False):
        # HANDLE PATH TO SPECIAL QUESTS
        if repeat is False:
            self.handle_to_special_quests()

        # SUPPORT SUMMONS
        self.handle_pre_fight_support_summons()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()
