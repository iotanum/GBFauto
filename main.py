from helpers.raid_finder import RaidFinder
from helpers.login import GBFGame
from gbf.raids import Raids
from gbf.slimes import Slimes
from gbf.gw import GW

from dotenv import load_dotenv

import os
import sys
import traceback
import logging
from datetime import datetime


logger = logging.getLogger()
logger.propagate = False

config = load_dotenv(dotenv_path='config.env')
gbf_login = os.getenv('GBF_LOGIN')
gbf_password = os.getenv('GBF_PASSWORD')
raid_boss_name = os.getenv('RAID_BOSS_NAME')

options = {1: 'Raids',
           2: 'Slime Blast',
           3: 'GW'}


def game():
    game_handler = GBFGame()
    game_handler.login(gbf_login, gbf_password)
    return game_handler


def print_menu(menu):
    for option_num, option_name in menu.items():
        print('\t', f"{option_num}. {option_name}.")

    option_num = input('Option: ')
    option_num = int(option_num)

    return option_num, menu[option_num]


def pick_option():
    print('\nWaiting for your input...')
    option_num, option = print_menu(options)

    return option


def gw_sub_options():
    sub_options = {1: 'Cybele (Hard)',
                   2: 'EX (Normal)',
                   3: 'Dimorphodon (Easiest)'}

    print('\nPick your GW raid...')
    sub_option_num, sub_option = print_menu(sub_options)

    # Cybele doesn't have a difficulty
    if sub_option != 'Cybele (Hard)':
        sub_option_diff_dimorphodon={1: 'Normal',
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


if __name__ == '__main__':
    game_handler = game()
    option_num = pick_option()
    try:
        if option_num == 'Raids':
            finder_handler = RaidFinder()
            bot = Raids(game_handler.driver, finder_handler)
            bot.set_raid_name(raid_boss_name)
            bot.raids()
        elif option_num == 'Slime Blast':
            slime_handler = Slimes(game_handler)
            slime_handler.slime_blast()
        elif option_num == 'GW':
            raid_type_num, raid_type, raid_diff_num, raid_diff = gw_sub_options()
            gw_handler = GW(game_handler)
            gw_handler.gw(raid_type_num, raid_type, raid_diff_num, raid_diff)
    except Exception as e:
        timestamp = str(datetime.now()).replace(":", "'")[:-7]
        game_handler.driver.save_screenshot(f'errors/{timestamp}.png')
        with open(f'errors/{timestamp} source_code.html', 'w', encoding='utf-8') as file:
            file.write(game_handler.driver.page_source)
        try:
            game_handler.driver.close()
            print('closed gamehandler')
            finder_handler.driver.close()
            print('closed finder')
        except:
            pass
        sys.exit(traceback.format_exc(e))
    else:
        sys.exit("Wrong option!")
