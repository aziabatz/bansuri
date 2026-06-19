from unittest.mock import MagicMock, patch

import pytest

from bansuri.alerts.notifier import FailureInfo
from bansuri.task_runner import TaskRunner


def test_handle_notify_builds_failure_info_for_notifier(make_script_config, global_config):
    config = make_script_config(notify="command", notify_command="send-alert")
    runner = TaskRunner(config, global_config)
    runner.failed_attempts = 2
    runner.notifier = MagicMock()
    runner.notifier.notify.return_value = True

    runner._handle_notify(1, "out", "err")

    runner.notifier.notify.assert_called_once()
    failure = runner.notifier.notify.call_args.args[0]
    assert isinstance(failure, FailureInfo)
    assert failure.task_name == "test-task"
    assert failure.return_code == 1
    assert failure.attempt == 2
    assert failure.stdout == "out"
    assert failure.stderr == "err"


@pytest.mark.parametrize(
    ("mode", "failed_attempts", "threshold", "max_attempts", "on_fail", "should_notify"),
    [
        pytest.param("after-fail", 1, 3, 4, "restart", True, id="after-fail"),
        pytest.param("after-many", 2, 2, 4, "restart", True, id="after-many-threshold"),
        pytest.param("after-many", 1, 2, 4, "restart", False, id="after-many-before-threshold"),
        pytest.param("on-exhausted", 4, 2, 4, "restart", True, id="on-exhausted-restart"),
        pytest.param("on-exhausted", 1, 2, 4, "stop", True, id="on-exhausted-stop"),
    ],
)
def test_maybe_notify_failure_respects_notify_mode(
    make_script_config,
    global_config,
    mode,
    failed_attempts,
    threshold,
    max_attempts,
    on_fail,
    should_notify,
):
    config = make_script_config(
        notify="command",
        notify_command="send-alert",
        notify_mode=mode,
        notify_threshold=threshold,
        max_attempts=max_attempts,
        on_fail=on_fail,
    )
    runner = TaskRunner(config, global_config)
    runner.notifier = MagicMock()
    runner.failed_attempts = failed_attempts
    runner._last_return_code = 7
    runner._last_stdout = "stdout"
    runner._last_stderr = "stderr"

    with patch.object(runner, "_handle_notify") as mock_handle_notify:
        runner._maybe_notify_failure()

    if should_notify:
        mock_handle_notify.assert_called_once_with(7, "stdout", "stderr")
    else:
        mock_handle_notify.assert_not_called()


@pytest.mark.parametrize(
    ("on_fail", "failed_attempts", "max_attempts", "expected"),
    [
        pytest.param("ignore", 1, 3, False, id="ignore"),
        pytest.param("stop", 1, 3, True, id="stop"),
        pytest.param("restart", 1, 3, False, id="restart-with-retries-left"),
        pytest.param("restart", 3, 3, True, id="restart-exhausted"),
    ],
)
def test_handle_on_fail_returns_expected_stop_decision(
    make_script_config,
    global_config,
    on_fail,
    failed_attempts,
    max_attempts,
    expected,
):
    config = make_script_config(on_fail=on_fail, max_attempts=max_attempts)
    runner = TaskRunner(config, global_config)
    runner.failed_attempts = failed_attempts

    assert runner._handle_on_fail() is expected


def test_check_max_executions_ignores_cron_limit(make_script_config, global_config):
    config = make_script_config(schedule_cron="* * * * *", timer="0", times=1)
    runner = TaskRunner(config, global_config)
    runner.attempts = 10

    assert runner._check_max_executions() is False
