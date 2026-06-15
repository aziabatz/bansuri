import subprocess
from unittest.mock import MagicMock, patch

from bansuri.task_runner import TaskRunner


@patch("bansuri.task_runner.subprocess.Popen")
def test_run_command_uses_combined_stderr(mock_popen, script_config, global_config):
    config = script_config
    config.stderr = "combined"
    runner = TaskRunner(config, global_config)

    process = MagicMock()
    process.poll.return_value = 0
    process.returncode = 0
    mock_popen.return_value = process

    runner._run_command()

    assert mock_popen.call_args.kwargs["stderr"] == subprocess.STDOUT


@patch("bansuri.task_runner.subprocess.Popen")
def test_run_command_records_output_for_failed_process(mock_popen, script_config, global_config):
    runner = TaskRunner(script_config, global_config)

    process = MagicMock()
    process.poll.return_value = 1
    process.returncode = 1
    process.communicate.return_value = ("out", "err")
    mock_popen.return_value = process

    runner._run_command()

    assert runner._last_return_code == 1
    assert runner._last_stdout == "out"
    assert runner._last_stderr == "err"


@patch("bansuri.task_runner.subprocess.Popen")
@patch("builtins.open")
def test_run_command_resolves_relative_log_paths_from_working_directory(
    mock_open,
    mock_popen,
    make_script_config,
    global_config,
):
    config = make_script_config(
        working_directory="/srv/jobs",
        stdout="stdout.log",
        stderr="stderr.log",
    )
    runner = TaskRunner(config, global_config)

    process = MagicMock()
    process.poll.return_value = 0
    process.returncode = 0
    mock_popen.return_value = process

    runner._run_command()

    mock_open.assert_any_call("/srv/jobs/stdout.log", "a")
    mock_open.assert_any_call("/srv/jobs/stderr.log", "a")


@patch("bansuri.task_runner.subprocess.Popen")
def test_run_command_marks_timeout_and_kills_process(mock_popen, make_script_config, global_config):
    config = make_script_config(timeout="1s")
    runner = TaskRunner(config, global_config)

    process = MagicMock()
    process.poll.return_value = None
    process.pid = 1234
    mock_popen.return_value = process

    with (
        patch("bansuri.task_runner.time.time", side_effect=[100, 102]),
        patch.object(runner, "_kill_process") as mock_kill_process,
    ):
        runner._run_command()

    assert mock_kill_process.called
    assert runner._last_return_code == -1
    assert runner._last_stderr == "Timeout exceeded (1s)"
