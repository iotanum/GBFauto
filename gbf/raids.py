from selenium import common as selenium_err

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss
from dotenv import load_dotenv

import time
import os


class Raids:
    def __init__(self, game_handler, finder_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.raid_finder = finder_handler
        self.bot.raid_battle = True
        #########################
        self.raid_id = None
        self.raid_name = ""

    def get_raid_boss_hps(self):
        try:
            strainer = ss('div', attrs={'class': 'prt-targeting-area main-tap-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            raid_boss_hps = parser.find_all('span', 'txt-gauge-value')
            raid_boss_hps = [int(hp.text) for hp in raid_boss_hps]

            return raid_boss_hps
        except AttributeError:
            return

    def enable_auto_in_loading_screen(self):
        start = time.time()

        while True:
            if time.time() - start >= 10:
                break

            try:
                parser = bs(self.driver.page_source, 'lxml')

                auto_enabled_button = parser.find_all('div', {'class': ['btn-ready-auto', 'anim-simple-fadein']})

                if not auto_enabled_button:
                    self.driver.find_element_by_class_name('txt-auto-setting').click()
                else:
                    print("Since there's no queue - enabled auto attacks.")
                    break
            except:
                continue

    def monitor_raid_boss_hp(self):
        # monitors and handles attacks, attacks the boss if it's below 50% hp and then just
        # waits until it's dead

        # Monkey patch to load stuff config real time while bot is running
        load_dotenv('config.env', override=True)
        queue = os.getenv('QUEUE_FIRST_FIGHT')

        # If there's no queue - just enable auto stuff in the loading screen
        if not queue:
            self.enable_auto_in_loading_screen()

        self.bot.handle.wait_before_fight(fight_start=True)
        self.bot.handle.backup_request()
        self.bot.handle.wait_before_fight(fight_start=False)

        if queue:
            self.bot.queue.do_queue(queue)

        raid_boss_is_alive = True
        made_a_leech_hit = False
        waiting_for_kill = False
        old_raid_boss_hp = []
        hp_timer = time.time()
        stale_hp_timer = 0
        times_refreshed = 0
        point_threshold_reached = False

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

            # Check if HP is 0
            if all(hp == 0 for hp in raid_boss_hps):
                print("Raid boss is defeated.")
                raid_boss_is_alive = False
                self.driver.refresh()

            # monitor for how long raid boss hp/hps hasn't changed
            if old_raid_boss_hp != raid_boss_hps:
                old_raid_boss_hp = raid_boss_hps
                # If HP has changed - reset the timer
                # hp_timer = time, when HP has changed
                hp_timer = time.time()
            else:
                # If HP hasn't changed - subtract hp_timer with current time
                # = seconds for how long HP hasn't changed
                stale_hp_timer = time.time() - hp_timer

            # If stale_hp_timer is more or equal 60 seconds - refresh the page.
            if stale_hp_timer >= 60:
                print("Raid boss HP didn't change for 60 seconds, refreshing.")
                stale_hp_timer = 0
                hp_timer = time.time()
                times_refreshed += 1
                self.driver.refresh()

                if not queue:
                    self.enable_auto_in_loading_screen()

                self.bot.handle.wait_before_fight(fight_start=False)
                # Reset everything after refresh
                self.bot.handle.backup_request()
                # If this handle returns 'none' it means that the raid boss is dead
                # or bot is outside raid boss battle
                page = self.handle_return_page(fight_end=True)
                if page is None:
                    return False

            if times_refreshed == 2:
                try:
                    self.bot.press.attack_button()
                except:
                    pass
                times_refreshed = 0

            battle_finished = self.bot.popup.battle_concluded()
            if battle_finished is True:
                self.bot.press.usual_ok()

            # Check if raid points are up to threshold
            if self.bot.point_threshold:
                if made_a_leech_hit is True:

                    points = self.bot.handle.raid_points()
                    if points >= int(self.bot.point_threshold) and point_threshold_reached is False:
                        self.bot.press.auto_attack()
                        point_threshold_reached = True
                        print('Point limit reached. Turning off auto attacks.')

            if any(0 < hp <= 101 for hp in raid_boss_hps) and made_a_leech_hit is False and queue:
                try:
                    self.bot.press.attack_button()
                    print('Made the leech hit.')
                    made_a_leech_hit = True

                    if self.bot.point_threshold:
                        self.bot.press.auto_attack()
                        print(f'Auto attacks are on until I reach {self.bot.point_threshold} points.')
                except selenium_err.exceptions.WebDriverException:
                    continue

            if (made_a_leech_hit is True and waiting_for_kill is False) or \
                    (not queue and waiting_for_kill is False):
                print("Waiting for the raid boss to be killed..")
                waiting_for_kill = True

            time.sleep(0.3)

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
        self.bot.handle.not_enough_of_x()

        # This handles everything related to summon picking before fight
        success = self.bot.handle.pre_fight_support_summons()
        print("success handle_entering_raid", success)
        if success is False and '#quest/supporter' in self.driver.current_url:
            # If there was a popup in summon page - move bot to 'raids' page
            self.handle_to_raids()
            # And repeat whole function
            self.handle_entering_raid()
        elif success is False and '#quest/assist' in self.driver.current_url:
            self.handle_entering_raid()

        print(f"Joined raid '{self.raid_id}'.")

    def handle_return_page(self, fight_end=False):
        # self.bot.wait.for_loading_screen()

        change_time = 2
        start_time = time.time()
        before_joining_url = str(self.driver.current_url)
        while True:
            current_page = str(self.driver.current_url)

            if time.time() - start_time > change_time and current_page == before_joining_url:
                print(f"URL didn't change in {change_time}s. Searching for another raid.")
                return

            if current_page != before_joining_url or fight_end is True:
                print('different url')
                if '#raid_multi' in current_page:
                    return True

                if 'empty' in current_page:
                    return

                if '#result_multi' in current_page:
                    return

                if '#quest' in current_page:
                    self.driver.refresh()
                    return

                if '#supporter_raid' in current_page:
                    return

                if '#mypage' in current_page:
                    self.handle_to_raids()
                    return ['enter_raid_func']

            time.sleep(0.1)

    def handle_raid_mechanics(self):
        # self.bot.wait.for_loading_screen()

        # Happens ever so often that after joining the raid
        # raid boss is immediately killed.
        page = self.handle_return_page()
        if page is None:
            print(self.driver.current_url)
            print("Wasn't fast enough to join the read - Raid Boss is dead.")
            return False

        self.monitor_raid_boss_hp()

    def convert_seconds_to_hms_format(self):
        seconds = round(self.bot.run_time(), 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def handle_after_fight(self):
        initial_url = str(self.driver.current_url)
        self.bot.wait.for_loading_screen()

        self.bot.handle.after_fight_popups(kill=True)

        hours, minutes, seconds = self.convert_seconds_to_hms_format()

        if self.bot.total_fights == 0:
            self.bot.total_fights += 1

        avg_time_per_quest = round(self.bot.run_time() / self.bot.total_fights, 2)
        print('-----------------------------------------------------------------------')
        print(f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
              f"Pendants: {self.bot.total_pendants}\n"
              f"Running for {hours}h:{minutes}min:{seconds}s, "
              f"Average time per quest: {avg_time_per_quest}s")
        print('-----------------------------------------------------------------------')

        page = self.handle_return_page(fight_end=True)
        if page is not None:
            self.bot.wait.for_loot_screen()

        return

    def handle_to_raids(self):
        self.bot.wait.for_loading_screen()
        # JS my way to 'raids' page
        self.driver.execute_script("window.location.href = '#quest/assist'")
        # And then press the 'Enter ID' tab
        time.sleep(0.5)
        self.bot.press.enter_raid_id()

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
