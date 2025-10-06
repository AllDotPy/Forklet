"""
Logging/structured log models for Forklet.

Currently a placeholder as no explicit logging models exist yet. This module
is created to satisfy the proposed structure and future extensibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class StructuredLogRecord:
    """Simple structured log record for future use."""

    level: str
    message: str
    timestamp: datetime
    context: Optional[Dict[str, str]] = None


__all__ = [
    "StructuredLogRecord",
]


