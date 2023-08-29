from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss

from .timeout import Timeout

import time


class Press:
    def __init__(self, game_handler):
        self._driver = game_handler.driver
        self._bot = game_handler
        self._Actions = ActionChains(self._driver)
        self._Timeout = Timeout(self._driver)
        self._quest_button_main_menu_class = "prt-link-quest"
        self._quest_button_after_fight_class = "btn-control"
        self._raid_button_class = "prt-multi-button"
        self._enter_raid_id_id = "tab-id"
        self._join_raid_room_class = "btn-post-key"
        self._support_summon_confirm_xpath = (
            '//*[@id="wrapper"]/div[3]/div[3]/div[3]/div[2]'
        )
        self._attack_button_css = ".btn-attack-start.display-on"
        self._results_button_class = "btn-result"
        self._cancel_button_class = "btn-usual-cancel"
        self._ok_button_class = "btn-usual-ok"
        self._close_button_class = "btn-usual-close"
        self._approve_backup_request_css = ".btn-usual-text.with-potion"
        self._quest_button_after_fight_no_loot_css = ".btn-control.location-href"
        self._back_button_css = ".btn-command-back.display-on"
        self._summons_button_css = ".prt-list-top.btn-command-summon.summon-on"
        self._summon_card_xpath = (
            '//*[@id="wrapper"]/div[3]/div[2]/div[9]/div[2]/div/div[1]'
        )
        self._next_char_class = "ico-next"
        self._previous_char_class = "ico-pre"
        self._special_quests_class = "btn-extra-quest"
        self._fight_advice_class = "prt-advice"
        self._log_ability_css = ".prt-raid-log.log-ability"
        self._play_again_quest_css = ".btn-retry.cnt-quest"
        self._confirm_summon_battle_xpath = (
            '//*[@id="wrapper"]/div[3]/div[14]/div[3]/div[2]'
        )
        self._retreat_class = "btn-withdraw"
        self._skip_button_class = "btn-command-skip"
        self._next_button_class = "btn-usual-next"
        self._auto_attack_xpath = '//*[@id="wrapper"]/div[3]/div[2]/div[8]'
        self._consumables_xpath = (
            '//*[@id="wrapper"]/div[3]/div[2]/div[2]/div[1]/div[1]/div[2]'
        )
        self._consumables_ap_xpath = '//*[@id="prt-target-list"]/div[2]/img'
        self._consumables_ep_xpath = '//*[@id="prt-target-list"]/div[4]/img'
        self._skippable_battle_xpath = '//*[@id="pop"]/div/div[2]/div/div[4]/label'
        self._approve_backup_request_gw_xpath = '//*[@id="pop"]/div/div[3]/a'
        # TODO
        self._guild_wars_xpath = (
            '//*[@id="wrapper"]/div[3]/div[2]/div[4]/div[2]/div/img'
        )
        self._mobage_thing_xpath = '//*[@id="notify-response-button"]/div'
        self._raid_refresh_btn_xpath = '//*[@id="prt-assist-search"]/div[2]/div[2]'

    def _wait_for_button(self, search_by, element_name, timeout=5):
        expected_behaviour = EC.element_to_be_clickable
        search_by = search_by

        button = self._Timeout.wait_for_element(
            timeout, expected_behaviour, search_by, element_name
        )
        return button

    def usual_cancel(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._cancel_button_class)
        self._driver.find_element(By.CLASS_NAME, self._cancel_button_class).click()

    def quest_button_main_menu(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._quest_button_main_menu_class)
        self._driver.find_element(
            By.CLASS_NAME, self._quest_button_main_menu_class
        ).click()

    def usual_event_home(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._quest_button_after_fight_class)
        self._driver.find_element(
            By.CLASS_NAME, self._quest_button_after_fight_class
        ).click()

    def quest_button_after_fight_no_loot(self):
        search_by = By.CSS_SELECTOR

        self._wait_for_button(search_by, self._quest_button_after_fight_no_loot_css)
        self._driver.find_element(
            By.CSS_SELECTOR, self._quest_button_after_fight_no_loot_css
        ).click()

    def raid_button(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._raid_button_class)
        self._driver.find_element(By.CLASS_NAME, self._raid_button_class).click()

    def enter_raid_id(self):
        search_by = By.ID

        self._wait_for_button(search_by, self._enter_raid_id_id)
        self._driver.find_element(By.ID, self._enter_raid_id_id).click()

    def join_raid(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._join_raid_room_class)
        # TESTING THIS OUT
        btn = self._driver.find_element(By.CLASS_NAME, self._join_raid_room_class)
        self._Actions.double_click(btn).perform()
        # self._driver.find_element(By.CLASS_NAME, self._join_raid_room_class).click()

    def support_summon(
        self, support_dict=None, support_element_num=None, first_summon=False
    ):
        # TODO
        # Bot should be able to pick a specific support summon
        # Also I'm testing double_click on how it performs in game
        if first_summon is True:
            first_support_summon_xpath = f'//*[@id="cnt-quest"]/div[2]/div[{support_element_num + 3}]/div[1]/div[4]'

            # Misc. support
            if support_element_num == 7:
                first_support_summon_xpath = (
                    f'//*[@id="cnt-quest"]/div[2]/div[{3}]/div[1]/div[4]'
                )

            search_by = By.XPATH

            self._wait_for_button(search_by, first_support_summon_xpath)
            self._driver.find_element(By.XPATH, first_support_summon_xpath).click()
        else:
            element_tab_num = (
                (support_element_num + 3) if support_element_num < 7 else 3
            )
            support_summon_xpath = f'//*[@id="cnt-quest"]/div[2]/div[{element_tab_num}]/div[{support_dict["Num"]}]'
            search_by = By.XPATH
            self._wait_for_button(search_by, support_summon_xpath)
            element = self._driver.find_element(By.XPATH, support_summon_xpath)
            self._driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()

    def support_element(
        self, support_dict=None, support_element_num=None, first_summon=None
    ):
        # Support element tabs in order:
        # 1 - Fire
        # 2 - Water
        # 3 - Earth
        # 4 - Wind
        # 5 - Light
        # 6 - Dark
        # 7 - Misc. - TODO

        support_element_xpath = f'//*[@id="prt-type"]/div[{support_element_num}]'
        search_by = By.XPATH

        self._wait_for_button(search_by, support_element_xpath)
        self._driver.find_element(By.XPATH, support_element_xpath).click()

    def confirm_support_summon(
        self, support_dict=None, support_element_num=None, first_summon=None
    ):
        while True:
            parser = bs(self._driver.page_source, "lxml")
            confirm_btn = parser.find("div", {"class": "btn-usual-ok se-quest-start"})

            req_id = self._bot.game_requests.find_generic_request("quest/decks_info")

            if req_id:
                req_body = self._bot.game_requests.get_resp_body(req_id)
                if "popup" in req_body:
                    action = self._bot.handle.check_if_action_is_needed(req_body)
                    if action:
                        return True

            if confirm_btn:
                self._driver.find_element(By.XPATH, self._support_summon_confirm_xpath).click()
                return False

    def attack_button(self):
        start = time.time()

        strainer = ss("div", attrs={"id": "cnt-raid-information"})
        try:
            while True:
                if time.time() - start > 15:
                    break

                parser = bs(self._driver.page_source, "lxml", parse_only=strainer)

                attack_button_on = parser.find(
                    "div", class_="btn-attack-start display-on"
                )

                if attack_button_on:
                    self._driver.find_element(
                        By.CSS_SELECTOR, self._attack_button_css
                    ).click()
                    break
        except:
            pass

    def results_button(self):
        timeout = 10
        search_by = By.CLASS_NAME

        if "result" not in self._driver.current_url:
            self._wait_for_button(
                search_by, self._results_button_class, timeout=timeout
            )
            self._driver.find_element(By.CLASS_NAME, self._results_button_class).click()

    def approve_backup_request(self):
        search_by = By.CSS_SELECTOR
        search_by_gw = By.XPATH

        css = self._wait_for_button(search_by, self._approve_backup_request_css)
        if css:
            self._driver.find_element(
                By.CSS_SELECTOR, self._approve_backup_request_css
            ).click()
            return

        gw = self._wait_for_button(search_by_gw, self._approve_backup_request_gw_xpath)
        if gw:
            self._driver.find_element(
                By.XPATH, self._approve_backup_request_gw_xpath
            ).click()

    def usual_ok(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._ok_button_class)
        self._driver.find_element(By.CLASS_NAME, self._ok_button_class).click()

    def usual_close(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._close_button_class)
        self._driver.find_element(By.CLASS_NAME, self._close_button_class).click()

    def char_to_start_queue(self, char_num):
        char_xpath = f'//*[@id="prt-command-top"]/div/div/div[{char_num}]'
        search_by = By.XPATH

        self._wait_for_button(search_by, char_xpath)
        self._driver.find_element(By.XPATH, char_xpath).click()

    def next_char(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._next_char_class)
        self._driver.find_element(By.CLASS_NAME, self._next_char_class).click()

    def previous_char(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._previous_char_class)
        self._driver.find_element(By.CLASS_NAME, self._previous_char_class).click()

    def char_skill(self, char_num, skill_num, raids=False):
        div = "div[10]" if raids else "div[10]"
        ability_xpath = f'//*[@id="wrapper"]/div[3]/div[2]/{div}/div[{char_num + 2}]/div[3]/div[{skill_num}]'
        search_by = By.XPATH

        self._wait_for_button(search_by, ability_xpath)
        self._driver.find_element(By.XPATH, ability_xpath).click()

    def select_part_member(self, char_num):
        party_member_xpath = (
            f'//*[@id="wrapper"]/div[3]/div[10]/div[2]/div[2]/div[2]/div[{char_num}]'
        )
        search_by = By.XPATH

        self._wait_for_button(search_by, party_member_xpath)
        self._driver.find_element(By.XPATH, party_member_xpath).click()

    def back(self):
        search_by = By.CSS_SELECTOR

        self._wait_for_button(search_by, self._back_button_css)
        self._driver.find_element(By.CSS_SELECTOR, self._back_button_css).click()

    def summon_num(self, summon_num, raids=False):
        div = "div[10]" if raids else "div[10]"
        summon_xpath = (
            f'//*[@id="wrapper"]/div[3]/div[2]/{div}/div[2]/div/div[{summon_num + 1}]'
        )
        search_by = By.XPATH

        self._wait_for_button(search_by, summon_xpath)
        self._driver.find_element(By.XPATH, summon_xpath).click()

    def summon_card(self, raids=False):
        div = "div[10]" if raids else "div[10]"
        summon_card_xpath = f'//*[@id="wrapper"]/div[3]/div[2]/{div}/div[2]/div/div[1]'
        search_by = By.XPATH

        self._wait_for_button(search_by, summon_card_xpath)
        self._driver.find_element(By.XPATH, summon_card_xpath).click()

    def special_quests(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._special_quests_class)
        self._driver.find_element(By.CLASS_NAME, self._special_quests_class).click()

    def specific_treasure_quest(self, treasure_quest_num):
        # treasure_quest_num is in accordance to menu dict at when launching the bot
        search_by = By.XPATH

        specific_treasure_quest_xpath = (
            f'//*[@id="cnt-normal-quest"]/div/div/div[{treasure_quest_num}]/div/div[4]'
        )
        self._wait_for_button(search_by, specific_treasure_quest_xpath)
        self._driver.find_element(By.XPATH, specific_treasure_quest_xpath).click()

    def by_chapter_id(self, chapter_id):
        # quest_id parsed from page source code in accordance to what a bot user chose
        search_by = By.XPATH

        chapter_id_btn_xpath = f"//div[@data-chapter-id='{chapter_id}']"
        self._wait_for_button(search_by, chapter_id_btn_xpath)
        self._driver.find_element(By.XPATH, chapter_id_btn_xpath).click()

    def coop_room(self):
        coop_room_xpath = '//*[@id="cnt-result"]/div[1]/div[2]/div[5]'
        start = time.time()

        while True:
            if time.time() - start > 5:
                break

            parser = bs(self._driver.page_source, "lxml")

            coop_room_button = parser.find_all(
                "div", {"class": "btn-control", "style": "display: block;"}
            )

            if coop_room_button:
                self._driver.find_element(By.XPATH, coop_room_xpath).click()
                break

            time.sleep(0.15)

    def fight_advice(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._fight_advice_class)
        self._driver.find_element(By.CLASS_NAME, self._fight_advice_class).click()

    def log_ability(self):
        search_by = By.XPATH
        timeout = 2

        # self._wait_for_button(search_by, self._log_ability_xpath, timeout=timeout)
        self._driver.find_element(By.CSS_SELECTOR, self._log_ability_css).click()

    def play_again_quest(self):
        search_by = By.CSS_SELECTOR

        elem = self._wait_for_button(search_by, self._play_again_quest_css, timeout=10)
        self._driver.find_element(
            By.CSS_SELECTOR, self._play_again_quest_css
        ).click() if elem else None
        return elem

    # raids arg is not needed here, but added to make it easier for the queue adaptation
    def confirm_summon_fight(self, raids=False):
        search_by = By.XPATH

        self._wait_for_button(search_by, self._confirm_summon_battle_xpath)
        self._driver.find_element(By.XPATH, self._confirm_summon_battle_xpath).click()

    def guild_wars(self):
        search_by = By.XPATH

        self._wait_for_button(search_by, self._guild_wars_xpath)
        self._driver.find_element(By.XPATH, self._guild_wars_xpath).click()

    def gw_raid_type(self, type_num):
        # 3 - Cybele
        # 2 - EX
        # 1 - Dimorphodon

        raid_type_xpath = f'//*[@id="cnt-teamraid-top"]/div[4]/div[{type_num}]'
        search_by = By.XPATH
        self._wait_for_button(search_by, raid_type_xpath)
        self._driver.find_element(By.XPATH, raid_type_xpath).click()

    def gw_dimorphodon_diff(self, diff_num):
        # 1 - Easy

        dimo_diff_xpath = f'//*[@id="pop"]/div/div[2]/div/div[4]/div[{diff_num}]'
        search_by = By.XPATH

        self._wait_for_button(search_by, dimo_diff_xpath)
        self._driver.find_element(By.XPATH, dimo_diff_xpath).click()

    def gw_ex_diff(self, diff_num):
        if diff_num != 3:
            ex_diff_xpath = (
                f'//*[@id="pop"]/div/div[2]/div/div[3]/div[1]/div/div[{diff_num}]'
            )
        else:
            ex_diff_xpath = '//*[@id="pop"]/div/div[2]/div/div[3]/div[2]/div/div'

        search_by = By.XPATH

        self._wait_for_button(search_by, ex_diff_xpath)
        self._driver.find_element(By.XPATH, ex_diff_xpath).click()

    def usual_retreat(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._retreat_class)
        self._driver.find_element(By.CLASS_NAME, self._retreat_class).click()

    def usual_skip(self):
        search_by = By.CLASS_NAME

        self._wait_for_button(search_by, self._skip_button_class)
        self._driver.find_element(By.CLASS_NAME, self._skip_button_class).click()

    def usual_next(self):
        search_by = By.CLASS_NAME
        self._wait_for_button(search_by, self._next_button_class)
        self._driver.find_element(By.CLASS_NAME, self._next_button_class).click()

    def auto_attack(self):
        start = time.time()

        while True:
            if time.time() - start > 5:
                break

            parser = bs(self._driver.page_source, "lxml")

            auto_button = parser.find_all(
                "div", {"class": "btn-auto", "style": "display: block;"}
            )

            if auto_button:
                # With "auto-guard" auto-attack xpath
                # self._driver.find_element(By.XPATH, self._auto_attack_xpath).click()
                # Without one
                self._driver.find_element(
                    By.XPATH, '//*[@id="wrapper"]/div[3]/div[2]/div[7]'
                ).click()
                break

            time.sleep(0.15)

    def consumables(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._consumables_xpath, timeout=7)
        self._driver.find_element(By.XPATH, self._consumables_xpath).click()

    def consumables_ap(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._consumables_ap_xpath)
        self._driver.find_element(By.XPATH, self._consumables_ap_xpath).click()

    def consumables_ep(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._consumables_ep_xpath)
        self._driver.find_element(By.XPATH, self._consumables_ep_xpath).click()

    def skip_nightmare_battle(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._skippable_battle_xpath)
        self._driver.find_element(By.XPATH, self._skippable_battle_xpath).click()

    def approve_mobage_thing(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._mobage_thing_xpath)
        self._driver.find_element(search_by, self._mobage_thing_xpath).click()

    def raid_filter_refresh(self):
        search_by = By.XPATH
        self._wait_for_button(search_by, self._raid_refresh_btn_xpath)
        self._driver.find_element(search_by, self._raid_refresh_btn_xpath).click()

    def pick_raid(self, raid_num):
        raid_pick_xpath = f'//*[@id="prt-search-list"]/div[{raid_num}]'
        search_by = By.XPATH

        # i'm tired
        element = self._driver.find_element(By.XPATH, raid_pick_xpath)
        self._driver.execute_script("arguments[0].scrollIntoView(true);", element)

        self._wait_for_button(search_by, raid_pick_xpath)
        self._driver.find_element(search_by, raid_pick_xpath).click()

    def fa_in_loading_screen(self, xpath):
        search_by = By.XPATH
        ready_btn_xpath = xpath

        self._wait_for_button(search_by, ready_btn_xpath)
        self._driver.find_element(search_by, ready_btn_xpath).click()
