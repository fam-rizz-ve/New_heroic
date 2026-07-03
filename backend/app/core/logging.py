"""Structured logging configuration using structlog.

Configures structlog to output structured JSON logs in production
and pretty-printed logs in development.
"""

import logging
import sys

import structlog


def configure_logging(debug: bool = False) -> None:
    """Configure structlog and standard library logging.

    Args:
        debug: If True, use pretty-printed console output with debug level.
               If False, use JSON output at INFO level.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.dev.ConsoleRenderer()
                if debug
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root logger to use structlog
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)
