from selenium import common as selenium_err
from selenium.webdriver.support.ui import WebDriverWait


class Timeout:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_element(self, timeout, expected_behaviour, search_by, element_name):
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(expected_behaviour((search_by, element_name)))
            return True
        except selenium_err.exceptions.TimeoutException:
            # except , selenium_err.exceptions.WebDriverException
            return False
