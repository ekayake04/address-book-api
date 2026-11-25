"""Central logging configuration used by the whole application."""

import logging

from app.config import LOG_LEVEL


def setup_logging() -> None:
    """Configure the root logger with a consistent, readable format."""
    logging.basicConfig(
        level=LOG_LEVEL.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
