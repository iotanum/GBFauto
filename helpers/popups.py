from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from helpers.timeout import Timeout

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

import time


class Popup:
    def __init__(self, game_handler):
        self._driver = game_handler.driver
        self._Timeout = Timeout(self._driver)
        self._verification_xpath = (
            "//*[@class='prt-popup-header' and contains(text(),'Access Verification')]"
        )
        self._backup_request_xpath = (
            "//div[contains(@class, 'assist') and contains(@style, 'display: block')]"
        )

    def _wait_for_popup(
        self,
        timeout,
        search_by,
        element_name,
        expected_behaviour=EC.visibility_of_element_located,
    ):
        expected_behaviour = expected_behaviour
        popup = self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, element_name
        )

        return popup

    def backup_request(self):
        start = time.time()

        # while True:
        #     print("backup request wait")
        #     if time.time() - start > 5:
        #         break
        #
        #     strainer = ss('div', attrs={'id': 'cnt-raid-information'})
        #     parser = bs(self._driver.page_source, 'lxml', parse_only=strainer)
        #
        #     attack_button_on = parser.find('div', class_='btn-attack-start display-on')
        #
        #     if attack_button_on:
        #         return
        #
        #     time.sleep(0.1)
        timeout = 2
        print("bakcup vistiek ce esu")
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._backup_request_xpath)

    def human_verification(self):
        timeout = 2
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._verification_xpath)
