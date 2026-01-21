import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Union, Any


@dataclass
class ScriptConfig:
    """
    Represents the configuration of a task
    """

    name: str
    command: str
    user: Optional[str] = None
    working_directory: Optional[str] = None
    no_interface: bool = False
    schedule_cron: Optional[str] = None
    timer: Optional[str] = None
    timeout: Optional[str] = None
    times: int = 1
    on_fail: str = "stop"
    depends_on: List[str] = field(default_factory=list)
    success_codes: List[int] = field(default_factory=lambda: [0])
    environment_file: Optional[str] = None
    priority: int = 0
    stdout: Optional[str] = None
    stderr: Union[str, None] = "combined"
    notify: str = "none"
    description: str = ""

    @property
    def is_smart_script(self) -> bool:
        return False
        # return ".py" in self.command or "python" in self.command.lower()

    def validate(self):
        """
        Applies differentiated validation rules depending on the script type.
        """
        if self.name is None:
            # FIXME log warning and set name to command basename
            pass

        if not self.is_smart_script:
            # The execution method MUST be defined (cron, timer, ...)
            has_schedule = self.schedule_cron or (
                self.timer is not None and str(self.timer).lower() != "none"
            )
            has_dependency = bool(self.depends_on)

            if not (has_schedule or has_dependency):
                raise ValueError(
                    f"Plain script '{self.name}' requires 'schedule-cron', 'timer' or 'depends-on' defined in the JSON."
                )


@dataclass
class BansuriConfig:
    "Represents the current loaded definitions for Bansuri"

    version: str
    scripts: List[ScriptConfig]
    notify_command: Optional[str] = None  # command <text> TODO: make <text> replaceable

    @classmethod
    def load_from_file(cls, file_path: str) -> "BansuriConfig":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error decoding JSON in {file_path}: {e}")

        version = data.get("version", "UNKNOWN")
        notify_command = data.get("notify_command")
        scripts_data = data.get("scripts", [])
        parsed_scripts = []

        for item in scripts_data:
            # all hyphens to pythonic "-" to "_"
            normalized_item = {k.replace("-", "_"): v for k, v in item.items()}

            # check only keys that match to avoid errors
            # TODO add warnings on unmatched keys
            valid_keys = ScriptConfig.__annotations__.keys()
            filtered_item = {k: v for k, v in normalized_item.items() if k in valid_keys}

            try:
                script = ScriptConfig(**filtered_item)
                script.validate()
                parsed_scripts.append(script)
            except TypeError as e:
                raise ValueError(
                    f"Missing required fields in script '{item.get('name', 'unknown')}': {e}"
                )
            except ValueError as e:
                raise ValueError(f"Validation error in '{item.get('name')}': {e}")

        return cls(version=version, scripts=parsed_scripts, notify_command=notify_command)
