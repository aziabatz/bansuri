from unittest.mock import MagicMock, patch

import pytest

from bansuri.alerts.cmd_notifier import CommandNotifier
from bansuri.task_runner import TaskRunner


def test_runner_initializes_default_state(script_config, global_config):
    runner = TaskRunner(script_config, global_config)

    assert runner.process is None
    assert runner.attempts == 0
    assert runner.failed_attempts == 0
    assert runner.status == "STOPPED"
    assert runner.notifier is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("250ms", 0.25, id="milliseconds"),
        pytest.param("30s", 30, id="seconds"),
        pytest.param("5m", 300, id="minutes"),
        pytest.param("1h", 3600, id="hours"),
        pytest.param("2d", 172800, id="days"),
        pytest.param("45", 45, id="plain-digits"),
        pytest.param(None, None, id="missing"),
        pytest.param("invalid", None, id="invalid"),
    ],
)
def test_parse_timeout_handles_supported_values(script_config, global_config, value, expected):
    runner = TaskRunner(script_config, global_config)

    assert runner._parse_timeout(value) == expected


def test_create_notifier_prefers_task_command_over_global_command(make_script_config, global_config):
    config = make_script_config(notify="command", notify_command="task-alert")
    global_config.notify_command = "global-alert"

    runner = TaskRunner(config, global_config)

    assert isinstance(runner.notifier, CommandNotifier)
    assert runner.notifier.notify_command == "task-alert"


def test_create_notifier_returns_none_without_notify_command(make_script_config, global_config):
    config = make_script_config(notify="mail")

    runner = TaskRunner(config, global_config)

    assert runner.notifier is None


def test_start_creates_thread_and_stop_joins_existing_thread(script_config, global_config):
    runner = TaskRunner(script_config, global_config)

    with patch("bansuri.task_runner.threading.Thread") as mock_thread_cls:
        thread = MagicMock()
        thread.is_alive.return_value = False
        mock_thread_cls.return_value = thread

        runner.start()

        assert runner.status == "STARTING"
        thread.start.assert_called_once()

        runner.thread = thread
        thread.is_alive.side_effect = [True, False]
        with patch.object(runner, "_kill_process") as mock_kill_process:
            stopped = runner.stop()

    mock_thread_cls.assert_called_once()
    mock_kill_process.assert_called_once()
    thread.join.assert_called_once_with(timeout=5)
    assert stopped is True
    assert runner.status == "STOPPED"


def test_stop_returns_false_when_thread_still_alive_after_join(script_config, global_config):
    runner = TaskRunner(script_config, global_config)
    runner.thread = MagicMock()
    runner.thread.is_alive.side_effect = [True, True]

    with patch.object(runner, "_kill_process") as mock_kill_process:
        stopped = runner.stop()

    mock_kill_process.assert_called_once()
    runner.thread.join.assert_called_once_with(timeout=5)
    assert stopped is False
    assert runner.status == "STOPPING"


def test_start_does_not_replace_running_thread(script_config, global_config):
    runner = TaskRunner(script_config, global_config)
    runner.thread = MagicMock(is_alive=MagicMock(return_value=True))

    with patch("bansuri.task_runner.threading.Thread") as mock_thread_cls:
        runner.start()

    mock_thread_cls.assert_not_called()
