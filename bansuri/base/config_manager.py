from datetime import datetime
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any


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
    times: int = 0 # for successful runs
    max_attempts: int = 1 # for failed executons
    on_fail: str = "stop"
    depends_on: List[str] = field(default_factory=list)
    success_codes: List[int] = field(default_factory=lambda: [0])
    environment_file: Optional[str] = None
    priority: int = 0
    stdout: Optional[str] = None
    stderr: Union[str, None] = "combined"
    notify: str = "none"
    notify_after: Optional[str] = "300s"
    description: str = ""
    restart_delay: Optional[str] = "5s"
    notify_mode: str = "after-fail"
    notify_threshold: int = 1
    notify_command: Optional[str] = None

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
            raw_text = f.read()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            try:
                data = json.loads(cls._strip_json_comments(raw_text))
            except json.JSONDecodeError as e:
                raise ValueError(f"Error decoding JSON in {file_path}: {e}")

        version = data.get("version", "UNKNOWN")
        notify_command = data.get("notify_command")
        defaults = data.get("defaults", {})
        scripts_data = data.get("scripts", [])
        parsed_scripts = []

        for item in scripts_data:
            normalized_item = cls._normalize_script_item(item, defaults)

            valid_keys = ScriptConfig.__annotations__.keys()
            filtered_item = {k: v for k, v in normalized_item.items() if k in valid_keys}

            not_found_keys = set(normalized_item) - set(valid_keys)

            for k in not_found_keys:
                message = f"Config: Found key {k} but not recognized as a bansuri valid field"
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MASTER] {message}",
                    flush=True,
                )

            try:
                script = ScriptConfig(**filtered_item)
                script.validate()
                parsed_scripts.append(script)
            except TypeError as e:
                raise ValueError(
                    f"Missing required fields in script '{cls._script_name(item)}': {e}"
                )
            except ValueError as e:
                raise ValueError(f"Validation error in '{cls._script_name(item)}': {e}")

        return cls(version=version, scripts=parsed_scripts, notify_command=notify_command)

    @staticmethod
    def _script_name(item: Dict[str, Any]) -> str:
        general = item.get("general", {})
        return item.get("name") or general.get("name") or "unknown"

    @classmethod
    def _normalize_script_item(
        cls, item: Dict[str, Any], defaults: Dict[str, Any]
    ) -> Dict[str, Any]:
        if any(section in item for section in ("general", "scheduling", "failure-control", "logging")):
            return cls._normalize_grouped_script(item, defaults)

        return {k.replace("-", "_"): v for k, v in item.items()}

    @classmethod
    def _normalize_grouped_script(
        cls, item: Dict[str, Any], defaults: Dict[str, Any]
    ) -> Dict[str, Any]:
        general = cls._merge_dicts(defaults.get("general", {}), item.get("general", {}))
        scheduling = cls._merge_dicts(defaults.get("scheduling", {}), item.get("scheduling", {}))
        failure_control = cls._merge_dicts(
            defaults.get("failure-control", {}),
            item.get("failure-control", {}),
        )
        logging = cls._merge_dicts(defaults.get("logging", {}), item.get("logging", {}))

        scheduler = scheduling.get("scheduler")
        params = scheduling.get("params")
        schedule_cron = None
        timer = None

        if scheduler == "cron":
            schedule_cron = params
        elif scheduler == "timer":
            timer = params
        elif scheduler == "none":
            timer = "0"

        restart_params = failure_control.get("restart-params", {})
        notify_config = failure_control.get("notify", {})

        notify_handler = "none"
        notify_command = None
        if cls._coerce_bool(notify_config.get("enabled", False)):
            handler = str(notify_config.get("handler", "command")).lower()
            if handler == "command":
                handler_config = notify_config.get("handler-config")
                if isinstance(handler_config, str):
                    notify_handler = "command"
                    notify_command = handler_config
                elif handler_config is not None:
                    message = "Config: command notify handler requires string handler-config. Notifications disabled."
                    print(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MASTER] {message}",
                        flush=True,
                    )
            else:
                message = f"Config: notify handler '{handler}' is not supported yet. Notifications disabled."
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MASTER] {message}",
                    flush=True,
                )

        return {
            "name": general.get("name"),
            "command": general.get("command"),
            "description": general.get("description", ""),
            "working_directory": general.get("working-directory"),
            "schedule_cron": schedule_cron,
            "timer": timer,
            "timeout": scheduling.get("timeout"),
            "times": cls._coerce_int(scheduling.get("max-runs"), 0),
            "max_attempts": cls._coerce_int(failure_control.get("max-attempts"), 1),
            "on_fail": failure_control.get("on-fail", "stop"),
            "stdout": cls._normalize_log_target(logging.get("stdout")),
            "stderr": cls._normalize_log_target(logging.get("stderr", "$$combined")),
            "notify": notify_handler,
            "notify_mode": str(notify_config.get("mode", "after-fail")).lower(),
            "notify_threshold": cls._coerce_int(notify_config.get("after-threshold"), 1),
            "notify_command": notify_command,
            "restart_delay": restart_params.get("after", "5s"),
        }

    @staticmethod
    def _merge_dicts(base: Any, override: Any) -> Dict[str, Any]:
        base_dict = base if isinstance(base, dict) else {}
        override_dict = override if isinstance(override, dict) else {}
        merged = dict(base_dict)

        for key, value in override_dict.items():
            if isinstance(merged.get(key), dict) and isinstance(value, dict):
                merged[key] = BansuriConfig._merge_dicts(merged[key], value)
            else:
                merged[key] = value

        return merged

    @staticmethod
    def _normalize_log_target(value: Any) -> Any:
        if value == "$$combined":
            return "combined"
        return value

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == "true"
        return bool(value)

    @staticmethod
    def _coerce_int(value: Any, default: int) -> int:
        if value in (None, ""):
            return default
        return int(value)

    @staticmethod
    def _strip_json_comments(text: str) -> str:
        result = []
        in_string = False
        escaped = False
        in_line_comment = False
        in_block_comment = False
        index = 0

        while index < len(text):
            char = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""

            if in_line_comment:
                if char == "\n":
                    in_line_comment = False
                    result.append(char)
                index += 1
                continue

            if in_block_comment:
                if char == "*" and next_char == "/":
                    in_block_comment = False
                    index += 2
                    continue
                if char == "\n":
                    result.append(char)
                index += 1
                continue

            if in_string:
                result.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "\"":
                    in_string = False
                index += 1
                continue

            if char == "\"":
                in_string = True
                result.append(char)
                index += 1
                continue

            if char == "/" and next_char == "/":
                in_line_comment = True
                index += 2
                continue

            if char == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue

            result.append(char)
            index += 1

        return "".join(result)
