from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

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
        self.bot.raid_battle = False
        self.coop = False
        self.sandbox = False
        self.quest_url = None
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
        while True:
            raid_filter_num = self.get_raid_filter()
            if raid_filter_num:
                print(f"Is 'Filter {raid_filter_num}' correct?")
                answer = input("Y/N: ")
                validated = self.validate_raid_filter_input(answer)
                if not validated:
                    print("Please choose between Y or N.")
                if validated and answer.lower() == "y":
                    print(f"Locked to 'Filter {raid_filter_num}'.")
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
        filter_uri_contains = "quest/assist/search/assist_list"
        request_uri = self.bot.game_requests.find_generic_request(
            filter_uri_contains, return_uri=True
        )

        if request_uri:
            # let's take the last element of this list
            # since I just need the latest info from gathering requests
            # during the duration of the req/resp scan
            raid_filter_num = request_uri.split("assist_list/")
            raid_filter_num = raid_filter_num[-1].split("/")[0]

            return raid_filter_num

    def remove_battle_scene_element(self):
        try:
            elem = self.driver.find_element(By.CLASS_NAME, "btn-scene-next")
            self.driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", elem
            )
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def enemy_hps(self):
        strainer = ss("div", attrs={"class": "prt-targeting-area main-tap-area"})
        parser = bs(self.driver.page_source, "lxml", parse_only=strainer)

        mob_hps = parser.find_all("span", "txt-gauge-value")
        mob_hps = [int(hp.text) for hp in mob_hps]

        return mob_hps

    def finish_fight(self, initial_info):
        # remove the battle scene/advice element from the fight, less clutter
        self.remove_battle_scene_element()

        printed_battle = False
        battle = initial_info
        while True:
            queues = self.bot.handle.find_all_queues()
            queues = self.bot.handle.handle_queue(queues, battle)
            if queues is not None:
                next_turn_queue = battle["turn"] + 1 in queues[battle["battle"]]
                this_turn_queue = battle["turn"] in queues[battle["battle"]]
            else:
                next_turn_queue = None
                this_turn_queue = None

            if not printed_battle:
                print(f"Fight #{battle['battle']}.")
                printed_battle = True

            try:
                if queues and this_turn_queue:
                    self.bot.press.attack_button()

                boss_killed = self.bot.handle.wait_for_next_turn(battle)

                if self.bot.handle.results_screen():
                    return True

                # print(
                #     battle["battle"] == battle["total_battles"],
                #     "check for battle equal",
                # )

                # we only want to refresh if there's no more parts to the battle
                # or wer are in the final battle
                if (battle["battle"] == battle["total_battles"]) or battle[
                    "total_battles"
                ] == 1:
                    self.bot.handle.refresh_page()

                if boss_killed:
                    print("Everyone died.")
                    return True

                # after refreshing get the status of a battle
                if not next_turn_queue and not self.bot.handle.results_screen():
                    if not self.bot.auto_button_on:
                        print("enabling auto in loading screen")
                        self.bot.handle.enable_auto_in_loading_screen()

                battle = self.bot.battle.get_battle_start_info()

                if battle is None:
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

    def count_quest_fight_parts(self):
        parser = bs(self.driver.page_source, "lxml")

        progress_bar = parser.find("div", {"class": "prt-position"})
        quest_parts = progress_bar.find_all("div", {"class": ["lis-spot"]})

        # If list is empty - it's a one fight quest
        if not quest_parts:
            quest_parts = [1]

        return len(quest_parts)

    def get_start_button_chapter_id(self):
        parser = bs(self.driver.page_source, "lxml")

        ready_btn = parser.find("div", class_="btn-quest-start multi se-quest-start")
        chapter_id = ready_btn["data-chapter-id"]

        return chapter_id

    def handle_fight(self):
        load_dotenv("config.env", override=True)
        queue = os.getenv("QUEUE_1_1")

        # Wait for a start.json request from the game to get info
        # on the state of a battle when starting a battle
        initial_battle_info = self.bot.battle.get_battle_start_info()
        if not initial_battle_info:
            return

        if not queue:
            self.bot.handle.enable_auto_in_loading_screen()

        if not self.bot.auto_button_on:
            self.bot.handle.enable_auto_in_loading_screen()

        if queue:
            self.bot.handle.pre_fight_screens()
            self.bot.handle.wait_before_fight(
                fight_start=True, gw=True if not queue else False
            )

        fight_ended = self.finish_fight(initial_battle_info)

        # Reset quest_on_repeat states
        self.bot.refreshed = False
        # Reset only for raid-type of quests, not multi-battles ones
        if not initial_battle_info["total_battles"] > 1:
            self.bot.auto_button_on = False

        # Skip animations after completing the quest
        if fight_ended:
            # Also check if after refreshing the page we're still in a fight
            # or quest contains more than 1 fight
            if "result" not in self.driver.current_url:
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

        self.bot.raid_battle = False
        self.bot.auto_button_on = False

        if "#quest/supporter" not in str(self.driver.current_url):
            self.bot.handle.not_enough_of_x(ep=self.bot.new_raids)

    def go_to_quest(self):
        attempts = 0

        while True:
            if self.driver.current_url == self.quest_url:
                break

            else:
                self.driver.execute_script(f"window.location.href = '{self.quest_url}'")
                time.sleep(0.5)
                attempts += 1

                # Avoid constant location change spam
                if attempts > 1:
                    time.sleep(3)

    def repeatable_quest(self):
        while True:
            self.do_repeatable_quest()

    def refresh_raid_filter(self):
        if self.bot.handle.is_refresh_raid_filter_available():
            self.bot.press.raid_filter_refresh()

    def get_most_suitable_raid(self):
        raids = self.bot.handle.get_raid_filter_raids()
        # if raids come back empty -> just return
        if not raids:
            return

        raids = raids.find_all("div", {"class": "prt-raid-info"})
        suitable_raid_ele = raids[0]
        suitable_raid_idx = None

        for idx, raid in enumerate(raids, 1):
            hp_bar = raid.find("div", {"class": "prt-raid-gauge-inner"})
            hp_ele = str(hp_bar["style"])

            suitable_raid_hp_bar = suitable_raid_ele.find(
                "div", {"class": "prt-raid-gauge-inner"}
            )
            suitable_raid_hp = re.findall(r"\d+", str(suitable_raid_hp_bar["style"]))[0]
            hp = re.findall(r"\d+", hp_ele)[0]

            if suitable_raid_hp <= hp:
                suitable_raid_ele = raid
                suitable_raid_idx = idx

        return suitable_raid_idx

    def pick_raid(self, raid_num):
        self.bot.press.pick_raid(raid_num)

    def check_pre_fight_popups(self):
        popups = self.bot.handle.pre_fight_popups()
        if popups:
            return True

    def handle_new_raids_join(self):
        while True:
            raid_num = self.get_most_suitable_raid()

            if raid_num:
                self.pick_raid(raid_num)
                self.bot.handle.not_enough_of_x(ep=self.bot.new_raids)
                success = self.bot.handle.pre_fight_support_summons()
                if not success:
                    self.go_to_quest()
                    continue
                return success

            self.refresh_raid_filter()

            time.sleep(0.5)

    def handle_pre_fight(self):
        modes = [self.coop, self.sandbox, self.bot.new_raids]
        simple_repeatable = not any(modes)
        if simple_repeatable:
            self.bot.handle.pre_fight_support_summons()
        elif self.sandbox is True:
            self.bot.handle.sandbox_summon_pick()
        elif self.bot.new_raids is True:
            self.handle_new_raids_join()
        else:
            # Wait until player chooses it's COOP team.
            self.wait_for_coop_prep()

            # And now press 'Ready' to enter the fight.
            chapter_id = self.get_start_button_chapter_id()
            self.bot.press.by_chapter_id(chapter_id)

        action = self.check_pre_fight_popups()
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
