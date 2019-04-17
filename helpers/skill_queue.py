from selenium import common as selenium_err

import sys
import time
import traceback

class Skills:
    def __init__(self, game_obj, buttons, popups):
        self._driver = game_obj.driver
        self._Press = buttons
        self._Popup = popups
        self._queue = None
        self._queue_from_config = None

    def parse_queue(self, queue):
        char_to_num = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
        queue_final = {}
        queue = queue.split(">")
        queue = [step.strip(' ') for step in queue]
        queue = [{'Character': int(step[:-1]), 'Ability': step[1:]} for step in queue]

        for idx, step in enumerate(queue, 1):
            queue_final[idx] = step
            ability_char = queue_final[idx]['Ability']
            queue_final[idx]['Ability'] = char_to_num[ability_char.lower()]
        self.check_queue(queue_final)
        return queue_final

    def check_queue(self, queue):
        max_actions_per_turn = 17

        if len(queue) > max_actions_per_turn:
            sys.exit('Too many steps, max is 17 in 1 turn.')
        for step, action in queue.items():
            char_num = queue[step]['Character']
            ability_num = queue[step]['Ability']
            if char_num != 5 and ability_num > 4:
                sys.exit('Character cannot have more than 4 abilities!')
            elif char_num == 5 and ability_num > 6:
                sys.exit('There cannot be more than 6 support summons!')
            elif char_num > 5:
                sys.exit('Please check your queue, number of playables cannot be more than 5')

    def handle_skill_press(self, char_num, ability_num):
        self._Press.char_skill(char_num, ability_num)
        # self.handle_ability_log_popup()

    def handle_char_switching(self, direction=None):
        if direction is 'next':
            self._Press.next_char()
        else:
            self._Press.previous_char()
        time.sleep(0.5)
        # self.handle_ability_log_popup()

    def handle_ability_log_popup(self):
        popup = self._Popup.log_ability()
        if popup is True:
            self._Press.log_ability()
            print("Clicked log ability")

    def remove_ability_log_element(self):
        try:
            elem = self._driver.find_element_by_class_name('prt-raid-log')
            self._driver.execute_script("arguments[0].parentNode.removeChild(arguments[0]);", elem)
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def remove_backup_request_element(self):
        try:
            popup = self._driver.find_element_by_class_name('txt-raid-assist')
            popup_footer = self._driver.find_element_by_class_name('prt-popup-footer')
            self._driver.execute_script('arguments[0].parentNode.removeChild(arguments[0]);', popup)
            self._driver.execute_script('arguments[0].parentNode.removeChild(arguments[0]);', popup_footer)
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def do_queue(self, queue_from_config):
        self.remove_ability_log_element()
        self.remove_backup_request_element()

        self._queue = self.parse_queue(queue_from_config)
        summon_was_used = False
        current_char_num = None

        for step, action in self._queue.items():
            # Try/Except in case of fight ending while queueing skills
            try:
                char_num = self._queue[step]['Character']
                ability_num = self._queue[step]['Ability']
                print('Running', step, char_num, ability_num)
                # Click on a first character in the queue to open up it's abilities 'menu'
                if step == 1 and char_num != 5 or summon_was_used is True:
                    print('starter char tiem!')
                    self._Press.char_to_start_queue(char_num)
                    self.handle_skill_press(char_num, ability_num)
                    current_char_num = char_num
                    # Set this variable to false so it wouldn't spam char_to_start_queue
                    # when summon was/is used
                    if summon_was_used is True:
                        summon_was_used = False
                # Check if action to take in queue is for a character
                if char_num <= 4:
                    if char_num != current_char_num:
                        num_of_actions_to_take = current_char_num - char_num
                        # Convert possible negative number to positive
                        num_of_actions_to_take = max(num_of_actions_to_take, -num_of_actions_to_take)
                        print("char num != current_char_num", num_of_actions_to_take)
                        if current_char_num < char_num:
                            print('Moving to next char')
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction='next')
                                time.sleep(0.15)
                        else:
                            print("moving to previous char")
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction='previous')
                                time.sleep(0.15)
                    current_char_num = char_num
                    self.handle_skill_press(char_num, ability_num)
                    time.sleep(0.15)
                # if char_num is 5, then it means it's a support summon
                else:
                    # Skip pressing 'back' button if support summon is your starter 'char'
                    if summon_was_used is True:
                        self._Press.back()
                    time.sleep(0.2)
                    self._Press.summon_card()
                    time.sleep(0.3)
                    self._Press.summon_num(ability_num)
                    time.sleep(0.3)
                    self._Press.confirm_summon_fight()
                    time.sleep(0.3)
                    summon_was_used = True
            except (selenium_err.exceptions.ElementNotVisibleException, selenium_err.exceptions.WebDriverException) as e:
                break
