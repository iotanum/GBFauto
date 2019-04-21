from selenium import common as selenium_err

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss
from dotenv import load_dotenv

import time
import sys
import random
import os

load_dotenv('config.env')

MANUAL_SUPPORT_PICK = int(os.getenv('MANUAL_SUPPORT_PICKING'))


class Raids:
    def __init__(self, game_handler, finder_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.raid_finder = finder_handler
        #########################
        self.raid_id = None
        self.raid_name = ""
        self.total_kills = 0
        self.total_xp = 0
        self.total_pendants = 0

    def handle_backup_request_screen(self):
        backup_popup = self.bot.popup.backup_request()

        if backup_popup is True:
            try:
                # approve_request_backup_css = ".btn-usual-text.with-potion"
                try:
                    self.bot.press.approve_backup_request()
                    self.bot.press.usual_ok()
                except selenium_err.exceptions.NoSuchElementException:
                    self.bot.press.usual_ok()
                # self.driver.find_element_by_css_selector(approve_request_backup_css).click()
                # self.find_and_handle_div("btn-usual-ok", arg='class')
            except selenium_err.exceptions.TimeoutException:
                pass

    def monitor_raid_boss_hp(self):
        # monitors and handles attacks, attacks the boss if it's below 50% hp and then just
        # waits until it's dead

        # TODO
        self.bot.wait.for_test_fight_ready_mask()
        queue = os.getenv('QUEUE_FIRST_FIGHT')
        self.bot.queue.do_queue(queue)

        raid_boss_is_alive = True
        made_a_leech_hit = False
        waiting_for_kill = False
        just_entered_raid = True
        old_raid_boss_hp = []
        stale_hp_time = 0
        times_refreshed = 0

        while raid_boss_is_alive is True:
            strainer = ss('div', attrs={'class': 'prt-targeting-area'})
            parser = bs(self.driver.page_source, 'lxml', parse_only=strainer)

            try:
                raid_boss_hps = parser.find_all('span', 'txt-gauge-value')
                raid_boss_hps = [int(hp.text) for hp in raid_boss_hps]
            except AttributeError:
                # This occurs if after refreshing there's no element named "prt-targeting-area"
                # aka bot is no longer in the fight screen
                page = self.handle_return_page()
                print("After refreshing I returned to ", page)
                # return False if fight ended (after refreshing the page) prematurely
                # skip remaining steps after this method
                if "#result_multi" in page:
                    raid_boss_is_alive = False
                elif "#raid_multi" in page:
                    self.bot.press.attack_button()
                else:
                    return False

            # monitor time of how long raid boss hp/hps hasn't changed
            # send help
            if old_raid_boss_hp != raid_boss_hps:
                old_raid_boss_hp = raid_boss_hps
                # if raid boss hp has changed - reset the timer
                stale_hp_time = 0
            else:
                if just_entered_raid is True:
                    # initialize the 'timer' for 'if stale hp'
                    old_stale_hp_time = time.time()
                    just_entered_raid = False
                # Subtract old stale hp time with the new initialized stale hp timer and
                # calculate how many seconds raid boss's hp haven't changed
                stale_hp_timer = time.time()
                stale_hp_time += stale_hp_timer - old_stale_hp_time
                old_stale_hp_time = stale_hp_timer

            # need to rewrite this logic, so the bot would leave 'stale' raids.
            if stale_hp_time >= 30:
                print("Raid boss HP didn't change for 30 seconds, refreshing.")
                self.driver.refresh()
                self.bot.wait.for_loading_screen()
                self.bot.wait.for_fight_ready_screen()
                stale_hp_time = 0
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

    def handle_not_enough_ep(self):
        ep_popup = self.bot.popup.not_enough_x()
        print(ep_popup, 'ep')
        rand = random.randint(10, 15)

        if ep_popup is True:
            self.bot.action.use_potions_or_pills(rand)
            self.bot.press.usual_ok()
            return True

    def handle_pre_raid_popups(self):
        pre_raid_popup = self.bot.popup.pre_raid_popup()

        if pre_raid_popup is True:
            parser = bs(self.driver.page_source, features='lxml')
            need_ep = self.handle_not_enough_ep()
            if need_ep is True:
                return False
            verification = self.handle_verification(parser)
            if verification is True:
                return True
            self.bot.press.usual_ok()
            return True
        else:
            return False

    def handle_verification(self, parser):
        verification = self.bot.popup.human_verification()

        if verification is True:
            for popup in parser.find_all('div', {'class': ['pop-usual', 'common-pop-error', 'pop-show']}):
                verification_div = popup.find('div', {'class': 'prt-popup-header'})
                if verification_div.text == 'Access Verification':
                    # Need to sleep this, because the captcha image takes time to load
                    time.sleep(3)
                    self.driver.save_screenshot('verification/screenshot.png')
                    send_button_class_name = 'btn-talk-message'
                    input_field = self.driver.find_element_by_class_name('frm-message')
                    verification_code = input('Input verification code: ')
                    input_field.send_keys(verification_code)
                    time.sleep(1)
                    self.driver.find_element_by_class_name(send_button_class_name).click()
                    time.sleep(1)
                break
            return True
        else:
            return False

    def get_raid_id(self):
        # raid_finder.py get_raid method with raid name as an argument
        # returns raid ID on what you searched
        self.raid_id = self.raid_finder.get_raid(self.raid_name)

    def handle_manual_support_pick(self):
        print("Waiting till you pick your supports...")
        while True:
            url = str(self.driver.current_url)
            popup = self.bot.popup.pre_raid_popup()
            if popup is True:
                break
            elif "#raid" in url:
                break

    def handle_picking_summon(self):
        if MANUAL_SUPPORT_PICK != 1:
            self.bot.press.support_element(5)
            self.bot.press.first_support_summon()
            return 'auto'
        else:
            self.handle_manual_support_pick()
            return 'manual'

    def type_and_join_raid(self):
        self.get_raid_id()
        self.bot.action.input_raid_id(self.raid_id)
        self.driver.find_element_by_class_name("btn-post-key").click()

    def handle_entering_raid(self):
        run_queue = {'enter_raid_func': self.type_and_join_raid,
                     'select_first_summon_func': self.handle_picking_summon,
                     'confirm_support_func': self.bot.press.confirm_support_summon}

        processed_queue = ['enter_raid_func']
        done = False

        # my queue implementation (?) for repeating actions in case of an
        # pre-described popups and/or errors
        # 'while' loop is needed because the for loop is only
        # capable of queueing actions and not for finishing them.
        # Also 'queueing' is hardcoded with functions and actions, AKA not for dynamic usage
        while done is False:
            for func in processed_queue:
                summon_pick_method = run_queue[func]()
                if summon_pick_method == 'manual':
                    done = True
                    break
                popup = self.handle_pre_raid_popups()
                if popup is True:
                    if func == 'enter_raid_func':
                        processed_queue = ['enter_raid_func']
                    else:
                        processed_queue = self.handle_return_page()
                else:
                    next_queue_num = list(run_queue.keys()).index(func) + 1
                    try:
                        next_queue = list(run_queue)[next_queue_num]
                        processed_queue = [next_queue]
                    except IndexError:
                        print(f"Joined raid '{self.raid_id}'.")
                        done = True

    def handle_return_page(self):
        self.bot.wait.for_loading_screen()
        return_page = str(self.driver.current_url)
        print(return_page)

        if return_page.endswith("#mypage"):
            self.handle_to_raids()
            return ['enter_raid_func']
        elif 'supporter_raid' in return_page:
            return ['select_first_summon_func']
        elif '#result_multi' in return_page:
            # self.handle_after_fight()
            return return_page
        elif '#quest' in return_page:
            return
        else:
            sys.exit(f"Returned to unknown destination: {return_page}")

    def convert_gains_to_int(self, gain):
        to_remove_chars = " +)s"
        extracted_numbers = str(gain)[-5:].strip(to_remove_chars)
        return int(extracted_numbers)

    def collect_raid_results(self):
        xp = self.bot.popup.after_fight_xp()
        print(xp, 'xp popup after fight')
        if xp is True:
            parser = bs(self.driver.page_source, features="lxml")
            rank_points = parser.find('div', {'class': 'txt-rankpt'})
            rank_points_bonus = parser.find('span', {'class': "exp-bonus"})
            r_pendants = parser.find('span', {'class': "txt-mbp-plus"})
            r_pendants_bonus = parser.find('span', {'class': "txt-add-bonus"})

            raid_gains = {'rank_xp': rank_points,
                          'rank_xp_bonus': rank_points_bonus,
                          'pendants': r_pendants,
                          'pendants_bonus': r_pendants_bonus}

            for gain_name, gain in raid_gains.items():
                if gain is not None:
                    if gain_name is 'rank_xp':
                        gain = gain.find('span')
                        gain = self.convert_gains_to_int(gain.text)
                        self.total_xp += gain
                        continue
                    gain = self.convert_gains_to_int(gain.text)
                    if 'rank' in gain_name:
                        self.total_xp += gain
                    elif 'pendants' in gain_name:
                        self.total_pendants += gain
            self.total_kills += 1
            self.bot.press.usual_ok()
        else:
            loot_after_fight = self.bot.wait.for_loot_screen()
            if loot_after_fight is True:
                self.total_kills += 1
                print("Loot is present, but no XP/Pendants.")
            else:
                print("No loot and no XP, probably wasn't fast enough to make a hit.")

    # help
    # TODO
    def handle_raid_mechanics(self):
        self.bot.wait.for_loading_screen()
        boss_alive = self.bot.wait.for_fight_ready_screen()
        # no_loot_screen = self.handle_no_loot_screen()

        if boss_alive is True:
            try:
                self.handle_backup_request_screen()
                result = self.monitor_raid_boss_hp()
                if result is False:
                    return False
                try:
                    self.bot.wait.for_fight_end_screen()
                    self.bot.press.results_button()
                except selenium_err.exceptions.NoSuchElementException:
                    print('After refresh I landed in results page.')
            except selenium_err.exceptions.ElementNotVisibleException:
                try:
                    self.bot.press.attack_button()
                    self.bot.press.results_button()
                except selenium_err.exceptions.NoSuchElementException:
                    self.bot.press.results_button()

    def handle_friend_request(self):
        friend_request = self.bot.popup.friend_request()

        if friend_request is True:
            self.bot.press.usual_cancel()

    def handle_extended_mastery(self):
        ex_mastery = self.bot.popup.extended_mastery()

        if ex_mastery is True:
            print("New extended mastery level!")
            time.sleep(3)
            # TODO
            # Refactor
            self.driver.find_element_by_id('cjs-lp-rankup').click()
            # action = webdriver.ActionChains(self.driver)
            # action.move_by_offset(448, 392)
            # action.click().perform()

    def handle_after_fight(self):
        self.bot.wait.for_loading_screen()
        loot = self.bot.wait.for_quest_results_screen()
        if loot is True:
            self.collect_raid_results()
            self.handle_extended_mastery()
            self.handle_new_item_screen()
            self.handle_achievement_screen()
            print(f"Total kills: {self.total_kills}, XP: {self.total_xp}, Pendants: {self.total_pendants}")
            self.bot.wait.for_loot_screen()
            self.bot.press.quest_button_after_fight()
            self.handle_friend_request()
        else:
            self.bot.press.quest_button_after_fight_no_loot()

    def handle_achievement_screen(self):
        achievement = self.bot.popup.achievement()

        if achievement is True:
            print("New achievement!")
            self.bot.press.usual_close()

    def get_new_item_image_url(self):
        parser = bs(self.driver.page_source, features='lxml')
        image_src = parser.find('img', {'class': 'img-newitem'})
        return image_src['src']

    def handle_new_item_screen(self):
        new_item = self.bot.popup.new_item()

        if new_item is True:
            url = self.get_new_item_image_url()
            print(f'New item drop! {url}')
            self.bot.press.usual_ok()
            time.sleep(2)

    def handle_resume_quest_popup(self):
        resume_quest = self.bot.popup.resume_quest()

        if resume_quest is True:
            self.bot.press.usual_cancel()
            time.sleep(1)

    def handle_to_raids(self):
        self.bot.wait.for_loading_screen()
        try:
            self.bot.press.quest_button_main_menu()
            self.handle_resume_quest_popup()
        except selenium_err.exceptions.NoSuchElementException:
            self.handle_resume_quest_popup()
            self.bot.press.raid_button()
            self.bot.press.enter_raid_id()
        else:
            self.bot.press.raid_button()
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
        fight = self.handle_raid_mechanics()
        if fight is False:
            return

        # AFTER RAID HANDLING HERE
        self.handle_after_fight()
