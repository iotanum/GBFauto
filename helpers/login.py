from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import common as selenium_err

from helpers.buttons import Press
from helpers.screens import Wait
from helpers.popups import Popup
from helpers.skill_queue import Skills
from helpers.actions import Action
from helpers.handles import Handle

import time
import os
import ctypes

from dotenv import load_dotenv

load_dotenv('config.env')

HEADLESS_MODE = int(os.getenv('HEADLESS_MODE'))
MANUAL_LOGIN = int(os.getenv('MANUAL_LOGIN'))


class GBFGame:
    started = False

    def __init__(self):
        self.chrome_options = Options()
        self.custom_chrome_options()
        self.driver = webdriver.Chrome(executable_path='utils/chromedriver.exe', options=self.chrome_options)
        self.login_page = "http://game.granbluefantasy.jp/#authentication"
        self._start_time = time.time()
        self.press = Press(self)
        self.wait = Wait(self)
        self.popup = Popup(self)
        self.action = Action(self)
        self.queue = Skills(self)
        self.handle = Handle(self)
        ##############################################
        self.total_ranks = 0
        self.total_exp = 0
        self.total_tokens = 0
        self.total_honors = 0
        self.total_pendants = 0
        self.total_fights = 0
        self.raid_battle = False
        #############################################
        self.option_repeatable = False
        self.current_ap = None
        self.quest_cost = None
        self.need_ap = False
        self.refreshed = False
        self.point_threshold = os.getenv('POINT_THRESHOLD')

    def run_time(self):
        return time.time() - self._start_time

    def custom_chrome_options(self):
        # Resize chrome window on smaller screens (otherwise chrome driver crashes?)
        if self.get_screen_resolution() == [1366, 768]:
            self.chrome_options.add_argument("--window-size=500,720")

        self.chrome_options.add_argument("--mute-audio")

    def get_screen_resolution(self):
        user32 = ctypes.windll.user32
        screen_resolution = [int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))]

        return screen_resolution

    def handle_click(self, element):
        if element.is_displayed():
            element.click()
        else:
            print('?')

    def wait_for_google_login(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-google.w-max')))

    def wait_for_gbf_login(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-auth-login')))

    def press_login(self):
        self.wait_for_gbf_login()
        elem = self.driver.find_element_by_class_name('btn-auth-login')
        self.handle_click(elem)

    def wait_for_title_change(self):
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.title_is("Mobage Connect"))

    def wait_for_window_switch(self):
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.number_of_windows_to_be(2))

    def switch_to_mobage_window(self):
        self.wait_for_window_switch()
        time.sleep(2)
        while 'mobage' not in str(self.driver.current_url):
            try:
                mobage_window = self.driver.window_handles[1]
                self.driver.switch_to.window(mobage_window)
            except (selenium_err.exceptions.NoSuchWindowException, IndexError):
                pass
        if str(self.driver.title) is not "Mobage Connect":
            self.driver.refresh()

    def press_google_login(self):
        self.switch_to_mobage_window()
        self.wait_for_google_login()
        elem = self.driver.find_element_by_css_selector('.btn-google.w-max')
        self.handle_click(elem)

    def wait_for_email(self):
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.element_to_be_clickable((By.NAME, 'identifier')))

    def wait_for_password(self):
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')))

    def enter_login_email(self, login, password):
        self.wait_for_email()
        form_email = self.driver.find_element_by_name('identifier')
        form_email.send_keys(login)
        time.sleep(0.5)
        self.driver.find_element_by_xpath('//*[@id="identifierNext"]').click()
        self.wait_for_password()
        form_password = self.driver.find_element_by_xpath('//*[@id="password"]/div[1]/div/div[1]/input')
        form_password.send_keys(password)
        time.sleep(0.5)
        self.driver.find_element_by_xpath('//*[@id="passwordNext"]').click()

    def switch_window_to_gbf(self):
        gbf_window = self.driver.window_handles[0]
        self.driver.switch_to.window(gbf_window)

    def handle_manual_login(self):
        input("Type 'yes' when you're done: ")

    def wait_for_main_menu_page(self):
        while True:
            url = str(self.driver.current_url)
            if '#mypage' in url:
                break

    def login(self, login, password):
        if GBFGame.started is False:
            self.driver.get(self.login_page)
            GBFGame.started = True
            print("Logging in w/ Google+ log-in method.")
            self.press_login()
            if MANUAL_LOGIN is 1:
                self.handle_manual_login()
            else:
                self.press_google_login()
                self.enter_login_email(login, password)
            self.switch_window_to_gbf()
            self.wait_for_main_menu_page()
            self.wait.for_loading_screen()
            print("Successfuly logged-in!")
