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
        self.quest_url = None
        # Some solo/raids that can be hosted are not always
        # repeatable, aka doesn't have "play again" button
        self.is_repeatable = False
        # In a context of current quest
        self.num_of_fights = 0

    def wait_for_repeatable_quest(self):
        if not self.quest_url:
            print('\nWaiting for you to enter a repeatable quest...')
        while True:
            url = str(self.driver.current_url)
            if '#quest/supporter' in url:
                if not self.quest_url:
                    self.quest_url = url
                    print("Locked in on this quest.")
                break
            if '#coopraid/room/' in url:
                print("Locked on this CO-OP quest.")
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

    def determine_type_of_quest(self):
        if self.coop is not True:
            # Check if a quest is not repeatable only if it wasn't done
            # before and if total fights is 1 and lower
            if not self.is_repeatable and self.bot.total_fights <= 1:
                self.is_repeatable = self.bot.press.play_again_quest()

            # If quest is repeatable - continue on
            if self.is_repeatable and self.bot.total_fights >= 2:
                self.bot.press.play_again_quest()
            # If not repeatable (ex.: hosting gw bosses)
            # press event home (triggers, IF, nightmare battle popup)
            elif not self.is_repeatable:
                self.bot.press.usual_event_home()
        else:
            self.bot.press.coop_room()

    def use_ap_for_non_repeatables(self):
        self.bot.handle.navigate_to_consumables()
        self.bot.wait.for_loading_screen()
        self.bot.press.consumables()
        self.bot.wait.for_loading_screen()
        self.bot.press.consumables_ap()
        self.bot.handle.not_enough_of_x()
        self.bot.need_ap = False

    def handle_after_fight(self):
        self.bot.wait.for_loading_screen()

        self.bot.handle.after_fight_popups(kill=True)

        hours, minutes, seconds = self.convert_seconds_to_hms_format()
        avg_time_per_quest = round(self.bot.run_time() / self.bot.total_fights, 2)
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {avg_time_per_quest}s")

        self.determine_type_of_quest()
        temp_nightmare_state = False

        nightmare_battle = self.bot.handle.after_fight_popups()
        if nightmare_battle is True:
            self.repeat = False
            # After nightmare battle quest is *obviously*
            # not repeatable, so set a temp state of it to false
            if self.is_repeatable:
                temp_nightmare_state = True
                self.is_repeatable = False
            # self.bot.need_ap = False

        # Use AP (if needed) and navigate to quest if only
        # the quest is not repeatable
        if not self.is_repeatable:
            # If there was a temp false state for repeatable quest
            # after nightmare battle - set it back to true
            if nightmare_battle and temp_nightmare_state:
                self.is_repeatable = True

            if self.bot.need_ap:
                self.use_ap_for_non_repeatables()

            # Navigate back to original quest
            self.go_to_quest()

        self.bot.raid_battle = False

        if '#quest/supporter' not in str(self.driver.current_url):
            self.bot.handle.not_enough_of_x()

    def go_to_quest(self):
        self.driver.execute_script(f"window.location.href = '{self.quest_url}'")

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
        self.bot.option_repeatable = True

        if self.repeat is False:
            self.wait_for_repeatable_quest()
            self.repeat = True

        # PRE-FIGHT STUFF
        self.handle_pre_fight()

        # FIGHT
        self.handle_fight()

        # AFTER FIGHT
        self.handle_after_fight()
