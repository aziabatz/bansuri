from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from bansuri.task_runner import TaskRunner


@pytest.mark.parametrize(
    ("overrides", "expected_method"),
    [
        pytest.param({"schedule_cron": "* * * * *", "timer": "0"}, "_cron_execution_loop", id="cron"),
        pytest.param({"schedule_cron": None, "timer": "10s"}, "_timer_execution_loop", id="timer"),
        pytest.param({"schedule_cron": None, "timer": "0"}, "_simple_execution_loop", id="simple"),
    ],
)
def test_execution_loop_dispatches_to_matching_mode(
    make_script_config,
    global_config,
    overrides,
    expected_method,
):
    config = make_script_config(**overrides)

    with (
        patch.object(TaskRunner, "_cron_execution_loop") as mock_cron,
        patch.object(TaskRunner, "_timer_execution_loop") as mock_timer,
        patch.object(TaskRunner, "_simple_execution_loop") as mock_simple,
    ):
        runner = TaskRunner(config, global_config)
        runner._execution_loop()

    called = {
        "_cron_execution_loop": mock_cron.called,
        "_timer_execution_loop": mock_timer.called,
        "_simple_execution_loop": mock_simple.called,
    }
    assert called == {
        "_cron_execution_loop": expected_method == "_cron_execution_loop",
        "_timer_execution_loop": expected_method == "_timer_execution_loop",
        "_simple_execution_loop": expected_method == "_simple_execution_loop",
    }


def test_simple_execution_loop_retries_then_completes(make_script_config, global_config):
    config = make_script_config(on_fail="restart", max_attempts=3, times=2)
    runner = TaskRunner(config, global_config)
    return_codes = iter([1, 0])

    def fake_run_process():
        code = next(return_codes)
        runner.process = MagicMock(returncode=code)

    with (
        patch.object(runner, "_run_process", side_effect=fake_run_process) as mock_run_process,
        patch.object(runner.stop_event, "wait", return_value=False),
    ):
        runner._simple_execution_loop()

    assert mock_run_process.call_count == 2
    assert runner.attempts == 2
    assert runner.failed_attempts == 0
    assert runner.status == "COMPLETED"


def test_timer_execution_loop_runs_once_and_waits_for_next_interval(
    make_script_config,
    global_config,
):
    config = make_script_config(timer="1s", times=1)
    runner = TaskRunner(config, global_config)

    with (
        patch.object(runner, "_run_process") as mock_run_process,
        patch.object(runner.stop_event, "wait", return_value=True) as mock_wait,
    ):
        runner._timer_execution_loop()

    mock_run_process.assert_called_once()
    mock_wait.assert_called_once_with(timeout=1)
    assert runner.next_run is not None


def test_timer_execution_loop_invalid_timer_marks_failed_when_run_fails(
    make_script_config,
    global_config,
):
    config = make_script_config(timer="invalid")
    runner = TaskRunner(config, global_config)

    def fake_run_process():
        runner.process = MagicMock(returncode=1)
        runner._last_return_code = 1

    with patch.object(runner, "_run_process", side_effect=fake_run_process) as mock_run_process:
        runner._timer_execution_loop()

    mock_run_process.assert_called_once()
    assert runner.times == 1
    assert runner.successful_times == 0
    assert runner.failed_attempts == 1
    assert runner.status == "FAILED"


def test_cron_execution_loop_waits_for_next_scheduled_run(make_script_config, global_config):
    config = make_script_config(schedule_cron="* * * * *", timer="0")
    runner = TaskRunner(config, global_config)
    expected_next_run = datetime.now() + timedelta(seconds=10)

    croniter_cls = MagicMock()
    croniter_cls.is_valid.return_value = True
    croniter_instance = MagicMock()
    croniter_instance.get_next.return_value = expected_next_run
    croniter_cls.return_value = croniter_instance

    with (
        patch.dict("sys.modules", {"croniter": SimpleNamespace(croniter=croniter_cls)}),
        patch.object(runner.stop_event, "wait", return_value=True) as mock_wait,
    ):
        runner._cron_execution_loop()

    mock_wait.assert_called_once()
    assert runner.next_run == expected_next_run
