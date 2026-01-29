from typing import Dict, Any
from dataclasses import dataclass, field

from bansuri.base.config.fail_config import FailureControlConfig
from bansuri.base.config.log_config import LoggingConfig
from bansuri.base.config.proc_id_config import IdentificationConfig
from bansuri.base.config.resource_config import ResourcesConfig
from bansuri.base.config.schedule_config import SchedulingConfig


@dataclass
class TaskConfig:
    """Config Wrapper for script tasks."""

    identification: IdentificationConfig
    scheduling: SchedulingConfig = field(default_factory=SchedulingConfig)
    failure_control: FailureControlConfig = field(default_factory=FailureControlConfig)
    resources: ResourcesConfig = field(default_factory=ResourcesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":  # type: ignore
        """Factory method to create TaskConfig from a flat dictionary."""
        return cls(
            identification=IdentificationConfig(
                name=data.get("name", "unnamed"),
                command=data.get("command", ""),
                user=data.get("user"),
                working_directory=data.get("where"),
            ),
            scheduling=SchedulingConfig(
                schedule_cron=data.get("schedule-cron"),
                timer=data.get("timer"),
                timeout=data.get("timeout"),
                times=int(data.get("times", 0)) if data.get("times") else 0,
            ),
            failure_control=FailureControlConfig(
                max_attempts=int(data.get("max-attempts", 1)) if data.get("max-attempts") else 1,
                on_fail=data.get("on-fail", "stop"),
                depends_on=data.get("depends-on", []),
                success_codes=data.get("success-codes", [0]),
            ),
            resources=ResourcesConfig(
                environment_file=data.get("environment-file"),
                priority=data.get("priority"),
            ),
            logging=LoggingConfig(
                stdout_path=data.get("stdout"),
                stderr_path=data.get("stderr"),
                notify_condition=data.get("notify", "none"),
                notify_after=data.get("notify-after"),
            ),
        )
