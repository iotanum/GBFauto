from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import os
import time

from selenium import common as selenium_err


class QuestOnRepeat:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.repeat = False
        self.bot.raid_battle = False
        self.coop = False
        # In a context of current quest
        self.num_of_fights = 0

    def wait_for_repeatable_quest(self):
        print('\nWaiting for you to enter a repeatable quest...')
        while True:
            url = str(self.driver.current_url)
            if '#quest/supporter' in url:
                print("Locked in on this quest.")
                break
            if '#coopraid/room/' in url:
                print("Locked in on this CO-OP quest.")
                self.coop = True
                break

            time.sleep(0.2)

    def remove_battle_scene_element(self):
        try:
            elem = self.driver.find_element_by_class_name('btn-scene-next')
            self.driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", elem)
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def finish_fight(self):
        refreshed = False

        # remove the battle scene/advice element from the fight, less clutter
        self.remove_battle_scene_element()

        while True:
            strainer = ss('div', attrs={'class': 'prt-targeting-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            mob_hps = parser.find_all('span', 'txt-gauge-value')
            mob_hps = [int(hp.text) for hp in mob_hps]

            if not all(hp == 0 for hp in mob_hps):
                try:
                    self.bot.press.attack_button()
                    self.bot.wait.for_fight_main_mask()

                    # Refresh the page (after queue) if quest contains 1 fight (F5 works)
                    # if the quest contains more than 1 fight - use BACK key (to be implemented)
                    if self.num_of_fights == 1 and refreshed is False:
                        refreshed = True
                        self.bot.handle.wait_after_queue_refresh()
                        self.driver.refresh()

                        start = time.time()
                        current_url = str(self.driver.current_url)

                        while True:
                            # Check if url was changed after refreshing
                            after_refresh_url = str(self.driver.current_url)
                            if current_url != after_refresh_url:
                                return True

                            if time.time() - start >= 3:
                                self.bot.handle.wait_before_fight(fight_start=True)

                                # Remove the element again since we refreshed the page
                                self.remove_battle_scene_element()
                                self.bot.handle.backup_request()
                                break

                except (selenium_err.exceptions.NoSuchElementException, selenium_err.exceptions.WebDriverException):
                    pass
            else:
                break

    def count_quest_fight_parts(self):
        parser = bs(self.driver.page_source, 'lxml')

        progress_bar = parser.find('div', {'class': 'prt-position'})
        quest_parts = progress_bar.find_all('div', {'class': ['lis-spot']})

        # If list is empty - it's a one fight quest
        if not quest_parts:
            quest_parts = [1]

        return len(quest_parts)

    def get_start_button_chapter_id(self):
        parser = bs(self.driver.page_source, 'lxml')

        ready_btn = parser.find('div', class_='btn-quest-start multi se-quest-start')
        chapter_id = ready_btn['data-chapter-id']

        return chapter_id

    def handle_fight(self):
        self.bot.handle.pre_fight_screens()
        self.bot.handle.wait_before_fight(fight_start=True)

        # If 'Quest' has a backup request screen
        # then it means that it's a raid.
        self.bot.raid_battle = '#raid_multi' in self.driver.current_url
        if self.bot.raid_battle is True:
            self.bot.handle.backup_request()
            self.num_of_fights = 1
        else:
            self.num_of_fights = self.count_quest_fight_parts()

        first_queue_from_config = os.getenv("QUEUE_FIRST_FIGHT")
        second_queue_from_config = os.getenv("QUEUE_SECOND_FIGHT")
        third_queue_from_config = os.getenv('QUEUE_THIRD_FIGHT')
        queues = [first_queue_from_config, second_queue_from_config, third_queue_from_config]

        for current_fight_num, queue in enumerate(queues, 1):
            # Don't need to wait on first iteration
            if current_fight_num != 1 or self.bot.raid_battle is True:
                self.bot.handle.wait_before_fight(fight_start=False)

            print(f"Fight #{current_fight_num}.")
            self.bot.queue.do_queue(queue)
            fight_ended = self.finish_fight()

            # Press result/next button if quest contains more than 1 fight
            if current_fight_num != self.num_of_fights and self.num_of_fights > 1:
                self.bot.handle.wait_results_button()
                self.bot.press.results_button()

            # Skip animations after completing the quest
            if current_fight_num == self.num_of_fights:
                # Also check if after refreshing the page we're still in a fight
                # or quest contains more than 1 fight
                if 'result' not in self.driver.current_url:
                    if fight_ended is not True or self.num_of_fights > 1:
                        self.driver.refresh()
                break

    def convert_seconds_to_hms_format(self):
        seconds = round(self.bot.run_time(), 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def handle_after_fight(self):
        self.bot.wait.for_loading_screen()

        self.bot.handle.after_fight_popups(kill=True)

        hours, minutes, seconds = self.convert_seconds_to_hms_format()
        avg_time_per_quest = round(self.bot.run_time() / self.bot.total_fights, 2)
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {avg_time_per_quest}s")

        if self.coop is not True:
            self.bot.press.play_again_quest()
        else:
            self.bot.press.coop_room()

        nightmare_battle = self.bot.handle.after_fight_popups()
        if nightmare_battle is True:
            self.repeat = False
            return

        self.bot.raid_battle = False

        if '#quest/supporter' not in str(self.driver.current_url):
            self.bot.handle.not_enough_of_x()

    def repeatable_quest(self):
        while True:
            self.do_repeatable_quest()

    def handle_pre_fight(self):
        if self.coop is False:
            self.bot.handle.pre_fight_support_summons()
        else:
            # Wait until player chooses it's COOP team.
            self.wait_for_coop_prep()

            # And now press 'Ready' to enter the fight.
            chapter_id = self.get_start_button_chapter_id()
            self.bot.press.by_chapter_id(chapter_id)
            # Give it a bigger timer because CO-OP fights
            # take a lot longer to start than your usual fights
            self.bot.handle.not_enough_of_x(timeout=10)

    def wait_for_coop_prep(self):
        found_room = False
        already_in_coop_party = False

        while True:
            parser = bs(self.driver.page_source, 'lxml')

            # First need to wait until the COOP room page has finished loading.
            if found_room is False:
                try:
                    coop_room_loaded = parser.find('div', {'class': 'txt-count-down'}).text
                    found_room = True
                except AttributeError:
                    coop_room_loaded = ''

            if found_room is True or 'Closes' in coop_room_loaded:
                # Check if party is already picked.
                party_ready = parser.find('div', {'class': 'txt-guide'}).text

                if 'Start' in party_ready:
                    print('Starting CO-OP quest.')
                    break
                else:
                    if already_in_coop_party is False:
                        print('Waiting until you pick your team for CO-OP.')
                        already_in_coop_party = True
                        found_room = False

                        previous_url = self.driver.current_url
                        picked = False

                        # please don't judge
                        while True:
                            current_url = self.driver.current_url

                            if current_url != previous_url:
                                picked = True

                            if '#coopraid/room' in current_url and picked is True:
                                break

            time.sleep(0.2)

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
