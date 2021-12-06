from helpers.raid_finder import RaidFinder
from helpers.login import GBFGame
from gbf.raids import Raids
from gbf.special_quests import SpecialQuests
from gbf.gw import GW
from gbf.quest_on_repeat import QuestOnRepeat

from dotenv import load_dotenv
import selenium
from selenium import common

import os
import sys
import traceback
import logging
import time
from datetime import datetime
from subprocess import check_output


logger = logging.getLogger()
logger.propagate = False

config = load_dotenv(dotenv_path='config.env')
gbf_login = os.getenv('GBF_LOGIN')
gbf_password = os.getenv('GBF_PASSWORD')
raid_boss_name = os.getenv('RAID_BOSS_NAME')
headless = os.getenv('HEADLESS_MODE')

options = {1: 'Raids',
           2: 'Special Quests',
           3: 'GW',
           4: 'Repeatable Quest'}


def game():
    try:
        game_handler = GBFGame()
        game_handler.login(gbf_login, gbf_password)
        return game_handler
    except selenium.common.exceptions.SessionNotCreatedException:
        chromedriver_dl_link = "https://chromedriver.chromium.org/downloads"
        sys.exit(f"Chromedriver is outdated - update it!\n{chromedriver_dl_link}")

def print_menu(menu):
    for option_num, option_name in menu.items():
        print('\t', f"{option_num}. {option_name}.")

    option_num = input('Option: ')
    option_num = int(option_num)

    return option_num, menu[option_num]


def pick_option():
    print('\nWaiting for your input...')
    try:
        option_num, option = print_menu(options)

        return option

    except (ValueError, KeyError):
        return None


def gw_sub_options():
    sub_options = {1: 'Cybele (Hard)',
                   2: 'EX (Normal)',
                   3: 'Dimorphodon (Easiest)'}

    print('\nPick your GW raid...')
    sub_option_num, sub_option = print_menu(sub_options)

    # Cybele doesn't have a difficulty
    if sub_option != 'Cybele (Hard)':
        sub_option_diff_dimorphodon = {1: 'Normal',
                                       2: 'Hard',
                                       3: 'Very Hard'}

        sub_option_diff_ex = {1: 'Very Hard',
                              2: 'Extreme',
                              3: 'Extreme+'}

        print(f"\nDifficulty for '{sub_option}'...")
        if sub_option == 'Dimorphodon (Easiest)':
            sub_option_diff_num, sub_option_diff = print_menu(sub_option_diff_dimorphodon)
        elif sub_option == 'EX (Normal)':
            sub_option_diff_num, sub_option_diff = print_menu(sub_option_diff_ex)
    else:
        sub_option_diff_num = None
        sub_option_diff = None

    return sub_option_num, sub_option, sub_option_diff_num, sub_option_diff


def special_quest_sub_options():
    print("\nPick your treasure quest..")
    sub_options = {1: 'Basic Treasure Quests',
                   2: 'Shiny Slime Search!',
                   3: 'Six-Dragon Trial (not working)',
                   4: 'Elemental Treasure Quests',
                   5: 'Showdowns (not working)',
                   6: 'Angel Halo'}

    sub_option_num, sub_option = print_menu(sub_options)

    if sub_option_num == 1:
        sub_options_btq = {1: 'Scarlet Trial',
                           2: 'Cerulean Trial',
                           3: 'Violet Trial'}

        sub_option_diff_num, sub_option_diff = print_menu(sub_options_btq)

        sub_options_btq_diffs = {1: 'Normal',
                                 2: 'Hard',
                                 3: 'Very Hard'}

        sub_option_inner_diff_num, sub_option_inner_diff = print_menu(sub_options_btq_diffs)

    elif sub_option_num == 2:
        sub_options_sss = {1: 'Easy',
                           2: 'Hard',
                           3: 'Very Hard'}

        sub_option_diff_num, sub_option_diff = print_menu(sub_options_sss)

    elif sub_option_num == 4:
        sub_options_etq = {1: 'The Hellfire Trial',
                           2: 'The Deluge Trial',
                           3: 'The Wasteland Trial',
                           4: 'The Typhoon Trial',
                           5: 'The Aurora Trial',
                           6: 'The Oblivion Trial'}

        sub_option_diff_num, sub_option_diff = print_menu(sub_options_etq)

    elif sub_option_num == 6:
        sub_options_ah = {1: 'Normal',
                          2: 'Hard',
                          3: 'Very Hard'}

        sub_option_diff_num, sub_option_diff = print_menu(sub_options_ah)

    # TODO
    # Needs some work
    # This is for quests where it's div tree looks like:
    # Quest -> Inner Quest -> Inner Quest diff
    # 'Considered Default' tree is:
    # Quest -> Quest diff
    sub_options_with_inner_diffs = [1]

    if sub_option_num not in sub_options_with_inner_diffs:
        sub_option_inner_diff_num = None
        sub_option_inner_diff = None

    return sub_option_num, sub_option, sub_option_diff_num, sub_option_diff, \
           sub_option_inner_diff_num, sub_option_inner_diff


def force_kill_chromedriver():
    game_handler.driver.close()
    print('closed gamehandler')
    try:
        finder_handler.driver.close()
        print('closed finder')
    except:
        pass

    # Shell command to force kill chromedriver.exe process
    # returns string output from my command
    check_output('TASKKILL /IM chromedriver.exe /F', shell=True)


def choose_option():
    option = pick_option()
    viable_options = ['Raids', 'Special Quests', 'GW', 'Repeatable Quest']

    try:
        if option in viable_options:
            if option == 'Raids':
                finder_handler = RaidFinder()
                raid_handler = Raids(game_handler, finder_handler)
                raid_handler.set_raid_name(raid_boss_name)
                raid_handler.raids()

            elif option == 'Special Quests':
                sub_option_num, sub_option, sub_option_diff_num, sub_option_diff, \
                sub_option_inner_diff_num, sub_option_inner_diff = special_quest_sub_options()
                special_quest_handler = SpecialQuests(game_handler)
                special_quest_handler.special_quests(sub_option_num, sub_option, sub_option_diff_num, sub_option_diff)

            elif option == 'GW':
                raid_type_num, raid_type, raid_diff_num, raid_diff = gw_sub_options()
                gw_handler = GW(game_handler)
                gw_handler.gw(raid_type_num, raid_type, raid_diff_num, raid_diff)

            elif option == 'Repeatable Quest':
                questing_handler = QuestOnRepeat(game_handler)
                questing_handler.repeatable_quest()

            # After choosing an option the 'real' bot start time is assigned
            game_handler._start_time = time.time()
        else:
            print('\nWrong option! Try again...')
            choose_option()

    except Exception as e:
        log_failure()
        exit_application(e)


def log_failure():
    timestamp = str(datetime.now()).replace(":", "'")[:-7]
    game_handler.driver.save_screenshot(f'errors/{timestamp}.png')
    with open(f'errors/{timestamp} source_code.html', 'w', encoding='utf-8') as file:
        file.write(game_handler.driver.page_source)


def exit_application(e):
    force_kill_chromedriver()
    sys.exit(traceback.format_exc(e))


if __name__ == '__main__':
    game_handler = game()
    # Headless chrome options resizes default window size

    choose_option()
