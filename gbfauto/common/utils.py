import logging
import asyncio
import time

from bs4 import BeautifulSoup as bs4

_log = logging.getLogger(__name__)


class Utils:
    def __init__(self, bot):
        self.bot = bot
        self.events = self.bot.events
        self.queues = self.bot.queues

    async def wait_for_full_page_load(self):
        await self.bot.page.wait_for_load_state()

    async def get_page_content(self):
        return await self.bot.page.content()

    async def go_to_main(self):
        await self.bot.page.goto("http://game.granbluefantasy.jp/#mypage")
        await self.wait_for_full_page_load()

    async def go_to_locked_quest(self):
        await self.bot.page.goto(self.bot.questing.quest_url)

    async def get_current_url(self):
        return self.bot.page.url

    async def click(self, ele, force=False):
        xpath = await get_xpath_from_ele(ele)
        _log.debug(f"Clicking on element: {xpath}")
        await self.bot.page.locator(xpath).click(force=force)

    async def bs(self, content=None, parser=None, find=(), find_all=()):
        loop = asyncio.get_event_loop()

        if parser is None:
            if content is None:
                content = await self.get_page_content()
            parser = await loop.run_in_executor(None, bs4, content, "lxml")

        if find:
            return await loop.run_in_executor(None, parser.find, *find)

        if find_all:
            return await loop.run_in_executor(None, parser.find_all, *find_all)

        return parser

    async def refresh(self, wait_to_load=False):
        await self.bot.page.reload()
        if wait_to_load:
            print("waiting for load")
            await self.wait_for_full_page_load()


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
            _log.debug(
                f"Key {keys} not found in resp {resp_url if resp_url else element}"
            )
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
    return await resp.json()


async def is_timeout(start_time, timeout):
    if time.time() - start_time > timeout:
        return True
