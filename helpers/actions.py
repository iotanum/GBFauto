from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .timeout import Timeout

import time


class Action:
    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver
        self._Timeout = Timeout(self._driver)
        self._x_option_list_button_xpath = '//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[4]/select'
        self._x_use_button_xpath = '//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[5]/div'
        self._input_raid_id_class = "frm-battle-key"

    def input_raid_id(self, raid_id):
        elem = self._driver.find_element_by_class_name(self._input_raid_id_class)
        elem.clear()
        time.sleep(1)
        elem.send_keys(raid_id)

    def use_potions_or_pills(self, amount):
        timeout = 2
        expected_behaviour = EC.visibility_of_element_located
        search_by = By.XPATH
        ep_amount_option_xpath = f'//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[4]/select/option[{amount}]'

        # Click on the options button
        self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, self._x_option_list_button_xpath)
        self._driver.find_element_by_xpath(self._x_option_list_button_xpath).click()
        # Pick x amount of pills/potions
        self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, ep_amount_option_xpath)
        self._driver.find_element_by_xpath(ep_amount_option_xpath).click()
        # Click 'Use'
        self._bot.wait.for_loading_screen()
        self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, self._x_use_button_xpath)
        self._driver.find_element_by_xpath(self._x_use_button_xpath).click()
