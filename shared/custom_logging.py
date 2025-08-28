"""
shared.logging

Consistent logger setup for all listeners.

Example usage:
    from shared.logging import setup_logger
    logger = setup_logger(__name__)
    logger.info('Logger ready!')
"""
import logging
import sys
from typing import Optional


def setup_logging(level=logging.INFO):
    """
    Set up root logger with a consistent format and level.
    Args:
        level (int): Logging level (e.g., logging.INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )


def get_logger(name=None):
    """
    Get a logger with the given name (module/class).
    Args:
        name (str): Logger name (usually __name__ or class name).
    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)


def setup_logger(
    name: str, level: int = logging.INFO, fmt: Optional[str] = None
) -> logging.Logger:
    """
    Set up and return a logger with the specified name and level.

    Args:
        name (str): Logger name, usually __name__.
        level (int): Logging level (default: logging.INFO).
        fmt (Optional[str]): Log format string. If None, uses a default format.

    Returns:
        logging.Logger: Configured logger instance.

    Example:
        >>> from shared.logging import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info('Logger is ready!')
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt or "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
