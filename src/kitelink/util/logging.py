"""User-safe logging helpers — never log tokens or secrets."""

from __future__ import annotations

import logging
import re
from typing import Any

_SECRET_PATTERNS = [
    re.compile(r"(?i)(access_token|refresh_token|client_secret|password|authorization)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"),
    re.compile(r"ya29\.[a-zA-Z0-9_\-.]+"),
]


def redact(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact(a) if isinstance(a, str) else a for a in record.args
                )
        return True


def get_logger(name: str = "kitelink") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    elif not any(isinstance(f, RedactingFilter) for h in logger.handlers for f in h.filters):
        for handler in logger.handlers:
            handler.addFilter(RedactingFilter())
    return logger


def safe_event(message: str, **extra: Any) -> str:
    """Format a diagnostics-safe event line."""
    if extra:
        parts = " ".join(f"{k}={redact(str(v))}" for k, v in extra.items())
        return redact(f"{message} {parts}".strip())
    return redact(message)
