import asyncio

from gbfauto.misc.logger import setup_logger
from gbfauto.misc.args import get_args

from gbfauto.bot import Bot
from gbfauto.login import Login


async def start():
    while True:
        await asyncio.sleep(10000)


async def main():
    args = get_args()
    setup_logger(**args)

    bot = Bot()
    await bot.run()

    await start()


if __name__ == "__main__":
    asyncio.run(main())
