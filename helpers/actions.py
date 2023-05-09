from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .timeout import Timeout

import time


class Action:
    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver
        self._Timeout = Timeout(self._driver)
        self._x_option_list_button_xpath = (
            '//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[4]/select'
        )
        self._x_use_button_xpath = (
            '//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[5]/div'
        )
        self._half_elixir_consumable_list_xpath = (
            '//*[@id="pop"]/div/div[2]/div/div/div[4]/div[2]/select'
        )
        self._half_elixir_consumable_use_xpath = '//*[@id="pop"]/div/div[3]/div[2]'
        self._input_raid_id_class = "frm-battle-key"

    def input_raid_id(self, raid_id):
        elem = self._driver.find_element(By.CLASS_NAME, self._input_raid_id_class)
        elem.clear()
        time.sleep(1)
        elem.send_keys(raid_id)

    def use_potions_or_pills(self, amount, consumable=False, sandbox=False):
        timeout = 2
        expected_behaviour = EC.visibility_of_element_located
        search_by = By.XPATH

        option_list = self._x_option_list_button_xpath
        amount_in_list = f'//*[@id="pop"]/div/div[2]/div/div[2]/div[2]/div[4]/select/option[{amount}]'
        use_button = self._x_use_button_xpath

        if consumable is True:
            option_list = self._half_elixir_consumable_list_xpath
            use_button = self._half_elixir_consumable_use_xpath
            amount_in_list = f'//*[@id="pop"]/div/div[2]/div/div/div[4]/div[2]/select/option[{amount}]'

        if sandbox:
            option_list = '//*[@id="pop"]/div/div[2]/div/div[3]/div[2]/div[4]/select'
            amount_in_list = f'//*[@id="pop"]/div/div[2]/div/div[3]/div[2]/div[4]/select/option[{amount}]'
            use_button = '//*[@id="pop"]/div/div[2]/div/div[3]/div[2]/div[5]/div'

        # Click on the options button
        self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, option_list
        )
        self._driver.find_element(By.XPATH, option_list).click()
        # Pick x amount of pills/potions
        self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, amount_in_list
        )
        self._driver.find_element(By.XPATH, amount_in_list).click()
        # Click 'Use'
        self._bot.wait.for_loading_screen()
        self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, use_button
        )
        self._driver.find_element(By.XPATH, use_button).click()
