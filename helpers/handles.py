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
SUPPORT_SUMMONS = os.getenv('SUPPORT_SUMMONS_TO_PICK')


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
                    time.sleep(1.5)
                    break
                time.sleep(0.5)

        popup_search_start = time.time()
        # Just a declaration for a placeholders
        exp_popup = False
        mc_gauge = None
        team_gauges = None
        timer_assigned = False

        while True:
            parser = bs(self._driver.page_source, 'lxml')

            popup = parser.find('div', {'class': ['pop-show']})
            party = parser.find('div', {'class': 'prt-party'})

            # Loot 'window' is a styled element that is displayed after first popups
            # after the fight
            loot = parser.find('div', {'class': 'cnt-get-treasure', 'style': 'display: block;'})
            if loot and timer_assigned is False:
                loot_appear_time = time.time()
                timer_assigned = True

            # Same as 'loot' variable, but a literal mask on top of the page
            # needed for lvl-up checks
            main_mask = parser.find('div', {'class': 'mask', 'style': 'display: none;'})

            current_url = self._driver.current_url

            # Ignore 'Not enough AP/EP' popup for now.
            # Also this popup appears last, so we need to exit
            if popup is not None and 'pop-stamina' in popup['class']:
                break

            # For raids
            # If bot didn't manage to get any hits on the boss
            # It returns to an empty quest screen after the fight
            if 'empty' in current_url:
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
            if loot and kill is True and time.time() - loot_appear_time >= 1:
                self._bot.total_fights += 1
                time.sleep(0.5)
                break

            # If your main character/team character gains a level/multiple levels
            # the game holds it's popups until the 'level gauge' finishes it's
            # animations until it's at it's gained level
            # so it needs to be handled.
            # If changes in any of the gauges are found - reset the popup timer.
            # Also don't need to check for changes if kill is False
            # Because every lvl-up is displayed BEFORE loot element
            # meaning the 'first' burst of popups
            if main_mask and kill is True and exp_popup is True:
                # Main 'level' elements
                mc_lvl_elem = party.find('div', {'class': 'prt-player-exp'})
                team_lvl_elem = party.find('div', {'class': 'prt-party-npc'})

                # It's exact percentages
                mc_lvl_xp_percentage = mc_lvl_elem.find('div', {'class': 'prt-exp-gauge-inner-new'})['style']
                team_lvl_xp_percentages = team_lvl_elem.find_all('div', {'class': 'prt-exp-gauge-inner-new'})

                # Also, since team gauges are a list (find_all func)
                # it needs a list comp to get it's elements style
                team_lvl_xp_percentages = [elem['style'] for elem in team_lvl_xp_percentages]

                # Now extract the percentage/s number from a string
                mc_lvl_xp_percentage = self._convert_gain_to_int(mc_lvl_xp_percentage)
                team_lvl_xp_percentages = [self._convert_gain_to_int(percentage) for percentage in team_lvl_xp_percentages]

                # And now the actual check if it changed or not
                if mc_lvl_xp_percentage != mc_gauge:
                    # If this goes through - reset the timer (wait until the animations are done)
                    mc_gauge = mc_lvl_xp_percentage
                    popup_search_start = time.time()

                if team_lvl_xp_percentages != team_gauges:
                    team_gauges = team_lvl_xp_percentages
                    popup_search_start = time.time()

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
                    exp_popup = True
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
                    night_boss_name = popup.find('div', {'class': "btn-usual-next"})
                    night_boss_name = night_boss_name['data-chapter-name']
                    print(f"'{night_boss_name}' nightmare battle!")
                    if EXTREME_BATTLES == 1:
                        try:
                            self._bot.press.usual_next()
                            self._extreme_fight()
                            return True
                        except selenium_err.exceptions.NoSuchElementException:
                            pass
                    else:
                        self._bot.press.usual_close()

                elif any(name in popup_name for name in ['mission-check', 'update-beginner-mission-teamraid']):
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
                    item_img_url = popup.find('img', {'class': 'img-newitem'})['src']
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

                elif 'get-ability' in popup_name:
                    popup_header = popup.find('div', {'class': 'prt-popup-header'}).text
                    print(f"{popup_header}")
                    self._bot.press.usual_ok()

                elif 'get-support-ability' in popup_name:
                    ability_text = popup.find('div', {'class': 'txt-ability'}).text
                    print(f"New support ability!\n'{ability_text}''")
                    self._bot.press.usual_ok()

                elif 'skin-open' in popup_name:
                    skin_text = popup.find('div', {'class': 'txt-popup-body'}).text
                    print(skin_text)
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

        # Wait until URL changes into the battle one
        while True:
            current_url = self._driver.current_url
            if 'quest/stage' in self._driver.current_url:
                break

            if 'raid' in current_url:
                break

        while True:
            popup_search_time = time.time()

            # For slower internet speeds if bot is taking longer than usual to
            # load - reset the start timer while in quest/stage page
            if 'quest/stage' in self._driver.current_url:
                popup_search_start = time.time()

            # A fail-safe to exit the loop if there is not side-scroll mini event
            if 'raid' in current_url:
                break

            if popup_search_time - popup_search_start > 5:
                break

            parser = bs(self._driver.page_source, 'lxml')

            side_scroll_quest = parser.find('div', class_='pop-usual pop-skip-result pop-show')

            # Also search for 'quest progression' animation elements
            # That means that there is no side-scrolling mini event
            # in the quest
            try:
                progress_bar = parser.find('div', {'class': 'prt-position'})
                quest_parts = progress_bar.find_all('div', {'class': ['lis-spot']})
            except AttributeError:
                quest_parts = None

            if quest_parts:
                break

            if side_scroll_quest:
                # The second element is what we need
                ok_buttons = self._driver.find_elements_by_class_name('btn-usual-ok')

                ok_button = ok_buttons[1]
                ok_button.click()
                break

                # Will need this later
                # self._bot.press.usual_skip()
                # self._bot.popup.skip_side_scroll()
                # self._driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div[2]').click()
                # self._bot.popup.side_scroll_results()
                # self._driver.find_element_by_xpath('//*[@id="pop"]/div/div[3]/div').click()

    def pre_fight_popup(self, instruction_to_run):
        popup_search_start = time.time()

        while True:
            popup_search_time = time.time()

            if popup_search_time - popup_search_start > 2:
                # If there was a pre-fight popup, need to return a bool
                # and handle it appropriately (ex.: repeat last instruction)
                break

            if self._bot.raid_battle is False:
                break

            parser = bs(self._driver.page_source, 'lxml')
            popup = parser.find('div', {'class': ['common-pop-error']})

            current_url = self._driver.current_url

            # Conditions to exit popup detection loop
            # Picking support summon element doesn't need popup detection
            if instruction_to_run == 'support_element':
                break

            # Exit loop if after picking support summon the support confirmation 'popup' appeared
            elif instruction_to_run == 'pick_summon':
                supp_ele = parser.find(class_='pop-deck supporter',
                                       style_='display: block; top: 0px; margin-bottom: 0px;')
                if supp_ele:
                    break

            # Exit loop if after confirming support summon the URL has changed
            elif instruction_to_run == 'confirm_support':
                if 'quest/supporter' not in current_url:
                    break

            # Exit loop if after entering ID the URL has changed
            elif instruction_to_run == 'pre_summon_pick':
                if 'quest/supporter' in current_url:
                    break

            if popup:
                popup_search_start = time.time()

                # Needed to distinguish between verification/typical error popups
                popup_header = str(popup.find('div', {'class': 'prt-popup-header'}).text)

                if 'Battle' in popup_header:
                    self._bot.press.usual_ok()
                    return True

                elif 'Access Verification' in popup_header:
                    self.human_verification()
                    return 'verification'

    def pre_fight_support_summons(self):
        self._bot.wait.for_loading_screen()

        instructions_to_run = {'support_element': self._bot.press.support_element,
                               'pick_summon': self._bot.press.support_summon,
                               'confirm_summon': self._bot.press.confirm_support_summon}

        instruction_to_run = 'support_element'

        while True:
            # Execute the instruction
            if instruction_to_run == 'support_element':
                instructions_to_run[instruction_to_run](SUPPORT_ELEMENT)

            if instruction_to_run == 'pick_summon':
                support_summon_id = self.get_best_support_summon()

                if support_summon_id:
                    support_summon_id = support_summon_id['ID']
                    instructions_to_run[instruction_to_run](supporter_id=support_summon_id,
                                                            support_element_num=SUPPORT_ELEMENT)
                else:
                    instructions_to_run[instruction_to_run](support_element_num=SUPPORT_ELEMENT, first_summon=True)

            if instruction_to_run == 'confirm_summon':
                instructions_to_run[instruction_to_run]()

            # Then check for popups/verification and handle accordingly
            popup = self.pre_fight_popup(instruction_to_run)
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
            time.sleep(0.15)

    def parse_support_summon_list(self):
        parser = bs(self._driver.page_source, features='lxml')

        for element in parser.find_all('div', {'class': 'prt-supporter-attribute'}):
            # In page source currently picked support element list
            # contains only 1 attribute (usually)
            if len(element['class']) == 1:
                support_summon_list = element
                break
            # Also check if there's an attribute called "typeX" X being the
            # number of an element in game
            # If there's a 'type' attr in given element - it usually means
            # current support summon page is within an event
            elif len(element['class']) == 2 and 'type' in str(element['class'][1]):
                support_summon_list = element
                break

        # Extract actual support summons from the above found element
        support_summons = support_summon_list.find_all('div', class_='btn-supporter lis-supporter')

        support_summon_dict = {}

        for idx, support_summon in enumerate(support_summons):
            supporter_id = support_summon['data-supporter-user-id']
            support_name = support_summon.find('div', {'class': 'prt-supporter-summon'}).text.strip()
            skill_level = support_summon.find('div', {'class': ['prt-summon-skill']})
            # Sk level class consists of 3 styles, thus the magic number.
            # 3rd style is what I need, it consists of style used to display the skill level of
            # the summon
            skill_level = str(skill_level['class'][2] if len(skill_level['class']) == 3 else 0)
            friend_summon = support_summon.find('div', {'class': 'ico-friend'})

            # Extract summon level, name, and if it is a friend summon
            placeholder_lvl, support_summon_lvl, *support_summon_name = support_name.split()

            # *support_summon_name is a wildcard so slap everything together to get the full support summon name
            support_summon_name = ' '.join(support_summon_name)

            support_summon_dict[idx] = {}
            support_summon_dict[idx]['Name'] = support_summon_name
            support_summon_dict[idx]['SkLvl'] = int(re.findall('\d+', skill_level)[0])
            support_summon_dict[idx]['ID'] = int(supporter_id)
            support_summon_dict[idx]['Friend'] = True if friend_summon else False

        return support_summon_dict

    def parse_from_config_summons(self):
        support_summons_from_config = SUPPORT_SUMMONS.split(', ')

        return support_summons_from_config

    def get_best_support_summon(self):
        supp_summon_dict = self.parse_support_summon_list()

        summons_from_config = self.parse_from_config_summons()

        # First element of parsed summons from config shouldn't contain an empty string
        # if it does - it means that the user didn't specify what summon to prioritize
        if summons_from_config[0] == '':
            return None

        print(supp_summon_dict, "<- Whole summon list.")
        needed_summons = {}
        priority, non_priority = summons_from_config
        search_for = priority.lower()
        found = False
        final_summ_pick = {'SkLvl': 1}
        MIN_SKLEVEL_THRESHOLD = 1

        while found is False:
            if len(needed_summons) < 1:
                for idx, summon in enumerate(supp_summon_dict.values(), 1):
                    if search_for in summon['Name'].lower() and summon['SkLvl'] >= MIN_SKLEVEL_THRESHOLD:
                        print(summon, '<- This goes into the "found" list.')
                        needed_summons[idx] = summon

                    if idx == len(supp_summon_dict):
                        # If there's at least 1 summon found - return
                        if len(needed_summons) >= 1:
                            break
                        # If already went through both priority and non and still
                        # found nothing - return
                        elif search_for == non_priority:
                            print(f"'{non_priority}' was also not found. Picking first given summon on the list.")
                            return None
                        # If went through priority and didn't go through non-priority
                        # - try that
                        else:
                            print(f"'{priority}' summon was not found.")
                            search_for = non_priority.lower()

                for idx, summon in enumerate(needed_summons.values(), 1):
                    if True in [summon['Friend'] is True for summon in needed_summons.values()]:
                        if summon['SkLvl'] >= final_summ_pick['SkLvl'] and summon['Friend'] is True:
                            final_summ_pick = summon
                    else:
                        if summon['SkLvl'] >= final_summ_pick['SkLvl']:
                            final_summ_pick = summon

                    if idx == len(needed_summons):
                        print(final_summ_pick, '<- Picking this.')
                        found = True
                        break

        return final_summ_pick

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

    def not_enough_of_x(self, timeout=3):
        start = time.time()

        while True:
            current_url = self._driver.current_url

            # Exit loop if in 'Pick support summon' page
            if time.time() - start > timeout or '#quest/supporter' in current_url or '#raid' in current_url:
                break

            parser = bs(self._driver.page_source, 'lxml')

            ap_ep_popup = parser.find('div', class_='pop-usual pop-stamina pop-show')
            various_popup = parser.find('div', {'class': ['common-pop-error']})

            if ap_ep_popup:
                ap_ep_amount = random.randint(3, 5)
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
