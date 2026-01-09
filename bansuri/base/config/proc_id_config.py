from dataclasses import dataclass
from typing import Optional

@dataclass
class IdentificationConfig:
    """Identity and execution context."""
    name: str = ''
    command: str = ''
    user: Optional[str] = None
    working_directory: Optional[str] = None

