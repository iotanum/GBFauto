from selenium import common as selenium_err

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import time
import sys
import random
import os


class Raids:
    def __init__(self, game_handler, finder_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.raid_finder = finder_handler
        #########################
        self.raid_id = None
        self.raid_name = ""

    def get_raid_boss_hps(self):
        try:
            strainer = ss('div', attrs={'class': 'prt-targeting-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            raid_boss_hps = parser.find_all('span', 'txt-gauge-value')
            raid_boss_hps = [int(hp.text) for hp in raid_boss_hps]

            return raid_boss_hps
        except AttributeError:
            return

    def monitor_raid_boss_hp(self):
        # monitors and handles attacks, attacks the boss if it's below 50% hp and then just
        # waits until it's dead

        self.bot.handle.wait_before_fight(fight_start=True)
        self.bot.handle.backup_request()
        self.bot.handle.wait_before_fight(fight_start=False)
        queue = os.getenv('QUEUE_FIRST_FIGHT')
        self.bot.queue.do_queue(queue)

        raid_boss_is_alive = True
        made_a_leech_hit = False
        waiting_for_kill = False
        old_raid_boss_hp = []
        hp_timer = time.time()
        stale_hp_timer = time.time()
        times_refreshed = 0

        while raid_boss_is_alive is True:
            raid_boss_hps = self.get_raid_boss_hps()

            if raid_boss_hps is None:
                # This occurs if after refreshing there's no element named "prt-targeting-area"
                # aka bot is no longer in the fight screen
                page = self.handle_return_page()
                print("After refreshing I returned to ", page)
                # return False if fight ended (after refreshing the page) prematurely
                # skip remaining steps after this method
                if "#result_multi" in page:
                    raid_boss_is_alive = False
                    break

            # monitor for how long raid boss hp/hps hasn't changed
            if old_raid_boss_hp != raid_boss_hps:
                old_raid_boss_hp = raid_boss_hps
                # If HP changed - reset the timer
                hp_timer = time.time()
            else:
                stale_hp_timer = time.time()

            if stale_hp_timer - hp_timer >= 60:
                print("Raid boss HP didn't change for 60 seconds, refreshing.")
                self.driver.refresh()
                self.bot.wait.for_loading_screen()
                self.bot.handle.backup_request()
                # If this handle returns 'none' it means that the raid boss is dead
                # or bot is outside raid boss battle
                page = self.handle_return_page()
                if page is None:
                    return False
                stale_hp_timer = 0
                times_refreshed += 1

            if times_refreshed == 2:
                try:
                    self.bot.press.attack_button()
                except selenium_err.exceptions.NoSuchElementException:
                    pass
                times_refreshed = 0

            battle_finished = self.bot.popup.battle_concluded()
            if battle_finished is True:
                self.bot.press.usual_ok()

            if any(0 < hp <= 50 for hp in raid_boss_hps) and made_a_leech_hit is False:
                try:
                    self.bot.press.attack_button()
                    print('Made the leech hit.')
                    made_a_leech_hit = True
                except selenium_err.exceptions.WebDriverException:
                    continue
            elif made_a_leech_hit is True and waiting_for_kill is False:
                print("Waiting for the raid boss to be killed..")
                waiting_for_kill = True
            elif all(hp == 0 for hp in raid_boss_hps):
                print("Raid boss is defeated.")
                raid_boss_is_alive = False
            time.sleep(0.15)

    def get_raid_id(self):
        # Get a RAID ID from raid_finder
        self.raid_id = self.raid_finder.get_raid(self.raid_name)

    def type_and_join_raid(self):
        self.get_raid_id()
        self.bot.action.input_raid_id(self.raid_id)
        time.sleep(0.5)
        self.driver.find_element_by_class_name("btn-post-key").click()

    def handle_entering_raid(self):
        self.type_and_join_raid()
        self.handle_not_enough_ep()
        # Check if everything is ok after typing and entering the raid
        popup = self.bot.handle.pre_fight_popup()
        # If there was a popup, try another raid/repeat last instruction
        if popup:
            self.type_and_join_raid()
        # If everything is OK - continue picking support
        else:
            # Try picking support summon
            success = self.bot.handle.pre_fight_support_summons()
            if success is False:
                # If there was a popup - move bot to 'raids' page
                self.handle_to_raids()
                # And repeat whole function
                self.handle_entering_raid()

        print(f"Joined raid '{self.raid_id}'.")

    def handle_return_page(self):
        self.bot.wait.for_loading_screen()
        current_page = str(self.driver.current_url)

        if '#mypage' in current_page:
            self.handle_to_raids()
            return ['enter_raid_func']
        elif '#raid_multi' in current_page:
            return True
        elif '#result_multi' in current_page:
            return
        elif '#quest' in current_page:
            return
        elif 'empty' in current_page:
            return
        else:
            sys.exit(f"Returned to unknown destination: {current_page}")

    def handle_raid_mechanics(self):
        self.bot.wait.for_loading_screen()

        # Happens ever so often that after joining the raid
        # raid boss is immediately killed.
        page = self.handle_return_page()
        if page is None:
            print("Wasn't fast enough to join the read - Raid Boss is dead.")
            return False

        success = self.monitor_raid_boss_hp()
        if success is not False:
            try:
                self.bot.press.results_button()
            except selenium_err.exceptions.ElementNotVisibleException:
                self.driver.refresh()
                self.bot.wait.for_loading_screen()

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
        print('-----------------------------------------------------------------------')
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Pendants: {self.bot.total_pendants}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {avg_time_per_quest}s")
        print('-----------------------------------------------------------------------')

        page = self.handle_return_page()
        if page is not None:
            self.bot.wait.for_loot_screen()

        return

    def handle_to_raids(self):
        self.bot.wait.for_loading_screen()
        # JS my way to 'raids' page
        self.driver.execute_script("window.location.href = '#quest/assist'")
        # And then press the 'Enter ID' tab
        self.bot.press.enter_raid_id()

    def handle_not_enough_ep(self):
        self.bot.wait.for_loading_screen()
        not_enough_ep = self.bot.popup.not_enough_x()
        if not_enough_ep is True:
            pill_amount = random.randint(1, 10)
            self.bot.action.use_potions_or_pills(pill_amount)
            self.bot.wait.for_loading_screen()
            self.bot.press.usual_ok()

    def set_raid_name(self, raid_boss_name):
        self.raid_name = raid_boss_name

    def raids(self):
        while True:
            self.do_raids()

    def do_raids(self):
        # BEFORE RAID HANDLING HERE
        self.handle_to_raids()

        # SEARCH/ENTER FOR ACTIVE RAID HERE
        self.handle_entering_raid()

        # INSIDE RAID HANDLING HERE
        success = self.handle_raid_mechanics()
        if success is False:
            return

        # AFTER RAID HANDLING HERE
        self.handle_after_fight()
