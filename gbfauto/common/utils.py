import logging
import asyncio
import time

from bs4 import BeautifulSoup as bs4

from gbfauto.common.battle.common import BattleCommon
from gbfauto.common.events.common import EventsCommon

_log = logging.getLogger(__name__)


class Utils:
    def __init__(self, bot):
        self.bot = bot
        self.events = self.bot.events
        self.queues = self.bot.queues
        self.battle_common = BattleCommon(self)
        self.events_common = EventsCommon(self)

    async def wait_for_full_page_load(self):
        await self.bot.page.wait_for_load_state()

    async def get_page_content(self):
        return await self.bot.page.content()

    async def go_to_locked_quest(self):
        await self.bot.page.goto(self.bot.questing.quest_url)

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

    async def get_current_url(self):
        return self.bot.page.url

    async def refresh(self):
        await self.bot.page.reload()


# Find ele ment with bs4 and get xpath with this function
async def get_xpath_from_ele(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if 1 == len(siblings)
            else "%s[%d]"
            % (child.name, next(i for i, s in enumerate(siblings, 1) if s is child))
        )
        child = parent
    components.reverse()

    _log.debug(f"Xpath parsed from BS4 element: /{'/'.join(components)}")
    return "/%s" % "/".join(components)


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
