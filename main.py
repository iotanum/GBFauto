from helpers.login import GBFGame
from gbf.quest_on_repeat import QuestOnRepeat

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

gbf_login = os.getenv("GBF_LOGIN")
gbf_password = os.getenv("GBF_PASSWORD")

options = {1: "Repeatable Quest"}


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
        print("\t", f"{option_num}. {option_name}.")

    option_num = input("Option: ")
    option_num = int(option_num)

    return option_num, menu[option_num]


def pick_option():
    print("\nWaiting for your input...")
    try:
        option_num, option = print_menu(options)

        return option

    except (ValueError, KeyError):
        return None


def force_kill_chromedriver():
    game_handler.driver.close()
    print("closed gamehandler")
    try:
        finder_handler.driver.close()
        print("closed finder")
    except:
        pass

    # Shell command to force kill chromedriver.exe process
    # returns string output from my command
    check_output("TASKKILL /IM chromedriver.exe /F", shell=True)


def choose_option():
    option = pick_option()
    viable_options = ["Repeatable Quest"]

    try:
        if option in viable_options:
            if option == "Repeatable Quest":
                questing_handler = QuestOnRepeat(game_handler)
                questing_handler.repeatable_quest()

            # After choosing an option the 'real' bot start time is assigned
            game_handler._start_time = time.time()
        else:
            print("\nWrong option! Try again...")
            choose_option()

    except Exception as e:
        log_failure()
        exit_application(e)


def log_failure():
    timestamp = str(datetime.now()).replace(":", "'")[:-7]
    game_handler.driver.save_screenshot(f"errors/{timestamp}.png")
    with open(f"errors/{timestamp} source_code.html", "w", encoding="utf-8") as file:
        file.write(game_handler.driver.page_source)


def exit_application(e):
    force_kill_chromedriver()
    sys.exit(traceback.format_exc(e))


if __name__ == "__main__":
    game_handler = game()
    # Headless chrome options resizes default window size

    choose_option()
