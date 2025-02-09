import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import playwright
from playwright.async_api import Error

from bs4 import BeautifulSoup as bs4

_log = logging.getLogger(__name__)


class Utils:
    def __init__(self, bot):
        self.bot = bot
        self.events = self.bot.events
        self.executor = ThreadPoolExecutor()

    async def get_page_content(self):
        return await self.bot.page.content()

    async def go_to_main(self):
        await self.bot.page.goto("https://game.granbluefantasy.jp/#mypage")
        await self.bot.page.wait_for_load_state()

    async def go_to_url(self, url, ele=None, retries=3, delay=2):
        for attempt in range(retries):
            try:
                _log.debug(f"Attempt {attempt + 1}: Going to url: '{url}'")
                await self.bot.page.goto(url)
                await self.bot.page.wait_for_url(url)

                if ele:
                    _log.debug(f"After going to '{url}', waiting for element: '{ele}'")
                    await self.bot.page.wait_for_selector(
                        ele, timeout=10000
                    )  # 10s timeout

                return

            except Exception as e:
                _log.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
                else:
                    _log.error(f"Failed to go to {url} after {retries} attempts")
                    raise

    async def go_to_locked_quest(self):
        await self.bot.page.goto(self.bot.questing.quest_url)

    async def get_current_url(self):
        try:
            return await self.bot.page.evaluate("window.location.href")
        except playwright._impl._errors.Error:
            return ""

    async def is_in_result_screen(self):
        current_url = await self.get_current_url()
        return "result" in current_url

    async def click(self, ele, force=False, timeout=5):
        xpath = await get_xpath_from_ele(ele)
        _log.debug(f"Clicking on element: {xpath}")
        await self.bot.page.locator(xpath).click(force=force, timeout=timeout * 1000)

    async def bs(self, content=None, parser=None, find=(), find_all=()):
        loop = asyncio.get_event_loop()

        if content is None:
            content = await self.get_page_content()

        if parser is None:
            parser = await loop.run_in_executor(self.executor, bs4, content, "lxml")

        if find:
            return await loop.run_in_executor(self.executor, parser.find, *find)

        if find_all:
            return await loop.run_in_executor(self.executor, parser.find_all, *find_all)

        return parser

    async def refresh(self, element=None):
        await self.bot.page.reload()

        if element:
            await self.bot.page.wait_for_selector(element)

def find_siblings_in_executor(parent, child_name):
    return parent.find_all(child_name, recursive=False)


# Find ele ment with bs4 and get xpath with this function
async def get_xpath_from_ele(element, debug=True):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = await asyncio.to_thread(
            find_siblings_in_executor, parent, child.name
        )
        components.append(
            child.name
            if len(siblings) == 1
            else f"{child.name}[{siblings.index(child) + 1}]"
        )
        child = parent
    components.reverse()

    if debug:
        _log.debug(f"Xpath parsed from BS4 element: /{'/'.join(components)}")
    return f"//{'/'.join(components)}"


async def keys_exists(element, *keys, resp_url=None):
    """
    Check if *keys (nested) exists in `element` (dict).
    """

    if not isinstance(element, dict):
        raise AttributeError("keys_exists() expects dict as first argument.")
    if len(keys) == 0:
        raise AttributeError("keys_exists() expects at least two arguments, one given.")

    _element = element
    for key in keys:
        try:
            _element = _element[key]

        except KeyError:
            return False

    _log.debug(f"Key {keys} found in resp {resp_url if resp_url else element}")
    return _element


async def multiple_keys_exists(element, keys, resp_url=None):
    _keys = keys
    for key in _keys:
        if res := await keys_exists(element, *key, resp_url=resp_url):
            return res


async def get_response_body(resp):
    _log.debug(f"Getting response body from {resp.url}..")
    try:
        return await resp.json()
    except Error as e:
        if "No resource with given identifier found" in str(e):
            _log.error(f"Failed to retrieve response body for '{resp.url}': {e}")
        else:
            _log.error(
                f"An unexpected error occurred while trying to retrieve response body for '{resp.url}': {e}"
            )
        return {}


async def is_timeout(start_time, timeout):
    if time.time() - start_time > timeout:
        return True
