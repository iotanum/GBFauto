from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .timeout import Timeout


class Wait:

    """
        A class for 'waiting' and/or handling various screens.
        Playing around with these methods could get the result *you* need,
        since selenium is all about waiting and THEN doing.

        :returns
            :bool if screen has appeared/disappeared.
    """

    def __init__(self, game_handler):
        self._driver = game_handler.driver
        self._Timeout = Timeout(self._driver)
        self._loading_screen_xpath = "//div[@id='loading'][@style='display: none;']"
        self._fight_end_screen_xpath = "//div[@id='main-mask'][contains(@style,'display: none')]"

        self._loot_screen_xpath = "//div[@class='cnt-get-treasure'][contains(@style,'display: block')]"
        self._fight_ready_screen_xpath = "//div[@class='prt-start-direction disable-ready-auto-setting']" \
                                         "[contains(@style,'display: none')]"
        self._quest_advancement_screen_xpath = "//div[@class='opaque-mask']" \
                                               "[contains(@style,'display: none')]"
        self._fight_main_mask_xpath = "//div[@class='active-mask']" \
                                      "[contains(@style,'display: none')]"
        self._test_fight_ready_mask = "//div[@class='mask']" \
                                      "[contains(@style,'display: none')]"

    # Main method used by all other methods
    def _wait_for_screen(self, timeout, expected_behaviour, search_by, element_name):
        screen = self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, element_name)
        # print(screen, element_name, "+++")
        return screen

    def for_loading_screen(self):
        # use with caution, only in methods that are triggered *AFTER* loading screen
        timeout = 10
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH
        return self._wait_for_screen(timeout, expected_behaviour, search_by, self._loading_screen_xpath)

    def for_fight_end_screen(self):
        timeout = 5
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._wait_for_screen(timeout, expected_behaviour, search_by, self._fight_end_screen_xpath)

    def for_loot_screen(self):
        # use with caution, only in methods that are triggered *AFTER* raid battles
        timeout = 5
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._wait_for_screen(timeout, expected_behaviour, search_by, self._loot_screen_xpath)

    def for_fight_ready_screen(self):
        timeout = 5
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._wait_for_screen(timeout, expected_behaviour, search_by, self._fight_ready_screen_xpath)

    def for_quest_results_screen(self):
        timeout = 5
        expected_behaviour = EC.url_contains("empty")

        return self._Timeout.wait_for_element_no_search_by(timeout, expected_behaviour)

    def for_quest_advencment_screen(self):
        timeout = 5
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._Timeout.wait_for_element(timeout, expected_behaviour, search_by,
                                              self._quest_advancement_screen_xpath)

    def for_fight_main_mask(self):
        timeout = 5
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, self._fight_main_mask_xpath)

    def for_test_fight_ready_mask(self):
        timeout = 3
        expected_behaviour = EC.presence_of_element_located
        search_by = By.XPATH

        return self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, self._test_fight_ready_mask)
