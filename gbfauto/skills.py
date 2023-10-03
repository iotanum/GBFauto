from gbfauto.helpers.skills.queue import Queue


class Skills:
    def __init__(self, bot):
        self.bot = bot
        self.queue = Queue(bot)
        self.queues = self.queue.queues

    async def do_queue(self):
        pass
