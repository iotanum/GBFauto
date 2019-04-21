from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import common as selenium_err

import sys
import time

from bs4 import BeautifulSoup as bs


class RaidFinder:
    def __init__(self):
        self.chrome_options = Options()
        self.headless_chrome()
        self.driver = webdriver.Chrome(executable_path='utils/chromedriver.exe', options=self.chrome_options)
        self.raid_finder_url = "https://gbf-raidfinder.aikats.us/"
        self.raid = []
        self.old_raid_id = 'baton'
        self.window_already_closed = False
        self.launched = True
        self.set_up()

    def headless_chrome(self):
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")

    def set_up(self):
        self.driver.get(self.raid_finder_url)

        try:
            elem = self.driver.find_element_by_css_selector('.mdl-button--fab')
            self.handle_clicks(elem)
        except selenium_err.exceptions.NoSuchElementException:
            sys.exit("It seems that 'Granblue Raid Finder' site is down, try again later.")

    def click_on_raid(self):
        try:
            if self.window_already_closed is False:
                elem = self.driver.find_element_by_xpath(f"// *[text()[contains(., '{self.raid_name}')]]")
                self.handle_clicks(elem)
                close_elem = self.driver.find_element_by_css_selector('.js-close-dialog')
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
        found = False
        start_time = time.time()

        print(f"Searching for '{self.raid_name}'...")
        while found is False:
            # It likes to hang for some reason ?
            if time.time() - start_time > 30 and len(self.raid) < 2:
                self.driver.refresh()
                start_time = time.time()

            # wait for the list to update itself to get the most recent raid
            soup = bs(self.driver.page_source, features='lxml')

            raid = soup.find('li', {'data-raidid': True})
            raid_id = raid['data-raidid']

            if self.old_raid_id != raid_id:
                self.raid.insert(1, raid_id)
                self.old_raid_id = raid_id
            elif len(self.raid) == 2:
                found = True

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
        self.raid = []
        self.raid.insert(0, self.old_raid_id)

    def handle_clicks(self, element):
        if element.is_displayed():
            element.click()
        else:
            print("?")
