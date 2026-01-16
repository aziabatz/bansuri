from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FailureInfo:
    task_name: str
    command: str
    working_directory: Optional[str]
    return_code: int
    attempt: int
    max_attempts: int
    timestamp: datetime
    description: str
    stdout: str
    stderr: str


class Notifier(ABC):
    """Base class for notification handlers."""

    @abstractmethod
    def notify(self, failure_info: FailureInfo) -> bool:
        """Abstract method that handles on failure notifications"""
        pass

