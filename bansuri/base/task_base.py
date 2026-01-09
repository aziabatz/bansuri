from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any

from bansuri.base.config.task_config import TaskConfig

class AbstractTask(ABC):
    """
    Abstract base class for tasks.
    Uses a modular TaskConfig for properties and as execution interface.
    """

    def __init__(self, config: TaskConfig):
        self.config = config

    @abstractmethod
    def run(self) -> int:
        """
        Execute the task.
        Returns:
            int: The exit code of the command.
        """
        #pass
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def stop(self) -> None:
        """
        Terminate the task if it is running.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def __repr__(self):
        return f"<{self.__class__.__name__} name='{self.config.identification.name}'>"
