from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from helpers.timeout import Timeout


class Popup:
    def __init__(self, obj):
        self._driver = obj.driver
        self._Timeout = Timeout(self._driver)
        self._resume_quest_xpath = "//div[@class='pop-usual popRestartQuest pop-show']" \
                                   "[contains(@style,'display: block')]"
        self._stamina_class = "pop-stamina"
        self._verification_xpath = "//*[@class='prt-popup-header' and contains(text(),'Access Verification')]"
        self._backup_request_xpath = "//div[contains(@class, 'assist') and contains(@style, 'display: block')]"
        self._after_fight_xp_xpath = "//div[@class='pop-usual pop-exp pop-show']" \
                                     "[contains(@style,'display: block')]"
        self._friend_request_class = "prt-friend-request"
        self._typical_popup = "pop-show"
        self._extended_mastery_id = "cjs-lp-rankup"
        self._achievement_xpath = "//div[@class='pop-usual pop-notification-title pop-show']" \
                                  "[contains(@style,'display: block')]"
        self._new_item_class = "img-newitem"
        self._quest_submenu = "//div[@class='pop-usual pop-quest-detail pop-show']" \
                              "[contains(@style,'display: block')]"
        self._fight_advice = "prt-advice"
        self._log_ability_xpath = "//div[@class='prt-raid-log log-ability']" \
                                  "[contains(@style,'display: block')]"
        self._new_rank_xpath = "//div[@class='pop-usual pop-player-up pop-show']" \
                               "[contains(@style,'display: block')]"
        self._battle_concluded_xpath = "//div[@class='pop-usual pop-rematch-fail pop-show']" \
                                       "[contains(@style,'display: block')]"
        self._event_items_xpath = "//div[@class='pop-usual pop-event-item pop-show']" \
                                  "[contains(@style,'display: block')]"

    def _wait_for_popup(self, timeout, search_by, element_name, expected_behaviour=EC.visibility_of_element_located):
        expected_behaviour = expected_behaviour
        popup = self._Timeout.wait_for_element(timeout, expected_behaviour, search_by, element_name)

        return popup

    def resume_quest(self):
        timeout = 3
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._resume_quest_xpath)

    def backup_request(self):
        timeout = 7
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._backup_request_xpath)

    def not_enough_x(self):
        timeout = 3
        search_by = By.CLASS_NAME

        return self._wait_for_popup(timeout, search_by, self._stamina_class)

    def human_verification(self):
        timeout = 4
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._verification_xpath)

    def friend_request(self):
        timeout = 3
        search_by = By.CLASS_NAME

        return self._wait_for_popup(timeout, search_by, self._friend_request_class)

    def pre_raid_popup(self):
        timeout = 2.2
        search_by = By.CLASS_NAME

        return self._wait_for_popup(timeout, search_by, self._typical_popup)

    def after_fight_xp(self):
        timeout = 5
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._after_fight_xp_xpath)

    def extended_mastery(self):
        timeout = 2
        search_by = By.ID

        return self._wait_for_popup(timeout, search_by, self._extended_mastery_id)

    def achievement(self):
        timeout = 3
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._achievement_xpath)

    def new_item(self):
        timeout = 3
        search_by = By.CLASS_NAME

        return self._wait_for_popup(timeout, search_by, self._new_item_class)

    def quest_submenu(self):
        timeout = 3
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._quest_submenu)

    def fight_advice(self):
        timeout = 1
        search_by = By.CLASS_NAME

        return self._wait_for_popup(timeout, search_by, self._fight_advice)

    def log_ability(self):
        # returns True if this popup appears
        timeout = 2
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._log_ability_xpath)

    def new_rank(self):
        timeout = 3
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._new_rank_xpath)

    def battle_concluded(self):
        timeout = 1
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._battle_concluded_xpath)

    def event_items(self):
        timeout = 3
        search_by = By.XPATH

        return self._wait_for_popup(timeout, search_by, self._event_items_xpath)
