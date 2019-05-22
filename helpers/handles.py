import time
import re
import os
import random

from selenium import common as selenium_err

from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss
from dotenv import load_dotenv

load_dotenv('config.env')

EXTREME_BATTLES = int(os.getenv('EXTREME_BATTLES'))
REQUEST_BACKUP = int(os.getenv('REQUEST_BACKUP'))
SUPPORT_ELEMENT = int(os.getenv('SUPPORT_ELEMENT'))


class Handle:
    def __init__(self, game_handler):
        self._bot = game_handler
        self._driver = game_handler.driver

    def after_fight_popups(self, kill=False):
        # After the page loads, there's no way to 'tell' if there will be
        # x popup or y popup, its load time depends on what popup it is
        # so plain old 'sleep' will do the trick
        # Don't need to sleep if this is being called
        # for the second bunch of popups
        if kill is True:
            while True:
                current_url = self._driver.current_url
                if 'result' in current_url:
                    time.sleep(3)
                    break
                time.sleep(0.5)

        popup_search_start = time.time()

        while True:
            parser = bs(self._driver.page_source, 'lxml')
            popup = parser.find('div', {'class': ['pop-show']})
            loot = parser.find('div', {'class': 'cnt-get-treasure', 'style': 'display: block;'})

            current_url = self._driver.current_url

            # Ignore 'Not enough AP/EP' popup for now.
            # Also this popup appears last, so we need to exit
            if popup is not None and 'pop-stamina' in popup['class']:
                break

            # Ignore 'Backup Request' popup, this handle can accidentally
            # get triggered on this after refreshing in a raid battle.
            if popup is not None and 'pop-start-assist' in popup['class']:
                popup = None

            # Extended mastery 'popup' isn't actually a popup, but a canvas put on
            # entirety of results screen, need to be handled separately
            extended_mastery = parser.find('div', {'class': 'onm-anim-parts'})

            # If no popups for 3.5 seconds - exit while loop
            # or if there was no popups
            popup_search_time = time.time()
            if popup_search_time - popup_search_start > 3.5 or 'result' not in current_url:
                # 'After fight popup' means that the bot finished a quest
                if kill is True:
                    self._bot.total_fights += 1
                break

            # Exit loop if 'loot' screen has appeared.
            # This means that the first bunch of popups after the fight
            # are done. For ex.: exp, event stuff, etc.
            # Also duplicate if statement for exiting the loop
            # for easier readability
            if loot and kill is True:
                self._bot.total_fights += 1
                time.sleep(0.5)
                break

            # Extracts the button/buttons inside the popup
            if popup:
                popup_name = str(popup['class'])
                # Reset popup search start timer if popup was found
                popup_search_start = time.time()
                # Get button
                popup_footer = popup.find('div', {'class': 'prt-popup-footer'})
                popup_button = popup_footer.find('div', {'class': True})
                popup_button = popup_button['class']

                # Check every type of popup
                if 'event-item' in popup_name:
                    self._count_after_fight_event_items(popup)
                    self._bot.press.usual_ok()

                elif 'pop-exp' in popup_name:
                    self._count_after_fight_xp(popup)
                    self._bot.press.usual_ok()

                elif 'player-up' in popup_name:
                    print('New rank!')
                    self._bot.press.usual_ok()

                elif 'notification-title' in popup_name:
                    print('New achievement!')
                    self._bot.press.usual_close()

                elif 'friend-request' in popup_name:
                    self._bot.press.usual_cancel()

                elif 'zc-up' in popup_name:
                    popup_body = popup.find('div', {'class': 'txt-zc-new'}).text
                    print(popup_body)
                    self._bot.press.usual_ok()

                elif 'npc-change-ability' in popup_name:
                    character_ability_change = popup.find('div', {'class': 'txt-change-ability'}).text
                    character_ability_change_text = self._convert_html_element_to_text(character_ability_change)
                    ability, change = character_ability_change_text.split(' from\n')
                    print(f"{ability}. ({change})")
                    self._bot.press.usual_ok()

                elif 'open-fate' in popup_name:
                    fate_ep_description = popup.find('div', {'class': 'prt-description'}).text
                    fate_ep_description = self._convert_html_element_to_text(fate_ep_description)
                    fate_ep_description = fate_ep_description.replace("'s", "'s ")
                    print(fate_ep_description)
                    self._bot.press.usual_ok()

                elif 'hell-appearance' in popup_name:
                    print('Nightmare battle!')
                    if EXTREME_BATTLES == 1:
                        try:
                            self._bot.press.usual_next()
                            self._extreme_fight()
                            return True
                        except selenium_err.exceptions.NoSuchElementException:
                            pass
                    else:
                        self._bot.press.usual_close()

                elif any(name in popup_name for name in ['mission-check-treasureraid', 'update-beginner-mission-teamraid']):
                    mission_description = popup.find('div', {'class': 'txt-mission-description'}).text
                    mission_progress = popup.find('div', {'class': 'prt-mission-progress'}).text
                    mission_progress = mission_progress.strip()
                    print(mission_description, f"({mission_progress})")
                    self._bot.press.usual_close()

                elif 'trajectory-info' in popup_name:
                    print('Game reset!')
                    self._bot.press.usual_ok()

                elif 'advent-proud-appearance' in popup_name:
                    print('Proud+ battle unclocked!')
                    self._bot.press.usual_close()

                elif 'zenith-bonus-open' in popup_name:
                    print('EMP upgrade!')
                    self._bot.press.usual_close()

                elif 'zenith-open' in popup_name:
                    print('Unlocked EMP!')
                    self._bot.press.usual_ok()

                elif 'newitem' in popup_name:
                    item_img_url = popup.find('img', {'class': 'img-newitem'})
                    item_name = popup.find('div', {'class': 'txt-newitem-name'}).text
                    print(f"New item! '{item_name}'.\n{item_img_url}")
                    self._bot.press.usual_ok()

                elif 'job-ability' in popup_name:
                    skill_name = popup.find('div', {'class': 'txt-jobability-name'}).text
                    print(f"Learned a new skill '{skill_name}'.")
                    self._bot.press.usual_ok()

                elif 'job-master' in popup_name:
                    class_name = popup.find('div', {'class': 'prt-bonus-box'}).text
                    class_name = str(class_name)[4:]
                    gained_bonus = popup.find('div', {'class': 'txt-bonus-name'}).text
                    print(f"Maxed out '{class_name}', gained '{gained_bonus}'!")
                    self._bot.press.usual_ok()

                elif 'pop-error' in popup_name:
                    self._bot.press.usual_ok()

                elif 'get-abilityitem' in popup_name:
                    popup_header = popup.find('div', {'class': 'prt-popup-header'}).text
                    print(f"{popup_header}")
                    self._bot.press.usual_ok()

                else:
                    print("Unhandled popup!\nPage source and error picture in 'errors' folder.")
                    print(f"Popup element: {popup}")
                    # Placeholder handling of unhandled popup
                    self._driver.find_element_by_class_name(popup_button).click()

            if extended_mastery:
                print('New extended mastery!')
                # Wait a bit and just remove the element
                time.sleep(4)
                # Also needs a timer reset
                popup_search_start = time.time()
                elem = self._driver.find_element_by_class_name('onm-anim-parts')
                elem.click()
                time.sleep(1)

    def pre_fight_screens(self):
        popup_search_start = time.time()

        while True:
            popup_search_time = time.time()

            parser = bs(self._driver.page_source, 'lxml')

            side_scroll_quest = parser.find('div', {'class': 'anim-title anim'})
            if side_scroll_quest:
                self._bot.press.usual_skip()
                self._bot.popup.skip_side_scroll()
                self._driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div[2]').click()
                self._bot.popup.side_scroll_results()
                self._driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div').click()

            if popup_search_time - popup_search_start > 2:
                break

    def pre_fight_popup(self):
        popup_search_start = time.time()
        popup_present = False

        while True:
            popup_search_time = time.time()

            parser = bs(self._driver.page_source, 'lxml')
            popup = parser.find('div', {'class': ['common-pop-error']})

            if popup:
                popup_present = True
                popup_search_start = time.time()

                # Needed to distinguish between verification/typical error popups
                popup_header = str(popup.find('div', {'class': 'prt-popup-header'}).text)

                if 'Battle' in popup_header:
                    self._bot.press.usual_ok()
                    return True

                elif 'Access Verification' in popup_header:
                    self.human_verification()
                    return 'verification'

            if popup_search_time - popup_search_start > 1:
                # If there was a pre-fight popup, need to return a bool
                # and handle it appropriately (ex.: repeat last instruction)
                break

    def pre_fight_support_summons(self):
        self._bot.wait.for_loading_screen()

        instructions_to_run = {'support_element': self._bot.press.support_element,
                               'first_summon': self._bot.press.first_support_summon,
                               'confirm_summon': self._bot.press.confirm_support_summon}

        instruction_to_run = 'support_element'

        while True:
            # Execute the instruction
            if instruction_to_run != 'confirm_summon':
                instructions_to_run[instruction_to_run](SUPPORT_ELEMENT)
            else:
                instructions_to_run[instruction_to_run]()
                time.sleep(0.5)

            # Then check for popups/verification and handle accordingly
            popup = self.pre_fight_popup()
            # Repeat last instruction if verification
            if popup == 'verification':
                instruction_to_run = instruction_to_run
            # Return if popup was present (needs to be handled elsewhere)
            elif popup is True:
                return False
            # If no popup - continue with the 'next' instruction to be ran
            else:
                next_instruction_num = list(instructions_to_run.keys()).index(instruction_to_run) + 1
                try:
                    next_instruction = list(instructions_to_run)[next_instruction_num]
                    instruction_to_run = next_instruction
                except IndexError:
                    break

    def wait_before_fight(self, fight_start=True):
        element_found = False
        start = time.time()

        while True:
            if time.time() - start > 15:
                break

            strainer = ss('div', attrs={'id': 'cnt-raid-information'})
            parser = bs(self._driver.page_source, 'lxml', parse_only=strainer)

            if fight_start is True:
                attack_button_on = parser.find('div', class_='btn-attack-start display-on')
                if attack_button_on:
                    break
            else:
                # attack_button_off = parser.find('div', {'class': ['btn-attack-start', 'display-off']})
                attack_button = parser.find('div', class_='btn-attack-start')
                if attack_button or element_found is True:
                    element_found = True
                    attack_button_on = parser.find('div', class_='btn-attack-start display-on')
                    if attack_button_on:
                        break

            # Eat less CPU
            time.sleep(0.2)

    def wait_after_queue_refresh(self):
        start = time.time()

        while True:
            if time.time() - start > 60:
                break

            # Wait for the skill overlay to 'hide' (that means it's finished) and exit
            # the loop
            strainer = ss('div', attrs={'id': 'cnt-raid-information'})
            parser = bs(self._driver.page_source, 'lxml', parse_only=strainer)

            finished_queue = parser.find('div', class_='prt-ability-rail-overlayer hide')
            if finished_queue:
                break

            # Eat less CPU
            time.sleep(0.5)

    def wait_results_button(self):
        start = time.time()

        while True:
            if time.time() - start > 15:
                break

            parser = bs(self._driver.page_source, 'lxml')

            results_button = parser.find('div', {'class': 'prt-command-end', 'style': 'display: block;'})
            if results_button:
                break

            # Eat less CPU
            time.sleep(0.5)

    def not_enough_of_x(self):
        start = time.time()

        while True:
            current_url = self._driver.current_url

            # Exit loop if in 'Pick support summon' page
            if time.time() - start > 3 or '#quest/supporter' in current_url:
                break

            parser = bs(self._driver.page_source, 'lxml')

            ap_ep_popup = parser.find('div', class_='pop-usual pop-stamina pop-show')
            various_popup = parser.find('div', {'class': ['common-pop-error']})

            if ap_ep_popup:
                ap_ep_amount = random.randint(1, 5)
                self._bot.action.use_potions_or_pills(ap_ep_amount)
                self._bot.wait.for_loading_screen()
                self._bot.press.usual_ok()
                break

            elif various_popup:
                break

            # Eat less CPU
            time.sleep(0.5)

    def backup_request(self):
        backup_request = self._bot.popup.backup_request()

        if backup_request is True:
            try:
                # If user wants to request backups - go for it
                if REQUEST_BACKUP == 1:
                    try:
                        self._bot.press.approve_backup_request()
                        self._bot.press.usual_ok()
                    except selenium_err.exceptions.NoSuchElementException:
                        self._bot.press.usual_ok()
                # otherwise - no.
                else:
                    try:
                        self._bot.press.usual_cancel()
                    except selenium_err.exceptions.ElementNotVisibleException:
                        try:
                            self._bot.press.usual_ok()
                        except:
                            pass

                # Backup screen takes time to fully disappear from the DOM
                time.sleep(0.8)
            except selenium_err.exceptions.TimeoutException:
                pass

            return True
        return False

    def _convert_gain_to_int(self, gain):
        regex_num_pattern = r'\d+'
        gains = re.findall(regex_num_pattern, gain)
        gain = [int(s) for s in gains]
        return sum(gain)

    def _count_after_fight_xp(self, xp_popup_element):
        # Declare 'span' element names for appropriate after fight gains
        # First element: non-bonus points, second element: bonus points (during events)
        rank = ['txt-rankpt-plus', 'exp-bonus']
        exp = ['txt-exp-plus', 'host-bonus']
        pendants = ['txt-mbp-plus', 'txt-add-bonus']

        gains = xp_popup_element.find('div', {'class': 'prt-exp-gain'}).find_all('span')

        if gains:
            for gain in gains:
                if gain is not None:
                    gain_name = str(gain['class']).lower()
                    gain_num = self._convert_gain_to_int(gain.text)
                    if any(elem_name in gain_name for elem_name in rank):
                        self._bot.total_ranks += gain_num
                    elif any(elem_name in gain_name for elem_name in exp):
                        self._bot.total_exp += gain_num
                    elif any(elem_name in gain_name for elem_name in pendants):
                        self._bot.total_pendants += gain_num

    def _convert_html_element_to_text(self, html_element):
        return str(html_element).strip(' \t\n')

    def _count_after_fight_event_items(self, event_item_element):
        gains = event_item_element.find_all('div', {'class': 'prt-event-point'})

        for gain in gains:
            if gain is not None:
                gain_name = str(gain.text)
                gain_num = self._convert_gain_to_int(gain_name)
                if 'tokens' in gain_name:
                    self._bot.total_tokens += gain_num
                elif 'honors' in gain_name:
                    self._bot.total_honors += gain_num
                elif 'pendants' in gain_name:
                    self._bot.total_pendants += gain_num

    def _extreme_fight(self):
        self._bot.wait.for_loading_screen()
        print('Waiting until you kill the boss...')

        # Wait until bot exits the current results screen
        while True:
            current_url = self._driver.current_url
            if '#result' not in current_url:
                break

        # Then wait until the boss has been killed and the bot is at results screen
        while True:
            current_url = self._driver.current_url
            if '#result' in current_url:
                self._bot.wait.for_loading_screen()
                print('You killed the boss!')
                self.after_fight_popups()
                self._bot.press.usual_event_home()
                self.after_fight_popups()
                print('Now re-select the quest.')
                break
            time.sleep(0.8)

    def human_verification(self):
        verification = self._bot.popup.human_verification()

        if verification is True:
            # Need to sleep this, because the captcha image takes time to load
            time.sleep(3)
            self._driver.save_screenshot('verification/screenshot.png')
            input_field = self._driver.find_element_by_class_name('frm-message')
            verification_code = input('Input verification code: ')
            input_field.send_keys(verification_code)
            time.sleep(1)
            self._driver.find_element_by_class_name('btn-talk-message').click()
            time.sleep(1)
            return True
