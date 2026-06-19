import signal
import sys
from unittest.mock import MagicMock, patch

import pytest

from bansuri.base.config_manager import BansuriConfig, ScriptConfig
from bansuri.master import Orchestrator, main


@pytest.fixture
def orchestrator_factory():
    with (
        patch("bansuri.master.signal.signal") as mock_signal,
        patch("bansuri.master.Dashboard") as mock_dashboard_cls,
    ):
        dashboard = MagicMock()
        mock_dashboard_cls.return_value = dashboard

        def _make(**kwargs):
            orchestrator = Orchestrator(**kwargs)
            return orchestrator, dashboard, mock_signal, mock_dashboard_cls

        yield _make


def test_orchestrator_initializes_dashboard_from_environment(monkeypatch, orchestrator_factory):
    monkeypatch.setenv("BANSURI_USER", "alice")
    monkeypatch.setenv("BANSURI_PASS", "secret")
    monkeypatch.setenv("BANSURI_PORT", "9090")

    orchestrator, _, mock_signal, mock_dashboard_cls = orchestrator_factory(
        config_file="conf.json",
        check_interval=10,
    )

    assert orchestrator.config_file == "conf.json"
    assert orchestrator.check_interval == 10
    assert mock_signal.call_count == 2
    mock_signal.assert_any_call(signal.SIGTERM, orchestrator.signal_handler)
    mock_signal.assert_any_call(signal.SIGINT, orchestrator.signal_handler)
    mock_dashboard_cls.assert_called_once_with(
        orchestrator,
        username="alice",
        password="secret",
        port=9090,
    )


def test_sync_tasks_adds_new_runner(orchestrator_factory):
    orchestrator, _, _, _ = orchestrator_factory(config_file="scripts.json")
    task = ScriptConfig(name="backup", command="echo backup", timer="1m")
    config = BansuriConfig(version="1.0", scripts=[task])

    with (
        patch("bansuri.master.BansuriConfig.load_from_file", return_value=config),
        patch("bansuri.master.TaskRunner") as mock_runner_cls,
    ):
        runner = MagicMock()
        mock_runner_cls.return_value = runner

        orchestrator.sync_tasks()

    assert orchestrator.runners == {"backup": runner}
    mock_runner_cls.assert_called_once_with(task, config)
    runner.start.assert_called_once()


def test_sync_tasks_removes_runner_missing_from_new_config(orchestrator_factory):
    orchestrator, _, _, _ = orchestrator_factory(config_file="scripts.json")
    old_runner = MagicMock()
    old_runner.config = ScriptConfig(name="backup", command="echo backup", timer="1m")
    orchestrator.runners = {"backup": old_runner}

    with patch(
        "bansuri.master.BansuriConfig.load_from_file",
        return_value=BansuriConfig(version="1.0", scripts=[]),
    ):
        orchestrator.sync_tasks()

    assert orchestrator.runners == {}
    old_runner.stop.assert_called_once()


def test_sync_tasks_restarts_runner_when_configuration_changes(orchestrator_factory):
    orchestrator, _, _, _ = orchestrator_factory(config_file="scripts.json")
    old_task = ScriptConfig(name="backup", command="echo backup", timer="1m")
    new_task = ScriptConfig(name="backup", command="echo updated", timer="1m")
    old_runner = MagicMock()
    old_runner.config = old_task
    orchestrator.runners = {"backup": old_runner}
    config = BansuriConfig(version="1.0", scripts=[new_task])

    with (
        patch("bansuri.master.BansuriConfig.load_from_file", return_value=config),
        patch("bansuri.master.TaskRunner") as mock_runner_cls,
    ):
        new_runner = MagicMock()
        mock_runner_cls.return_value = new_runner

        orchestrator.sync_tasks()

    old_runner.stop.assert_called_once()
    assert orchestrator.runners["backup"] is new_runner
    new_runner.start.assert_called_once()


def test_sync_tasks_delays_restart_while_previous_runner_is_still_stopping(orchestrator_factory):
    orchestrator, _, _, _ = orchestrator_factory(config_file="scripts.json")
    old_task = ScriptConfig(name="backup", command="echo backup", timer="1m")
    new_task = ScriptConfig(name="backup", command="echo updated", timer="1m")
    old_runner = MagicMock()
    old_runner.config = old_task
    old_runner.stop.return_value = False
    orchestrator.runners = {"backup": old_runner}
    config = BansuriConfig(version="1.0", scripts=[new_task])

    with (
        patch("bansuri.master.BansuriConfig.load_from_file", return_value=config),
        patch("bansuri.master.TaskRunner") as mock_runner_cls,
    ):
        orchestrator.sync_tasks()

    old_runner.stop.assert_called_once()
    mock_runner_cls.assert_not_called()
    assert orchestrator.runners["backup"] is old_runner


def test_stop_all_stops_dashboard_and_all_runners(orchestrator_factory):
    orchestrator, dashboard, _, _ = orchestrator_factory()
    orchestrator.runners = {
        "one": MagicMock(),
        "two": MagicMock(),
    }

    orchestrator.stop_all()

    dashboard.stop.assert_called_once()
    orchestrator.runners["one"].stop.assert_called_once()
    orchestrator.runners["two"].stop.assert_called_once()


def test_run_starts_dashboard_and_syncs_until_stop(orchestrator_factory):
    orchestrator, dashboard, _, _ = orchestrator_factory(check_interval=1)

    def stop_after_first_sync():
        orchestrator.should_stop = True

    orchestrator.sync_tasks = MagicMock(side_effect=stop_after_first_sync)

    with patch("bansuri.master.time.sleep") as mock_sleep:
        orchestrator.run()

    dashboard.start.assert_called_once()
    orchestrator.sync_tasks.assert_called_once()
    mock_sleep.assert_called_once_with(1)


def test_signal_handler_stops_all_and_exits(orchestrator_factory):
    orchestrator, _, _, _ = orchestrator_factory()
    orchestrator.stop_all = MagicMock()

    with patch("bansuri.master.sys.exit") as mock_exit:
        orchestrator.signal_handler(signal.SIGTERM, None)

    orchestrator.stop_all.assert_called_once()
    mock_exit.assert_called_once_with(0)


def test_main_uses_cwd_default_config_path():
    with (
        patch("bansuri.master.Orchestrator") as mock_orchestrator_cls,
        patch.object(sys, "argv", ["bansuri"]),
    ):
        orchestrator = mock_orchestrator_cls.return_value

        main()

    mock_orchestrator_cls.assert_called_once_with(config_file="scripts.json", check_interval=5)
    orchestrator.run.assert_called_once()


def test_main_accepts_config_override_from_cli():
    with (
        patch("bansuri.master.Orchestrator") as mock_orchestrator_cls,
        patch.object(sys, "argv", ["bansuri", "-c", "conf.json"]),
    ):
        orchestrator = mock_orchestrator_cls.return_value

        main()

    mock_orchestrator_cls.assert_called_once_with(config_file="conf.json", check_interval=5)
    orchestrator.run.assert_called_once()
