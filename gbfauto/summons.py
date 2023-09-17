import os

from dotenv import load_dotenv


class Summons:
    def __init__(self, bot):
        self.bot = bot
        self.support_element = None

    async def update_summon_config(self):
        load_dotenv("config.env", override=True)
        self.support_element = int(os.getenv("SUPPORT_ELEMENT"))

    async def pick_summon(self):
        await self.update_summon_config()

        instructions_to_run = {
            "support_element": self._bot.press.support_element,
            "pick_summon": self._bot.press.support_summon,
            "confirm_summon": self._bot.press.confirm_support_summon,
        }

        support_dict = None
        for instr, func in instructions_to_run.items():
            in_summon_screen = self._bot.wait.for_support_summon()
            if in_summon_screen:
                func(
                    support_dict=support_dict,
                    support_element_num=SUPPORT_ELEMENT,
                    first_summon=True if not support_dict else False,
                )

                if not support_dict:
                    support_dict = self.get_best_support_summon()

                time.sleep(0.15)

            else:
                return in_summon_screen
