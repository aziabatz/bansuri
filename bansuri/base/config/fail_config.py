from dataclasses import dataclass, field
from typing import List


@dataclass
class FailureControlConfig:
    """Error handling and dependencies."""

    max_attempts: int = 1  # how many retry attemps when task fails
    on_fail: str = "stop"  # what to do on process fail
    depends_on: List[str] = field(default_factory=list)  # NOT USED
    success_codes: List[int] = field(default_factory=lambda: [0])  # codes used for success
