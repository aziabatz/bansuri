import subprocess
from unittest.mock import MagicMock, patch

import pytest

from bansuri.alerts.cmd_notifier import CommandNotifier


def test_build_message_includes_failure_details(failure_info):
    notifier = CommandNotifier("send-alert")

    message = notifier._build_message(failure_info)

    assert "Task test-task has failed." in message
    assert "Command:           echo fail" in message
    assert "Attempt:           2/3" in message
    assert "Description:       A test task" in message
    assert "--- Output ---" in message
    assert "output line" in message
    assert "--- Error ---" in message
    assert "error line" in message


@patch("bansuri.alerts.cmd_notifier.subprocess.run")
def test_notify_runs_command_with_message_on_stdin(mock_run, failure_info):
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    notifier = CommandNotifier("send-alert --channel ops", timeout=9)

    result = notifier.notify(failure_info)

    assert result is True
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["send-alert", "--channel", "ops"]
    assert kwargs["input"] == notifier._build_message(failure_info)
    assert kwargs["capture_output"] is True
    assert kwargs["shell"] is False
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 9


@patch("bansuri.alerts.cmd_notifier.subprocess.run")
def test_notify_returns_false_for_non_zero_exit_code(mock_run, failure_info):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")
    notifier = CommandNotifier("send-alert")

    assert notifier.notify(failure_info) is False


@pytest.mark.parametrize(
    "side_effect",
    [
        pytest.param(subprocess.TimeoutExpired(cmd="send-alert", timeout=3), id="timeout"),
        pytest.param(RuntimeError("boom"), id="unexpected-error"),
    ],
)
@patch("bansuri.alerts.cmd_notifier.subprocess.run")
def test_notify_returns_false_when_subprocess_raises(mock_run, failure_info, side_effect):
    mock_run.side_effect = side_effect
    notifier = CommandNotifier("send-alert")

    assert notifier.notify(failure_info) is False
