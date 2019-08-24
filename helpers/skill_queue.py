from selenium import common as selenium_err

import time


class Skills:
    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver
        self._queue = None
        self._queue_from_config = None

    def parse_queue(self, queue):
        ability_to_num = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

        queue = queue.split(">")
        queue = [step.strip(' ') for step in queue]

        queue_final = {}

        for idx, step in enumerate(queue, 1):
            for character, ability, *rest in step.split():
                queue_final[idx] = {'Character': None,
                                    'Ability': None,
                                    'Select': None}

                queue_final[idx]['Character'] = int(character)
                queue_final[idx]['Ability'] = ability_to_num[ability]

                if len(rest) == 1:
                    queue_final[idx]['Select'] = int(rest[0])
                else:
                    queue_final[idx]['Select'] = None

        self.check_queue(queue_final)

        return queue_final

    def check_queue(self, queue):
        max_actions_per_turn = 17

        if len(queue) > max_actions_per_turn:
            raise AttributeError('Too many steps, max is 17 in 1 turn.')
        for step, action in queue.items():
            char_num = queue[step]['Character']
            ability_num = queue[step]['Ability']
            select_num = queue[step]['Select']

            if char_num != 5 and ability_num > 4:
                raise AttributeError('Character cannot have more than 4 abilities!')
            elif select_num is not None and select_num > 6:
                raise AttributeError("There cannot be more than 6 teammates in the 'Select Character' screen!")
            elif char_num == 5 and ability_num > 6:
                raise AttributeError('There cannot be more than 6 support summons!')
            elif char_num > 5:
                raise AttributeError('Please check your queue, number of playables cannot be more than 5')

    def handle_skill_press(self, char_num, ability_num):
        self._bot.press.char_skill(char_num, ability_num)
        # self.handle_ability_log_popup()

    def handle_char_switching(self, direction=None):
        if direction is 'next':
            self._bot.press.next_char()
        else:
            self._bot.press.previous_char()
        time.sleep(0.5)
        # self.handle_ability_log_popup()

    def handle_ability_log_popup(self):
        popup = self._bot.popup.log_ability()
        if popup is True:
            self._bot.press.log_ability()

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

    def remove_active_mask_element(self):
        try:
            mask = self._driver.find_element_by_id('main-mask')
            self._driver.execute_script('arguments[0].parentNode.removeChild(arguments[0]);', mask)
        except selenium_err.exceptions.NoSuchElementException:
            pass

    def do_queue(self, queue_from_config):
        self.remove_ability_log_element()
        self.remove_backup_request_element()
        self.remove_active_mask_element()

        # Handle empty queue string in config
        try:
            self._queue = self.parse_queue(queue_from_config)
        except ValueError:
            self._queue = {1: {'Character': 7, 'Ability': 8}}
            pass
        summon_was_used = False
        current_char_num = None

        for step, action in self._queue.items():
            # Try/Except in case of fight ending while queueing skills
            try:
                char_num = self._queue[step]['Character']
                ability_num = self._queue[step]['Ability']
                select_party_member = self._queue[step]['Select']
                # Instantly break if queue in config is empty
                if char_num == 7:
                    break
                # Click on a first character in the queue to open up it's abilities 'menu'
                if step == 1 and char_num != 5 or summon_was_used is True:
                    self._bot.press.char_to_start_queue(char_num)
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
                        if current_char_num < char_num:
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction='next')
                                time.sleep(0.15)
                        else:
                            for _ in range(num_of_actions_to_take):
                                self.handle_char_switching(direction='previous')
                                time.sleep(0.15)
                    current_char_num = char_num
                    self.handle_skill_press(char_num, ability_num)
                    time.sleep(0.15)
                    # This is for 'Select party member' type of ability
                    if select_party_member:
                        self._bot.press.select_part_member(select_party_member)
                        time.sleep(0.15)
                # if char_num is 5, then it means it's a support summon
                else:
                    # Pressing support summon in a middle of a queue requires
                    # pressing 'back' button in the left top corner
                    if step > 1:
                        self._bot.press.back()
                    actions_for_summon = [self._bot.press.summon_card,
                                          self._bot.press.summon_num,
                                          self._bot.press.confirm_summon_fight,
                                          self._bot.press.back]
                    for idx, summ_action in enumerate(actions_for_summon, 1):
                        # second step is choosing which summon
                        if idx == 2:
                            summ_action(ability_num)
                        else:
                            summ_action()
                        time.sleep(0.35)
                    summon_was_used = True
            except (selenium_err.exceptions.ElementNotVisibleException, selenium_err.exceptions.WebDriverException) as e:
                print(f"Broke on {step} step.")
                print(F"Reason: {e}")
                break
