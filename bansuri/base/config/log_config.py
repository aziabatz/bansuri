from dataclasses import dataclass
from typing import Optional


@dataclass
class LoggingConfig:
    """Output handling and notifications."""

    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    notify_condition: str = "none"
    notify_after: Optional[str] = None
