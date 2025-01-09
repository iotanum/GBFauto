from bs4 import BeautifulSoup as bs

import os
import time
import re

from selenium import common as selenium_err
from selenium.webdriver.common.by import By
from dotenv import load_dotenv


class QuestOnRepeat:
    def __init__(self, game_handler):
        self.bot = game_handler
        self.driver = game_handler.driver
        self.repeat = False
        self.coop = False
        self.sandbox = False
        self.quest_url = None
        self.event_raids = False
        # Some solo/raids that can be hosted are not always
        # repeatable, aka doesn't have "play again" button
        self.is_repeatable = False

    def wait_for_repeatable_quest(self):
        if not self.quest_url:
            print("\nWaiting for you to enter a repeatable quest...")

        # wait until you join a specific fight, set correct variables for given fight
        while True:
            url = str(self.driver.current_url)

            # normal fights (GW, Events, Missions)
            if "#quest/supporter" in url:
                if not self.quest_url:
                    self.quest_url = url
                    print("Locked in on this quest.")
                break

            # coop fights
            if "#coopraid/room/" in url:
                print("Locked on this CO-OP quest.")
                self.quest_url = url
                self.coop = True
                break

            # arcanum sandbox fights
            if "#replicard/supporter" in url:
                print("Locked on this Sandbox quest.")
                self.quest_url = url
                self.sandbox = True
                break

            # new raid thingy
            if "#quest/assist" in url:
                print("Locked to raids, please choose filter option.")
                self.choose_raid_filter()
                self.quest_url = url
                self.bot.new_raids = True
                break

            time.sleep(0.2)

    def choose_raid_filter(self):
        self.bot.handle.set_req_time()
        while True:
            raid_filter_num = self.get_raid_filter()
            event_filter_num = self.get_event_filter()

            if raid_filter_num or event_filter_num:
                print(f"Is filter '{raid_filter_num}' correct?")
                answer = input("Y/N: ")
                validated = self.validate_raid_filter_input(answer)
                if not validated:
                    print("Please choose between Y or N.")
                if validated and answer.lower() == "y":
                    print(f"Locked to filter '{raid_filter_num}'.")
                    break

    def validate_raid_filter_input(self, answer: str):
        possible_answers = ["y", "n"]
        if not answer.isalpha():
            return False

        if len(answer) > 1:
            return False

        if answer.lower() not in possible_answers:
            return False

        return True

    def get_raid_filter(self):
        req = self.bot.battle.find_raid_assist_response()
        if req:
            req = req[0]
            # let's take the last element of this list
            # since I just need the latest info from gathering requests
            # during the duration of the req/resp scan
            raid_filter_num = req["uri"].split("assist_list/")
            raid_filter_num = raid_filter_num[-1].split("/")[0]

            return raid_filter_num

    def get_event_filter(self):
        req = self.bot.battle.find_event_assist_response()
        if req:
            req = req[0]

            raid_filter_num = req["uri"].split("assist_list/")
            raid_filter_num = raid_filter_num[-1].split("?")[0]

            if raid_filter_num == '1':
                self.event_raids = True
                return 'Events'

    def remove_battle_scene_element(self):
        try:
            elem = self.driver.find_element(By.CLASS_NAME, "btn-scene-next")
            self.driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", elem
            )
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def finish_fight(self):
        # remove the battle scene/advice element from the fight, less clutter
        self.remove_battle_scene_element()

        while True:
            queues = self.bot.handle.find_all_queues()
            queues = self.bot.handle.handle_queue(queues)
            if queues is not None:
                next_turn_queue = (
                    self.bot.fight["turn"] + 1 in queues[self.bot.fight["battle"]]
                )
                this_turn_queue = (
                    self.bot.fight["turn"] in queues[self.bot.fight["battle"]]
                )
            else:
                next_turn_queue = None
                this_turn_queue = None

            print(f"Fight #{self.bot.fight['battle']}.")

            try:
                if queues and this_turn_queue:
                    # check if FA was in queue, don't press attack button
                    if (
                        "fa"
                        not in queues[self.bot.fight["battle"]][
                            self.bot.fight["turn"]
                        ].lower()
                    ):
                        self.bot.press.attack_button()

                boss_killed = self.bot.handle.wait_for_next_turn()
                if self.bot.handle.results_screen():
                    return True

                # we only want to refresh if there's no more parts to the battle
                # or wer are in the final battle
                if (
                    self.bot.fight["battle"] == self.bot.fight["total_battles"]
                ) or self.bot.fight["total_battles"] == 1:
                    self.bot.handle.refresh_page()

                if boss_killed:
                    print("Everyone died.")
                    return True

                # after refreshing get the status of a battle
                if not next_turn_queue and not self.bot.handle.results_screen():
                    if not self.bot.auto_button_on:
                        print("enabling auto in loading screen")
                        self.bot.handle.enable_auto_in_loading_screen()

                self.bot.fight = self.bot.battle.handle_battle_start_info()

                if self.bot.fight is None:
                    return

                if next_turn_queue:
                    self.bot.handle.wait_before_fight(fight_start=True)

                    # Remove the element again since we refreshed the page
                    self.remove_battle_scene_element()
            except (
                selenium_err.exceptions.NoSuchElementException,
                selenium_err.exceptions.WebDriverException,
            ):
                pass

    def get_start_button_chapter_id(self):
        parser = bs(self.driver.page_source, "lxml")

        ready_btn = parser.find("div", class_="btn-quest-start multi se-quest-start")
        chapter_id = ready_btn["data-chapter-id"]

        return chapter_id

    def handle_fight(self):
        load_dotenv("config.env", override=True)
        queue = os.getenv("QUEUE_1_1")

        if not self.bot.fight:
            return

        if not queue:
            self.bot.handle.enable_auto_in_loading_screen()

        if queue:
            self.bot.handle.pre_fight_screens()
            self.bot.handle.wait_before_fight(
                fight_start=True, gw=True if not queue else False
            )

        fight_ended = self.finish_fight()

        # Reset quest_on_repeat states
        self.bot.refreshed = False
        self.bot.auto_button_on = False

        # Skip animations after completing the quest
        if fight_ended:
            # Also check if after refreshing the page we're still in a fight
            # or quest contains more than 1 fight
            if not self.bot.handle.results_screen():
                # if not self.num_of_fights > 1:
                self.bot.handle.refresh_page()

    def convert_seconds_to_hms_format(self):
        seconds = round(self.bot.run_time(), 2)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return int(round(hours, 2)), int(round(minutes, 2)), int(round(seconds, 2))

    def determine_type_of_quest(self, gw=False):
        if self.coop is not True and gw is False:
            # Check if a quest is not repeatable only if it wasn't done
            # before and if total fights is 1 and lower
            if not self.is_repeatable and self.bot.total_fights <= 1:
                self.is_repeatable = self.bot.press.play_again_quest()

            # If quest is repeatable - continue on
            if self.is_repeatable and self.bot.total_fights >= 2:
                self.bot.press.play_again_quest()
            # If not repeatable (ex.: hosting gw bosses)
            # press event home (triggers, IF, nightmare battle popup)s4
            elif not self.is_repeatable:
                self.bot.press.usual_event_home()
        else:
            return

    def check_if_gw(self):
        load_dotenv("config.env", override=True)
        gw = os.getenv("GW")

        if gw == "1":
            return True
        return False

    def handle_after_fight(self):
        # Used to optimize GW runs
        # if this is true it skips some popups/screens (just like bookmarking)
        gw = self.check_if_gw()

        self.bot.wait.for_loading_screen()

        self.bot.handle.after_fight_popups(kill=True, gw=gw)

        hours, minutes, seconds = self.convert_seconds_to_hms_format()
        if self.bot.total_fights == 0:
            self.bot.total_fights += 1

        avg_time_per_quest = round(self.bot.run_time() / self.bot.total_fights, 2)
        print(
            f"Total fights: {self.bot.total_fights}, EXP: {self.bot.total_exp}, Rank points: {self.bot.total_ranks}\n"
            f"Running for {hours}h:{minutes}min:{seconds}s, "
            f"Average time per quest: {avg_time_per_quest}s"
        )

        self.determine_type_of_quest(gw=gw)
        temp_nightmare_state = False

        if not gw:
            nightmare_battle = self.bot.handle.after_fight_popups()
            if nightmare_battle is True:
                self.repeat = False
                # After nightmare battle quest is *obviously*
                # not repeatable, so set a temp state of it to false
                if self.is_repeatable:
                    temp_nightmare_state = True
                    self.is_repeatable = False
                # self.bot.need_ap = False
        else:
            nightmare_battle = False
            self.is_repeatable = False

        # Use AP (if needed) and navigate to quest if only
        # the quest is not repeatable
        if not self.is_repeatable:
            # If there was a temp false state for repeatable quest
            # after nightmare battle - set it back to true
            if nightmare_battle and temp_nightmare_state:
                self.is_repeatable = True

            if (
                self.bot.need_ap
                and self.sandbox is False
                and self.bot.new_raids is False
            ):
                self.bot.handle.use_ap_for_non_repeatables(ep=self.bot.new_raids)

            # Navigate back to original quest
            self.go_to_quest()

        self.bot.auto_button_on = False

        if "#quest/supporter" not in str(self.driver.current_url):
            self.bot.handle.not_enough_of_x(ep=self.bot.new_raids)

    def go_to_quest(self):
        print("Going back to quest.", self.driver.current_url)
        self.driver.execute_script("return document.readyState == 'complete';")
        print("Page is loaded? :D", self.driver.current_url)
        self.driver.get(self.quest_url)
        print("Waiting for quest to load.", self.driver.current_url)

    def repeatable_quest(self):
        while True:
            self.do_repeatable_quest()

    def refresh_raid_filter(self):
        if not self.event_raids:
            if self.bot.handle.is_refresh_raid_filter_available():
                self.bot.press.raid_filter_refresh()
                return True
        else:
            if self.bot.handle.is_refresh_event_filter_available():
                self.bot.press.event_filter_refresh()
                return True

    def get_most_suitable_raid(self):
        raids = self.bot.handle.get_filter_raids(event_filter=self.event_raids)
        # if raids come back empty -> just return
        if not raids:
            return

        load_dotenv("config.env", override=True)
        lower_hp_limit = int(os.getenv("RAIDS_LOWER_HP_LIMIT", 35))
        higher_hp_limit = int(os.getenv("RAIDS_UPPER_HP_LIMIT", 100))

        raids = raids.find_all("div", {"class": "prt-raid-info"})
        suitable_raid_ele = raids[0]
        suitable_raid_idx = None

        for idx, raid in enumerate(raids, 1):
            hp_bar = raid.find("div", {"class": "prt-raid-gauge-inner"})
            hp_ele = str(hp_bar["style"])

            suitable_raid_hp_bar = suitable_raid_ele.find(
                "div", {"class": "prt-raid-gauge-inner"}
            )
            suitable_raid_hp = int(
                re.findall(r"\d+", str(suitable_raid_hp_bar["style"]))[0]
            )
            hp = int(re.findall(r"\d+", hp_ele)[0])

            if suitable_raid_hp <= hp <= higher_hp_limit and hp >= lower_hp_limit:
                suitable_raid_ele = raid
                suitable_raid_idx = idx

        return suitable_raid_idx

    def pick_raid(self, raid_num):
        try:
            self.bot.press.pick_raid(raid_num, events_filter=self.event_raids)
        except selenium_err.exceptions.ElementClickInterceptedException:
            return False

    def post_summon_checks(self):
        self.bot.handle.set_req_time()
        while True:
            if self.bot.handle.results_screen():
                return True

            reqs = self.bot.battle.find_after_confirm_response()
            if reqs:
                for req in reqs:
                    if "start.json" in req["uri"]:
                        self.bot.fight = self.bot.battle.check_battle_info(req)
                        if self.bot.fight:
                            return

                    action = self.bot.handle.check_if_action_is_needed(req)
                    print(action, "action")
                    if action:
                        return True

    def handle_new_raids_join(self):
        refresh_timeout = 60
        start_refresh = time.time()

        while True:
            if time.time() - start_refresh > refresh_timeout:
                self.bot.handle.refresh_page()
                start_refresh = time.time()

            raid_num = self.get_most_suitable_raid()

            if raid_num:
                self.pick_raid(raid_num)
                self.bot.handle.not_enough_of_x(ep=self.bot.new_raids)
                success = self.bot.handle.pre_fight_support_summons()
                if not success:
                    self.go_to_quest()
                    continue
                print("handle_new_raids_join")
                return success

            refreshed = self.refresh_raid_filter()
            if refreshed:
                start_refresh = time.time()
            time.sleep(0.1)

    def handle_pre_fight(self):
        modes = [self.coop, self.sandbox, self.bot.new_raids]
        if not any(modes):
            self.bot.handle.pre_fight_support_summons()
        elif self.sandbox is True:
            self.bot.handle.sandbox_summon_pick()
        elif self.bot.new_raids is True:
            self.handle_new_raids_join()
        else:
            # Wait until player chooses its COOP team.
            self.wait_for_coop_prep()

            # And now press 'Ready' to enter the fight.
            chapter_id = self.get_start_button_chapter_id()
            self.bot.press.by_chapter_id(chapter_id)

        action = self.post_summon_checks()
        if action:
            self.go_to_quest()
            self.handle_pre_fight()

    def wait_for_coop_prep(self):
        found_room = False
        already_in_coop_party = False

        while True:
            parser = bs(self.driver.page_source, "lxml")

            # First need to wait until the COOP room page has finished loading.
            if found_room is False:
                try:
                    coop_room_loaded = parser.find(
                        "div", {"class": "txt-count-down"}
                    ).text
                    found_room = True
                except AttributeError:
                    coop_room_loaded = ""

            if found_room is True or "Closes" in coop_room_loaded:
                # Check if party is already picked.
                party_ready = parser.find("div", {"class": "txt-guide"}).text

                if "Start" in party_ready:
                    print("Starting CO-OP quest.")
                    break
                else:
                    if already_in_coop_party is False:
                        print("Waiting until you pick your team for CO-OP.")
                        already_in_coop_party = True
                        found_room = False

                        previous_url = self.driver.current_url
                        picked = False

                        # please don't judge
                        while True:
                            current_url = self.driver.current_url

                            if current_url != previous_url:
                                picked = True

                            if "#coopraid/room" in current_url and picked is True:
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
