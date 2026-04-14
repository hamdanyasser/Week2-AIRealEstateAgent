"""Logging configuration for the application.

Usage:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("something happened")

Call ``configure_logging()`` once at app startup (e.g. in the FastAPI
lifespan handler) to set up the root logger. ``get_logger`` is safe to
call from any module after that.
"""

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured: bool = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a single stderr handler.

    Idempotent: calling this multiple times will not attach duplicate
    handlers. Safe to call from multiple entry points (FastAPI startup,
    Streamlit app, test fixtures).

    Args:
        level: Minimum log level to emit. Defaults to ``logging.INFO``.
    """
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name.

    Ensures logging is configured before returning. Callers should pass
    ``__name__`` so that log records are tagged with the importing
    module's dotted path.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance.
    """
    if not _configured:
        configure_logging()
    return logging.getLogger(name)
