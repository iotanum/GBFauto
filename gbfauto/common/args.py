import argparse
import logging


_log = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description="GBF Auto :)")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error", "critical", "all"],
        default="info",
        metavar="",
        help="Set log level. (default: %(default)s)",
    )

    args = vars(parser.parse_args())
    _log.debug(f"Args initialized! {args}")

    return args
