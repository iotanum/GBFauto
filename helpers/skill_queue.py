from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

from selenium import common as selenium_err
from selenium.webdriver.common.by import By

import time
import re


class Skills:
    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver
        self._queue = None

    def parse_queue(self, queue):
        ability_to_num = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}

        queue = queue.split(">")
        queue = [step.strip(" ") for step in queue]

        queue_final = {}

        for idx, step in enumerate(queue, 1):
            for character, ability, *rest in step.split():
                print(character, ability, rest)
                queue_final[idx] = {
                    "Character": None,
                    "Ability": None,
                    "Select": None,
                    "FullAuto": False,
                }

                if character == "F":
                    queue_final[idx]["Full Auto"] = True
                    continue

                queue_final[idx]["Character"] = int(character)
                queue_final[idx]["Ability"] = ability_to_num[ability]

                if len(rest) == 1:
                    queue_final[idx]["Select"] = int(rest[0])
                else:
                    queue_final[idx]["Select"] = None

        self.check_queue(queue_final)

        return queue_final

    def check_queue(self, queue):
        max_actions_per_turn = 17

        if len(queue) > max_actions_per_turn:
            raise AttributeError("Too many steps, max is 17 in 1 turn.")
        for index, step in enumerate(list(queue.values())):
            if step["Full Auto"]:
                if index != len(list(queue.values())) - 1:
                    raise AttributeError(
                        "Full Auto can only be used at the end of the queue."
                    )
        for step, action in queue.items():
            char_num = queue[step]["Character"]
            ability_num = queue[step]["Ability"]
            select_num = queue[step]["Select"]

            if char_num != 5 and ability_num > 4:
                raise AttributeError("Character cannot have more than 4 abilities!")
            elif select_num is not None and select_num > 6:
                raise AttributeError(
                    "There cannot be more than 6 teammates in the 'Select Character' screen!"
                )
            elif char_num == 5 and ability_num > 6:
                raise AttributeError("There cannot be more than 6 support summons!")
            elif char_num > 5:
                raise AttributeError(
                    "Please check your queue, number of playables cannot be more than 5"
                )

    def handle_skill_press(self, char_num, ability_num, raids=False):
        self._bot.press.char_skill(char_num, ability_num, raids=raids)

    def handle_char_switching(self, direction=None):
        if direction == "next":
            self._bot.press.next_char()
        else:
            self._bot.press.previous_char()
        time.sleep(0.5)

    def remove_ability_log_element(self):
        try:
            elem = self._driver.find_element(By.CLASS_NAME, "prt-raid-log")
            self._driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", elem
            )
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def remove_backup_request_element(self):
        try:
            popup = self._driver.find_element(By.CLASS_NAME, "txt-raid-assist")
            popup_footer = self._driver.find_element(By.CLASS_NAME, "prt-popup-footer")
            self._driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", popup
            )
            self._driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", popup_footer
            )
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def remove_active_mask_element(self):
        try:
            mask = self._driver.find_element(By.ID, "main-mask")
            self._driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", mask
            )
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def check_for_back_button(self):
        start = time.time()

        while True:
            if time.time() - start > 5:
                break

            parser = bs(self._driver.page_source, features="lxml")

            main_characters_screen = parser.find_all(
                "div",
                {"class": "prt-command-top", "style": re.compile("display: none;")},
            )
            back_button_yatima = parser.find(
                "div", class_=f"btn-command-back display-off display-on"
            )
            back_button_normal = parser.find(
                "div", class_=f"btn-command-back display-on"
            )

            if not main_characters_screen:
                break

            if back_button_normal or back_button_yatima:
                return True

    def check_if_skill_is_disabled(self, chara_num, skill_num):
        start = time.time()

        charas = ss("div", attrs={"class": "prt-command"})

        while True:
            if time.time() - start > 2:
                break

            parser = bs(self._driver.page_source, features="lxml", parse_only=charas)
            chara = parser.find(
                "div",
                attrs={"class": re.compile(f"prt-command-chara chara{chara_num}")},
            )

            if parser:
                available_skill = parser.find_all(
                    "div", {"class": "lis-ability btn-ability-available"}
                )

                if "turn-disable" in chara["class"]:
                    print("blocked chara")
                    return True

                abilities = chara.find("div", {"class": "prt-ability-list"})
                abilities = abilities.findAll(
                    "div", {"class": re.compile("lis-ability btn-ability")}
                )
                for idx, ability in enumerate(abilities, 1):
                    if skill_num == idx and "ability-disable" in ability["class"]:
                        print("blocked skill")
                        return True

                if available_skill:
                    print("available skill, all good")
                    return False

            time.sleep(0.1)

    def do_queue(self, queue_from_config, raids=False):
        self.remove_ability_log_element()
        self.remove_backup_request_element()
        self.remove_active_mask_element()

        # Handle empty queue string in config
        try:
            self._queue = self.parse_queue(queue_from_config)
        except ValueError:
            self._queue = {1: {"Character": 7, "Ability": 8}}
            pass
        summon_was_used = False
        current_char_num = None
        executed_step = []

        for step, action in self._queue.items():
            print(step, action, "queue step action")
            # Try/Except in case of fight ending while queueing skills
            try:
                char_num = self._queue[step]["Character"]
                ability_num = self._queue[step]["Ability"]
                select_party_member = self._queue[step]["Select"]
                full_auto = self._queue[step]["FullAuto"]

                # If full auto is used, then break the loop
                if full_auto:
                    self._bot.press.auto_attack()
                    break

                # Instantly break if queue in config is empty
                if char_num == 7:
                    break
                # Click on a first character in the queue to open up it's abilities 'menu'
                if (
                    step == 1
                    and char_num != 5
                    or summon_was_used is True
                    and char_num != 5
                ):
                    print(1)
                    self._bot.press.char_to_start_queue(char_num)
                    if not self.check_if_skill_is_disabled(char_num, ability_num):
                        self.handle_skill_press(char_num, ability_num, raids)

                        if select_party_member:
                            time.sleep(0.15)
                            self._bot.press.select_part_member(select_party_member)
                            # Fuckery with select_party_member setup that I have, this will be fine I guess
                        executed_step = [step, action]

                    current_char_num = char_num
                    # Set this variable to false so it wouldn't spam char_to_start_queue
                    # when summon was/is used
                    if summon_was_used is True:
                        summon_was_used = False
                # Check if action to take in queue is for a character
                if char_num <= 4:
                    print(2)
                    if char_num != current_char_num:
                        print(3)
                        num_of_actions_to_take = current_char_num - char_num
                        # Convert possible negative number to positive
                        num_of_actions_to_take = max(
                            num_of_actions_to_take, -num_of_actions_to_take
                        )
                        print(current_char_num, char_num, "current, char")
                        if current_char_num == 4 and char_num == 1:
                            print("moving forward")
                            self.handle_char_switching(direction="next")
                            time.sleep(0.15)
                        elif current_char_num == 1 and char_num == 4:
                            print("moving backward")
                            self.handle_char_switching(direction="previous")
                            time.sleep(0.15)
                        elif current_char_num < char_num:
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction="next")
                                time.sleep(0.15)
                        else:
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction="previous")
                                time.sleep(0.15)
                    current_char_num = char_num
                    if (
                        not self.check_if_skill_is_disabled(char_num, ability_num)
                        and [step, action] != executed_step
                    ):
                        print(4)
                        self.handle_skill_press(char_num, ability_num, raids)
                        # This is for 'Select party member' type of ability
                        if select_party_member:
                            time.sleep(0.3)
                            self._bot.press.select_part_member(select_party_member)
                # if char_num is 5, then it means it's a support summon
                else:
                    print(5)
                    # Exit character skill selection 'window'
                    if step > 1 and self._queue[step - 1]["Character"] != 5:
                        self._bot.press.back()
                    # If MC is fked - no summon usage
                    # if not self.check_if_skill_is_disabled(1, 1):
                    actions_for_summon = [
                        self._bot.press.summon_card,
                        self._bot.press.summon_num,
                        self._bot.press.confirm_summon_fight,
                        self._bot.press.back,
                    ]
                    for idx, summ_action in enumerate(actions_for_summon, 1):
                        # second step is choosing which summon
                        if idx == 2:
                            summ_action(ability_num, raids)
                        elif idx == 4:
                            if self.check_for_back_button():
                                summ_action()
                        else:
                            summ_action(raids)
                        time.sleep(0.35)
                    summon_was_used = True
            except (
                selenium_err.exceptions.ElementNotVisibleException,
                selenium_err.exceptions.WebDriverException,
            ) as e:
                print(f"Broke on {step} step.")
                print(action)
                print(e)
                break
