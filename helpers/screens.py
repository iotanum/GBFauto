from bs4 import BeautifulSoup as bs

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .timeout import Timeout

import time
import re


class Wait:

    """
    A class for 'waiting' and/or handling various screens.
    Playing around with these methods could get the result *you* need,
    since selenium is all about waiting and THEN doing.

    :returns
        :bool if screen has appeared/disappeared.
    """

    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver
        self._Timeout = Timeout(self._driver)
        self._loading_screen_xpath_end = "//div[@id='loading'][@style='display: none;']"
        self._loading_screen_xpath_start = (
            "//div[@id='loading'][@style='display: block;']"
        )

    # Main method used by all other methods
    def _wait_for_screen(self, timeout, expected_behaviour, search_by, element_name):
        screen = self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, element_name
        )
        # print(screen, element_name, "+++")
        return screen

    def for_loading_screen(self, full=False):
        # use with caution, only in methods that are triggered *AFTER* loading screen
        timeout = 10
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        if full is False:
            return self._wait_for_screen(
                timeout, expected_behaviour, search_by, self._loading_screen_xpath_end
            )
        else:
            self._wait_for_screen(
                timeout, expected_behaviour, search_by, self._loading_screen_xpath_start
            )
            return self._wait_for_screen(
                timeout, expected_behaviour, search_by, self._loading_screen_xpath_end
            )

    def for_support_summon(self):
        start = time.time()

        while True:
            parser = bs(self._driver.page_source, "lxml")

            if time.time() - start > 3:
                print("Where is quest support window?")
                break

            regex = re.compile(".*icon-supporter-type.*")
            sup_types_ele = parser.find_all("div", {"class": regex})
            in_summon_screen_uri = "#quest/supporter" in self._driver.current_url
            if in_summon_screen_uri:
                if sup_types_ele:
                    first_sup_type_ele = sup_types_ele[0]
                    fire_sup_type_xpath = self._bot.handle.get_xpath_from_ele(
                        first_sup_type_ele
                    )
                    self._bot.press._wait_for_button(By.XPATH, fire_sup_type_xpath)
                    return True
