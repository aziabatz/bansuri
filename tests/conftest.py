from datetime import datetime

import pytest

from bansuri.alerts.notifier import FailureInfo
from bansuri.base.config_manager import BansuriConfig, ScriptConfig


@pytest.fixture
def global_config():
    return BansuriConfig(version="1.0", scripts=[])


@pytest.fixture
def make_script_config():
    def _make(**overrides):
        values = {
            "name": "test-task",
            "command": "echo test",
            "timer": "0",
        }
        values.update(overrides)
        return ScriptConfig(**values)

    return _make


@pytest.fixture
def script_config(make_script_config):
    return make_script_config()


@pytest.fixture
def failure_info():
    return FailureInfo(
        task_name="test-task",
        command="echo fail",
        working_directory="/tmp",
        return_code=1,
        attempt=2,
        max_attempts=3,
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        description="A test task",
        stdout="output line",
        stderr="error line",
    )
