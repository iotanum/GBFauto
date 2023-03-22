from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import common as selenium_err
from selenium.webdriver.common.keys import Keys

import sys
import time

from bs4 import BeautifulSoup as bs


class RaidFinder:
    def __init__(self):
        self.chrome_options = Options()
        self.headless_chrome()
        self.driver = webdriver.Chrome(executable_path='utils/chromedriver.exe', options=self.chrome_options)
        self.raid_finder_url = "https://gbf-raidfinder.la-foret.me/"
        self.raid = []
        self.window_already_closed = False
        self.launched = True
        self.set_up()

    def headless_chrome(self):
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")

    def set_up(self):
        # initialize selenium
        self.driver.get(self.raid_finder_url)

        try:
            elem = self.driver.find_element(By.CSS_SELECTOR, '.mdl-button--fab')
            self.handle_clicks(elem)
        except selenium_err.exceptions.NoSuchElementException:
            sys.exit("It seems that 'Granblue Raid Finder' site is down, try again later.")

    def wait_for_element(self, search_by, element_name):
        try:
            wait = WebDriverWait(self.driver, 5)
            wait.until(EC.visibility_of_element_located((search_by, element_name)))
            return True
        except selenium_err.exceptions.TimeoutException:
            return False

    def click_on_raid(self):
        try:
            if self.window_already_closed is False:
                elem = self.driver.find_element(By.XPATH, f"// *[text()[contains(., '{self.raid_name}')]]")
                self.handle_clicks(elem)
                close_elem = self.driver.find_element(By.CSS_SELECTOR, '.js-close-dialog')
                self.handle_clicks(close_elem)
                self.window_already_closed = True
                self.launched = False
                self.driver.refresh()
            self.parse_for_ids()

        except AttributeError:
            print('Please set the raid name!')
            sys.exit()

    def parse_for_ids(self):
        self.wait_fo_ids()
        start_time = time.time()

        print(f"Searching for '{self.raid_name}'...")
        while True:
            # It likes to hang for some reason ?
            if time.time() - start_time >= 30:
                # Ghetto refresh smh
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.F5)
                self.wait_for_element(By.XPATH, '//*[@id="gbfrf-dialog__follow"]/ul/li[1]/span/span[2]')
                start_time = time.time()

            # wait for the list to update itself to get the most recent raid
            soup = bs(self.driver.page_source, features='lxml')

            raid = soup.find('li', {'data-raidid': True})
            raid_id = raid['data-raidid']

            if self.raid[0] != raid_id:
                self.raid.insert(1, raid_id)

            if len(self.raid) == 2:
                break

    def wait_fo_ids(self):
        wait = WebDriverWait(self.driver, 3)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.gbfrf-js-tweet')))

    def get_raid(self, raid_name):
        self.raid_name = raid_name
        self.clean_raid_var()
        if self.launched is True:
            self.click_on_raid()
        else:
            self.parse_for_ids()
        rid = list(self.raid)[-1]
        print(f"Trying '{rid}'...")
        return rid

    def clean_raid_var(self):
        # Try/Except for the initial RaidFinder launch
        # placeholder variable
        try:
            # Change 1st element index to 0 and remove it
            self.raid.insert(0, self.raid[1])
            del self.raid[1:]
        except IndexError:
            self.raid.insert(0, '12345678')

    def handle_clicks(self, element):
        if element.is_displayed():
            element.click()
        else:
            print("?")
