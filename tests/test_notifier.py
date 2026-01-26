import pytest
import subprocess
from unittest.mock import MagicMock, patch
from datetime import datetime
from bansuri.alerts.cmd_notifier import CommandNotifier
from bansuri.alerts.notifier import FailureInfo


@pytest.fixture
def failure_info():
    return FailureInfo(
        task_name="test_task",
        command="echo fail",
        working_directory="/tmp",
        return_code=1,
        attempt=1,
        max_attempts=3,
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        description="A test task",
        stdout="output line",
        stderr="error line",
    )


@patch("subprocess.run")
def test_notify_success(mock_run, failure_info):
    notifier = CommandNotifier("send_alert.sh")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    assert notifier.notify(failure_info) is True

    mock_run.assert_called_once()
    cmd_arg = mock_run.call_args[0][0]
    assert "send_alert.sh" in cmd_arg
    assert "test_task" in cmd_arg


@patch("subprocess.run")
def test_notify_failure(mock_run, failure_info):
    notifier = CommandNotifier("send_alert.sh")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_run.return_value = mock_result

    assert notifier.notify(failure_info) is False


def test_build_output_command(failure_info):
    notifier = CommandNotifier("cmd")
    cmd = notifier._build_output_command(failure_info)

    assert "Task test_task has failed" in cmd
    assert "output line" in cmd
    assert '\\"printf %b' in cmd  # Check shell escaping structure


@patch("subprocess.run")
def test_notify_timeout(mock_run, failure_info):
    notifier = CommandNotifier("cmd", timeout=1)
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=1)

    assert notifier.notify(failure_info) is False


@patch("subprocess.run")
def test_notify_exception(mock_run, failure_info):
    notifier = CommandNotifier("cmd")
    mock_run.side_effect = Exception("Unexpected error")

    assert notifier.notify(failure_info) is False
