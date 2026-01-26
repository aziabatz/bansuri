import pytest
import signal
import sys
from unittest.mock import MagicMock, patch, call
from bansuri.master import Orchestrator
from bansuri.base.config_manager import ScriptConfig, BansuriConfig


@pytest.fixture
def mock_runner_cls():
    with patch("bansuri.master.TaskRunner") as mock:
        mock.side_effect = lambda *args, **kwargs: MagicMock()
        yield mock


@pytest.fixture
def mock_config_load():
    with patch("bansuri.base.config_manager.BansuriConfig.load_from_file") as mock:
        yield mock


def test_orchestrator_init():
    with patch("signal.signal") as mock_signal:
        orch = Orchestrator("conf.json", 10)
        assert orch.config_file == "conf.json"
        assert orch.check_interval == 10
        assert mock_signal.call_count == 2


def test_sync_tasks_add_new(mock_runner_cls, mock_config_load):
    orch = Orchestrator(config_file="test.json")

    cfg = ScriptConfig(name="t1", command="ls", timer="10s")
    mock_config_load.return_value = BansuriConfig(version="1", scripts=[cfg])

    orch.sync_tasks()

    assert "t1" in orch.runners
    mock_runner_cls.assert_called_with(cfg, mock_config_load.return_value)
    orch.runners["t1"].start.assert_called_once()


def test_sync_tasks_remove_old(mock_runner_cls, mock_config_load):
    orch = Orchestrator(config_file="test.json")

    cfg = ScriptConfig(name="t1", command="ls", timer="10s")
    mock_config_load.return_value = BansuriConfig(version="1", scripts=[cfg])
    orch.sync_tasks()

    runner_instance = orch.runners["t1"]

    mock_config_load.return_value = BansuriConfig(version="1", scripts=[])
    orch.sync_tasks()

    assert "t1" not in orch.runners
    runner_instance.stop.assert_called_once()


def test_sync_tasks_update_existing(mock_runner_cls, mock_config_load):
    orch = Orchestrator(config_file="test.json")

    cfg1 = ScriptConfig(name="t1", command="ls", timer="10s")
    mock_config_load.return_value = BansuriConfig(version="1", scripts=[cfg1])
    orch.sync_tasks()

    first_runner = orch.runners["t1"]

    cfg2 = ScriptConfig(name="t1", command="ls -la", timer="10s")
    mock_config_load.return_value = BansuriConfig(version="1", scripts=[cfg2])

    first_runner.stop.reset_mock()

    orch.sync_tasks()

    assert "t1" in orch.runners
    assert orch.runners["t1"] != first_runner

    first_runner.stop.assert_called_once()
    orch.runners["t1"].start.assert_called_once()


def test_stop_all(mock_runner_cls):
    orch = Orchestrator()
    r1 = MagicMock()
    r2 = MagicMock()
    orch.runners = {"t1": r1, "t2": r2}

    orch.stop_all()

    r1.stop.assert_called_once()
    r2.stop.assert_called_once()


def test_run_loop(mock_config_load):
    orch = Orchestrator(check_interval=0.1)
    orch.sync_tasks = MagicMock()

    # Run once then stop via exception
    with patch("time.sleep", side_effect=InterruptedError):
        try:
            orch.run()
        except InterruptedError:
            pass
    orch.sync_tasks.assert_called()


def test_signal_handler():
    orch = Orchestrator("conf.json")
    orch.stop_all = MagicMock()

    with patch("sys.exit") as mock_exit:
        orch.signal_handler(signal.SIGTERM, None)

        orch.stop_all.assert_called_once()
        mock_exit.assert_called_once_with(0)


def test_log_output(capsys):
    orch = Orchestrator("conf.json")
    orch._log("test log")
    captured = capsys.readouterr()
    assert "[MASTER] test log" in captured.out
