import logging
import signal

_log = logging.getLogger(__name__)


class SignalHandler:
    def __init__(self):
        self.keyboard_interrupt = False
        signal.signal(signal.SIGINT, self.sigint_handler)

    def sigint_handler(self, sig, frame):
        if sig == signal.SIGINT:
            self.keyboard_interrupt = True
            _log.info("(CTRL+C) detected! Setting exit flag...")
