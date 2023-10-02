import asyncio

from gbfauto.common.logger import setup_logger
from gbfauto.common.args import get_args

from gbfauto.common.engine import launch_engine
from gbfauto.bot import Bot


async def setup():
    """
    Set up logger and parse command-line arguments.
    """
    args = get_args()
    setup_logger(**args)


async def main():
    """
    Main function to run the GBF Auto bot.
    """
    await setup()

    bot_engine = await launch_engine()
    await Bot(bot_engine).run()


if __name__ == "__main__":
    asyncio.run(main())
