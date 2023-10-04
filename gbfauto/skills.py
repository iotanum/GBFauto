from gbfauto.helpers.skills.queue import Queue


class Skills:
    def __init__(self, bot):
        self.bot = bot
        self.queue_module = Queue(self)

    async def do_queue(self):
        pass
