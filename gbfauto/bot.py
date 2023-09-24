import logging

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from gbfauto.events import Events
from gbfauto.login import Login
from gbfauto.gbf.questing import Questing


_log = logging.getLogger(__name__)

BROWSER_OPTIONS = {
    "headless": False,
}
CONTEXT_OPTIONS = {
    "viewport": {"width": 560, "height": 760},
}

_log.debug(f"Engine configuration: {BROWSER_OPTIONS}, {CONTEXT_OPTIONS}")


class Bot:
    def __init__(self):
        self.bot = None
        self.context = None
        self.events = None
        self.login = None
        self.questing = None
        self.responses = None

    async def start_events(self):
        self.events = Events(self)
        await self.events.initialize_events()

    async def initialize_engine(self):
        _log.debug("Launching engine...")
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(**BROWSER_OPTIONS)
        self.context = await browser.new_context(**CONTEXT_OPTIONS)
        self.bot = await self.context.new_page()
        await stealth_async(self.bot)
        _log.debug("Engine launched!")

    async def initialize_login(self):
        self.login = Login(self)
        await self.login.login()
        _log.debug("Login initialized!")

    async def initialize_questing(self):
        self.questing = Questing(self)
        await self.questing.wait_for_repeatable_quest()
        _log.debug("Questing initialized!")

    async def run(self):
        await self.initialize_engine()
        await self.start_events()
        await self.initialize_login()
        await self.initialize_questing()
