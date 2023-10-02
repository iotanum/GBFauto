import logging
import asyncio
import os
import time
import re

from bs4 import BeautifulSoup as bs

from selenium import common as selenium_err
from selenium.webdriver.common.by import By
from dotenv import load_dotenv


_log = logging.getLogger(__name__)


class Questing:
    def __init__(self, bot):
        self.bot = bot
        self.repeat = False
        self.coop = False
        self.sandbox = False
        self.quest_url = None

    async def wait_for_repeatable_quest(self):
        if not self.quest_url:
            _log.info("Waiting for you to enter a quest...")

        while True:
            url = self.bot.page.url

            # normal fights (GW, Events, Missions)
            # if "#quest/supporter" in url:
            #     if not self.quest_url:
            #         _log.info("Locked in on this quest.")
            #         break
            #
            # # coop fights
            # if "#coopraid/room/" in url:
            #     _log.info("Locked on this CO-OP quest.")
            #     self.coop = True
            #     break
            #
            # # arcanum sandbox fights
            # if "#replicard/supporter" in url:
            #     _log.info("Locked on this Sandbox quest.")
            #     self.sandbox = True
            #     break
            #
            # # new raid thingy
            # if "#quest/assist" in url:
            #     _log.info("Locked to raids, please choose filter option.")
            #     # self.choose_raid_filter()
            #     self.bot.new_raids = True
            #     break

            await asyncio.sleep(0.2)

        self.quest_url = url

    async def pre_fight(self):
        modes = [self.coop, self.sandbox, self.bot.new_raids]
        if not any(modes):
            self.bot.handle.pre_fight_support_summons()
        elif self.sandbox is True:
            self.bot.handle.sandbox_summon_pick()
        elif self.bot.new_raids is True:
            self.handle_new_raids_join()
        else:
            # Wait until player chooses its COOP team.
            self.wait_for_coop_prep()

            # And now press 'Ready' to enter the fight.
            chapter_id = self.get_start_button_chapter_id()
            self.bot.press.by_chapter_id(chapter_id)

        action = self.post_summon_checks()
        if action:
            self.go_to_quest()
            self.handle_pre_fight()

    async def do_repeatable_quest(self):
        if self.repeat is False:
            await self.wait_for_repeatable_quest()
            self.repeat = True

        # PRE-FIGHT STUFF
        await self.pre_fight()
