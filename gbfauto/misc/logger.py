import logging


_logger = logging.getLogger(__name__)


def setup_logger(**kwargs):
    logging.basicConfig(
        level=kwargs["log_level"].upper(),
        format="%(asctime)s[%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _logger.debug("Logger initialized!")
