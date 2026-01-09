from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourcesConfig:
    """System resource limits and environment."""
    environment_file: Optional[str] = None
    priority: Optional[int] = None # NOT USED