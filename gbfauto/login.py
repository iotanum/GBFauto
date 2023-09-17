import logging
import asyncio
import os

from dotenv import load_dotenv


_log = logging.getLogger(__name__)


class Login:
    """Login class for the GBF Auto"""

    def __init__(self, bot):
        """Initialize the Login class"""
        self.bot = bot.bot
        self.username = None
        self.password = None
        self.login_tab = None
        self.auth_page = "http://game.granbluefantasy.jp/#authentication"

    async def _set_credentials(self):
        load_dotenv("config.env")
        self.username = os.getenv("GBF_LOGIN")
        self.password = os.getenv("GBF_PASSWORD")

    async def _open_auth_page(self):
        _log.debug("Opening auth page...")
        await self.bot.goto(self.auth_page)

    async def _navigate_to_mobage_login(self):
        _log.debug("Navigating to mobage login...")
        async with self.bot.context.expect_page() as login_tab:
            await self.bot.locator('//*[@id="mobage-login"]/img').click()
        self.login_tab = await login_tab.value
        _log.debug("Navigated to mobage login!")

    async def _navigate_to_google_login(self):
        await self.login_tab.locator(
            '//*[@id="mobage-connect-analytics"]/div[1]/ul/li[4]/a'
        ).click()
        await asyncio.sleep(1)

    async def _enter_login(self):
        await self.login_tab.locator('//*[@id="identifierId"]').fill(self.username)
        await self.login_tab.keyboard.press("Enter")

    async def _enter_password(self):
        await self.login_tab.locator(
            '//*[@id="password"]/div[1]/div/div[1]/input'
        ).fill(self.password)
        await self.login_tab.keyboard.press("Enter")

    async def _press_mobage_thingy(self):
        await self.login_tab.locator('//*[@id="notify-response-button"]/div').click()
        await self.bot.wait_for_load_state()

    async def login(self):
        """Login to the game"""
        _log.info("Logging in...")

        await self._set_credentials()
        await self._open_auth_page()
        await self._navigate_to_mobage_login()
        await self._navigate_to_google_login()
        await self._enter_login()
        await self._enter_password()
        await self._press_mobage_thingy()
        _log.info("Logged in!")
