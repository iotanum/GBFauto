from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import os
import time
import random

from selenium import common as selenium_err


class QuestOnRepeat:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        #######################
        self.total_ranks = 0
        self.total_exp = 0
        self.total_fights = 0
        self.start_time = time.time()

    def wait_for_repeatable_quest(self):
        print('\nWaiting for you to enter a repeatable quest...')
        while True:
            url = str(self.driver.current_url)
            if '#quest/supporter' in url:
                print("Locked in on this quest.")
                break
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

            if not all(hp == 0 for hp in mob_hps):
                try:
                    self.bot.press.attack_button()
                    self.bot.wait.for_fight_main_mask()
                except (selenium_err.exceptions.NoSuchElementException, selenium_err.exceptions.WebDriverException):
                    pass
            else:
                mobs_alive = False

    def wait_before_fight(self):
        self.bot.wait.for_loading_screen()
        self.bot.wait.for_quest_advencment_screen()
        self.bot.wait.for_fight_ready_screen()
        self.bot.wait.for_fight_main_mask()

    def handle_fight(self):
        first_queue_from_config = os.getenv("QUEUE_FIRST_FIGHT")
        second_queue_from_config = os.getenv("QUEUE_SECOND_FIGHT")
        third_queue_from_config = os.getenv('QUEUE_THIRD_FIGHT')
        queues = [first_queue_from_config, second_queue_from_config, third_queue_from_config]
        for idx, queue in enumerate(queues, 1):
            self.wait_before_fight()
            self.bot.queue.do_queue(queue)
            self.finish_fight()
            self.bot.wait.for_fight_main_mask()
            self.bot.press.results_button()
            print(f"Fight #{idx}.")

    def handle_pre_fight_support_summons(self):
        self.bot.wait.for_loading_screen()
        self.bot.press.support_element(5)
        self.bot.press.first_support_summon()
        self.bot.press.confirm_support_summon()

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
        self.bot.wait.for_loading_screen()

        for retry_no in range(3):
            try:
                parser = bs(self.driver.page_source, features="lxml")
                gains = parser.find('div', {'class': 'prt-exp-gain'}).find_all('span')
                break
            except AttributeError:
                time.sleep(3)
                gains = None
                continue

        if gains:
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
        self.bot.press.usual_ok()

        # TODO
        # If after pressing a button certain popup appears
        # ignore and/or handle other popups accordingly
        rank_up = self.bot.popup.new_rank()
        if rank_up is True:
            print("New rank!")
            self.bot.press.usual_ok()

        extended_mastery = self.bot.popup.extended_mastery()
        if extended_mastery is True:
            print("New extended mastery!")
            time.sleep(4)
            self.driver.find_element_by_id('cjs-lp-rankup').click()

        self.bot.wait.for_loot_screen()
        self.bot.press.play_again_quest()

        achievement = self.bot.popup.achievement()
        if achievement is True:
            print('New achievement!')
            self.bot.press.usual_close()

        friend_request = self.bot.popup.friend_request()
        if friend_request is True:
            self.bot.press.usual_cancel()

        self.handle_not_enough_ap()

    def handle_not_enough_ap(self):
        self.bot.wait.for_loading_screen()
        not_enough_ap = self.bot.popup.not_enough_x()
        if not_enough_ap is True:
            potion_amount = random.randint(1, 5)
            self.bot.action.use_potions_or_pills(potion_amount)
            self.bot.wait.for_loading_screen()
            self.bot.press.usual_ok()

    def repeatable_quest(self):
        while True:
            self.do_repeatable_quest(repeat=True if self.total_fights > 0 else False)

    def handle_quest_scrolling_screen(self):
        self.bot.wait.for_loading_screen()
        try:
            self.bot.wait.for_side_scroll_entry()
            self.bot.press.usual_skip()
            self.bot.popup.skip_side_scroll()
            self.driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div[2]').click()
            self.bot.popup.side_scroll_results()
            self.driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div').click()
            self.bot.wait.for_loading_screen()
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def do_repeatable_quest(self, repeat=False):
        # HANDLE PATH TO REPEATABLE QUEST
        if repeat is False:
            self.wait_for_repeatable_quest()

        # SUPPORT SUMMONS
        self.handle_pre_fight_support_summons()

        # Scrolling screen
        self.handle_quest_scrolling_screen()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()
