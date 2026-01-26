import pytest
import time
import os
import signal
import sys
from unittest.mock import MagicMock, patch, ANY, call
from bansuri.task_runner import TaskRunner
from bansuri.base.config_manager import ScriptConfig, BansuriConfig
from bansuri.alerts.notifier import FailureInfo


@pytest.fixture
def simple_config():
    return ScriptConfig(name="test_task", command="echo test", timer="0")


@pytest.fixture
def global_config():
    return BansuriConfig(version="1.0", scripts=[])


def test_runner_initialization(simple_config, global_config):
    runner = TaskRunner(simple_config, global_config)
    assert runner.config.name == "test_task"
    assert runner.attempts == 0
    assert runner.process is None


@patch("subprocess.Popen")
def test_run_command_execution(mock_popen, simple_config, global_config):
    runner = TaskRunner(simple_config, global_config)

    process = MagicMock()
    process.poll.side_effect = [None, 0]
    process.returncode = 0
    process.communicate.return_value = ("output", "")
    mock_popen.return_value = process

    runner.stop_event = MagicMock()
    runner.stop_event.is_set.side_effect = [False, False, True]

    with patch("time.sleep"):
        runner._run_command()

    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert args[0] == "echo test"
    assert kwargs["shell"] is True


@patch("subprocess.Popen")
def test_run_command_timeout(mock_popen, simple_config, global_config):
    simple_config.timeout = "1s"
    runner = TaskRunner(simple_config, global_config)

    process = MagicMock()
    process.poll.return_value = None
    process.pid = 123
    mock_popen.return_value = process

    with patch("time.time", side_effect=[100, 100.5, 102]):
        with patch("time.sleep"):
            with patch.object(runner, "_kill_process") as mock_kill:
                runner._run_command()
                mock_kill.assert_called_once()


@patch("subprocess.Popen")
def test_max_attempts_logic(mock_popen, simple_config, global_config):
    simple_config.times = 2
    runner = TaskRunner(simple_config, global_config)

    process = MagicMock()
    process.poll.return_value = 0
    process.returncode = 0
    mock_popen.return_value = process

    with patch.object(runner.stop_event, "wait", return_value=False):
        runner._simple_execution_loop()

    assert runner.attempts == 2
    assert mock_popen.call_count == 2


def test_parse_timeout(simple_config, global_config):
    runner = TaskRunner(simple_config, global_config)
    assert runner._parse_timeout("30s") == 30
    assert runner._parse_timeout("5m") == 300
    assert runner._parse_timeout("1h") == 3600
    assert runner._parse_timeout("invalid") is None
    assert runner._parse_timeout(None) is None


@patch("subprocess.Popen")
def test_kill_process(mock_popen, simple_config, global_config):
    runner = TaskRunner(simple_config, global_config)

    process = MagicMock()
    process.poll.return_value = None
    process.pid = 12345
    runner.process = process

    with patch("os.killpg") as mock_killpg:
        with patch("os.getpgid", return_value=12345):
            process.poll.side_effect = [None, 0]
            runner._kill_process()
            mock_killpg.assert_any_call(12345, signal.SIGTERM)


def test_handle_on_fail(simple_config, global_config):
    runner = TaskRunner(simple_config, global_config)

    simple_config.on_fail = "stop"
    assert runner._handle_on_fail() is True

    simple_config.on_fail = "restart"
    assert runner._handle_on_fail() is False


def test_create_notifier(simple_config, global_config):
    simple_config.notify = "none"
    runner = TaskRunner(simple_config, global_config)
    assert runner.notifier is None

    simple_config.notify = "mail"
    global_config.notify_command = None
    runner = TaskRunner(simple_config, global_config)
    assert runner.notifier is None

    global_config.notify_command = "mail -s"
    runner = TaskRunner(simple_config, global_config)
    assert runner.notifier is not None


def test_handle_notify(simple_config, global_config):
    simple_config.notify = "mail"
    global_config.notify_command = "echo"
    runner = TaskRunner(simple_config, global_config)

    runner.notifier = MagicMock()
    runner.notifier.notify.return_value = True

    runner._handle_notify(1, "out", "err")

    runner.notifier.notify.assert_called_once()
    args = runner.notifier.notify.call_args[0][0]
    assert isinstance(args, FailureInfo)
    assert args.return_code == 1


def test_cron_execution_loop(simple_config, global_config):
    # Test cron loop mocking the optional croniter dependency
    simple_config.schedule_cron = "* * * * *"
    runner = TaskRunner(simple_config, global_config)

    mock_croniter_cls = MagicMock()
    mock_croniter_cls.is_valid.return_value = True

    cron_instance = MagicMock()
    from datetime import datetime, timedelta

    cron_instance.get_next.return_value = datetime.now() + timedelta(seconds=10)
    mock_croniter_cls.return_value = cron_instance

    mock_module = MagicMock()
    mock_module.croniter = mock_croniter_cls

    runner.stop_event = MagicMock()
    runner.stop_event.is_set.side_effect = [False, True]
    runner.stop_event.wait.return_value = True

    with patch.dict("sys.modules", {"croniter": mock_module}):
        runner._cron_execution_loop()

    runner.stop_event.wait.assert_called()


def test_timer_execution_loop(simple_config, global_config):
    simple_config.timer = "1s"
    runner = TaskRunner(simple_config, global_config)

    runner.stop_event = MagicMock()
    runner.stop_event.is_set.side_effect = [False, True]
    runner.stop_event.wait.return_value = True

    with patch.object(runner, "_run_process") as mock_run:
        runner._timer_execution_loop()
        mock_run.assert_called_once()
        runner.stop_event.wait.assert_called_with(timeout=1)


def test_logging(simple_config, global_config, capsys):
    """Prueba que el log escriba en stdout con el formato correcto"""
    runner = TaskRunner(simple_config, global_config)
    runner.log("test message")
    captured = capsys.readouterr()
    assert "[test_task] test message" in captured.out


def test_start_stop_thread(simple_config, global_config):
    """Prueba que start inicie un hilo y stop lo detenga"""
    runner = TaskRunner(simple_config, global_config)

    with patch("threading.Thread") as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        mock_thread.is_alive.return_value = False  # Inicialmente parado

        runner.start()

        mock_thread_cls.assert_called_once()
        mock_thread.start.assert_called_once()

        # Simulamos que el hilo está vivo para probar el stop
        runner.thread = mock_thread
        mock_thread.is_alive.return_value = True

        with patch.object(runner, "_kill_process"):
            runner.stop()
            mock_thread.join.assert_called_once()
            assert runner.stop_event.is_set()


def test_check_max_attempts_cron(simple_config, global_config):
    """Prueba que con Cron se ignoren los intentos máximos"""
    simple_config.schedule_cron = "* * * * *"
    simple_config.times = 1
    runner = TaskRunner(simple_config, global_config)
    runner.attempts = 100
    assert runner._check_max_attempts() is False
