from dataclasses import dataclass
from typing import Optional, Union

@dataclass
class SchedulingConfig:
    """Timing and recurrence settings.
        * schedule_cron: Whether to use cron style for timers
        * timer: Frequence firing of the script. 0 for one-shot execution
        * timeout: The execution time given for the spawned process, if rebased, process is killed
        * no-interface: If set, the task is launched as a single command, without expecting the Task Interface
    """

    schedule_cron: Optional[str] = None
    timer: Optional[str] = None
    timeout: Optional[Union[int, str]] = None
    no_interface: bool = False

    @property
    def is_periodic(self) -> bool:
        """
        Docstring for is_periodic
        
        :param self: Description
        :return: Description
        :rtype: bool
        """
        return bool(self.schedule_cron or (self.timer and self.timer != 'none'))