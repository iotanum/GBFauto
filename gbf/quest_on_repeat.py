from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import os
import time
import random

from selenium import common as selenium_err

from dotenv import load_dotenv

load_dotenv('config.env')

SUPPORT_ELEMENT = int(os.getenv('SUPPORT_ELEMENT'))


class QuestOnRepeat:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.repeat = False

    def wait_for_repeatable_quest(self):
        print('\nWaiting for you to enter a repeatable quest...')
        while True:
            url = str(self.driver.current_url)
            if '#quest/supporter' in url:
                print("Locked in on this quest.")
                break
        # self.handle_not_enough_ap()

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

    def wait_before_fight(self, in_fight=False, raid=False):
        if in_fight is True and raid is False:
            self.bot.wait.for_quest_advencment_screen(start=True)

        self.bot.wait.for_loading_screen()
        self.bot.wait.for_quest_advencment_screen()
        self.bot.wait.for_fight_ready_screen()
        self.bot.wait.for_fight_main_mask()

    def count_quest_fight_parts(self):
        parser = bs(self.driver.page_source, 'lxml')

        progress_bar = parser.find('div', {'class': 'prt-position'})
        quest_parts = progress_bar.find_all('div', {'class': ['lis-spot']})

        # If list is empty - it's a one fight quest
        if not quest_parts:
            quest_parts = [1]

        return len(quest_parts)

    def handle_fight(self):
        self.wait_before_fight()

        # If 'Quest' has backup request screen
        # then it means that it's a raid.
        raid = self.bot.handle.backup_request()
        if raid is False:
            self.bot.wait.for_quest_advencment_screen(start=True)
            num_of_fights = self.count_quest_fight_parts()
        else:
            num_of_fights = 1
            # Raid screen takes time to fully disappear
            time.sleep(0.8)

        first_queue_from_config = os.getenv("QUEUE_FIRST_FIGHT")
        second_queue_from_config = os.getenv("QUEUE_SECOND_FIGHT")
        third_queue_from_config = os.getenv('QUEUE_THIRD_FIGHT')
        queues = [first_queue_from_config, second_queue_from_config, third_queue_from_config]

        for fight_num, queue in enumerate(queues, 1):
            # Don't need to wait on first iteration
            # TODO less clutter
            if fight_num != 1 or raid is True:
                self.wait_before_fight(in_fight=True, raid=True if raid else False)

            print(f"Fight #{fight_num}.")
            self.bot.queue.do_queue(queue)
            self.finish_fight()
            self.bot.wait.for_fight_main_mask()
            time.sleep(1.5)
            self.bot.press.results_button()
            if fight_num == num_of_fights:
                break

    def handle_pre_fight_support_summons(self):
        self.bot.wait.for_loading_screen()
        self.bot.press.support_element(SUPPORT_ELEMENT)
        time.sleep(0.5)
        self.bot.press.first_support_summon()
        captcha = self.bot.handle.human_verification()
        # if verification is required - need to repeat the last step
        if captcha is True:
            self.bot.press.first_support_summon()
        self.bot.press.confirm_support_summon()

    def convert_seconds_to_hms_format(self):
        seconds = round(self.bot.run_time(), 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def handle_after_fight(self):
        self.bot.wait.for_loading_screen()

        # After the page loads, there's no way to 'tell' if there will be
        # x popup or y popup, it load time depends on what popup it is
        # so plain old 'sleep' will do the trick
        time.sleep(3)
        self.bot.handle.after_fight_popups(kill=True)

        hours, minutes, seconds = self.convert_seconds_to_hms_format()
        avg_time_per_quest = round(self.bot.run_time() / self.bot.total_fights, 2)
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {avg_time_per_quest}s")

        self.bot.wait.for_loot_screen()
        self.bot.press.play_again_quest()

        nightmare_battle = self.bot.handle.after_fight_popups()
        if nightmare_battle is True:
            self.repeat = False
            return

        if '#quest/supporter' not in str(self.driver.current_url):
            self.handle_not_enough_ap()

    def handle_not_enough_ap(self):
        self.bot.wait.for_loading_screen()
        not_enough_ap = self.bot.popup.not_enough_x()
        print(not_enough_ap, 'ap handle')
        if not_enough_ap is True:
            potion_amount = random.randint(1, 5)
            self.bot.action.use_potions_or_pills(potion_amount)
            self.bot.wait.for_loading_screen()
            self.bot.press.usual_ok()

    def repeatable_quest(self):
        while True:
            self.do_repeatable_quest()

    def handle_pre_fight(self):
        self.handle_pre_fight_support_summons()
        self.bot.handle.pre_fight_screens()

    def do_repeatable_quest(self):
        # HANDLE PATH TO REPEATABLE QUEST
        if self.repeat is False:
            self.wait_for_repeatable_quest()
            self.repeat = True

        # PRE-FIGHT STUFF
        self.handle_pre_fight()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()
