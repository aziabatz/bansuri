import json
from textwrap import dedent

import pytest

from bansuri.base.config_manager import BansuriConfig, ScriptConfig


@pytest.fixture
def write_config(tmp_path):
    def _write_config(payload, *, filename="scripts.jsonc"):
        path = tmp_path / filename
        if isinstance(payload, str):
            path.write_text(dedent(payload).strip(), encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return _write_config


def test_script_config_defaults_are_initialized():
    config = ScriptConfig(name="backup", command="echo backup", timer="1m")

    assert config.user is None
    assert config.working_directory is None
    assert config.no_interface is False
    assert config.times == 0
    assert config.max_attempts == 1
    assert config.on_fail == "stop"
    assert config.success_codes == [0]
    assert config.notify == "none"
    assert config.notify_mode == "after-fail"
    assert config.notify_threshold == 1
    assert config.restart_delay == "5s"


@pytest.mark.parametrize(
    "execution_kwargs",
    [
        pytest.param({"timer": "10s"}, id="timer"),
        pytest.param({"schedule_cron": "*/5 * * * *"}, id="cron"),
        pytest.param({"depends_on": ["bootstrap"]}, id="dependency"),
    ],
)
def test_script_config_validate_accepts_supported_execution_modes(execution_kwargs):
    config = ScriptConfig(name="task", command="echo 1", **execution_kwargs)

    config.validate()


@pytest.mark.parametrize(
    "execution_kwargs",
    [
        pytest.param({}, id="no-schedule"),
        pytest.param({"timer": "none"}, id="explicit-none-timer"),
    ],
)
def test_script_config_validate_rejects_missing_schedule_and_dependencies(execution_kwargs):
    config = ScriptConfig(name="task", command="echo 1", **execution_kwargs)

    with pytest.raises(ValueError, match="requires 'schedule-cron', 'timer' or 'depends-on'"):
        config.validate()


@pytest.mark.parametrize(
    ("scheduling", "expected_cron", "expected_timer"),
    [
        pytest.param({"scheduler": "cron", "params": "0 3 * * *"}, "0 3 * * *", None, id="cron"),
        pytest.param({"scheduler": "timer", "params": "15m"}, None, "15m", id="timer"),
        pytest.param({"scheduler": "none"}, None, "0", id="service-mode"),
    ],
)
def test_load_from_file_maps_grouped_scheduler_variants(
    write_config, scheduling, expected_cron, expected_timer
):
    config_path = write_config(
        {
            "scripts": [
                {
                    "general": {"name": "scheduler-task", "command": "echo run"},
                    "scheduling": scheduling,
                    "failure-control": {},
                    "logging": {},
                }
            ]
        }
    )

    config = BansuriConfig.load_from_file(str(config_path))
    script = config.scripts[0]

    assert script.schedule_cron == expected_cron
    assert script.timer == expected_timer


def test_load_from_file_normalizes_grouped_scripts_and_merges_defaults(write_config):
    config_path = write_config(
        {
            "version": "2.0",
            "notify_command": "/usr/local/bin/global-notify",
            "defaults": {
                "scheduling": {"timeout": "15m", "max-runs": "2"},
                "failure-control": {
                    "on-fail": "restart",
                    "max-attempts": "4",
                    "restart-params": {"after": "30s"},
                    "notify": {
                        "enabled": "true",
                        "mode": "after-many",
                        "after-threshold": "3",
                        "handler": "command",
                        "handler-config": "/usr/local/bin/default-notify",
                    },
                },
                "logging": {"stdout": "/tmp/default.log", "stderr": "$$combined"},
            },
            "scripts": [
                {
                    "general": {
                        "name": "cleanup",
                        "command": "echo cleanup",
                        "description": "nightly cleanup",
                        "working-directory": "/srv/jobs",
                    },
                    "scheduling": {"scheduler": "timer", "params": "5m"},
                    "failure-control": {
                        "notify": {"handler-config": "/usr/local/bin/task-notify"}
                    },
                    "logging": {},
                }
            ],
        }
    )

    config = BansuriConfig.load_from_file(str(config_path))
    script = config.scripts[0]

    assert config.version == "2.0"
    assert config.notify_command == "/usr/local/bin/global-notify"
    assert script.name == "cleanup"
    assert script.command == "echo cleanup"
    assert script.description == "nightly cleanup"
    assert script.working_directory == "/srv/jobs"
    assert script.timer == "5m"
    assert script.schedule_cron is None
    assert script.timeout == "15m"
    assert script.times == 2
    assert script.max_attempts == 4
    assert script.on_fail == "restart"
    assert script.stdout == "/tmp/default.log"
    assert script.stderr == "combined"
    assert script.notify == "command"
    assert script.notify_mode == "after-many"
    assert script.notify_threshold == 3
    assert script.notify_command == "/usr/local/bin/task-notify"
    assert script.restart_delay == "30s"


def test_load_from_file_supports_legacy_flat_scripts_and_warns_on_unknown_fields(
    write_config, capsys
):
    config_path = write_config(
        {
            "scripts": [
                {
                    "name": "legacy-task",
                    "command": "echo legacy",
                    "depends-on": ["bootstrap"],
                    "working-directory": "/tmp/legacy",
                    "unknown-field": "ignored",
                }
            ]
        }
    )

    config = BansuriConfig.load_from_file(str(config_path))
    script = config.scripts[0]

    assert config.version == "UNKNOWN"
    assert script.depends_on == ["bootstrap"]
    assert script.working_directory == "/tmp/legacy"

    captured = capsys.readouterr()
    assert "Found key unknown_field but not recognized as a bansuri valid field" in captured.out


def test_load_from_file_supports_json_with_comments(write_config):
    config_path = write_config(
        """
        {
          // Top-level comment.
          "version": "1.0",
          "scripts": [
            {
              "name": "quoted-comments",
              "command": "printf \\"// keep /* this */\\"",
              "timer": "5m"
            }
          ]
          /* trailing block comment */
        }
        """
    )

    config = BansuriConfig.load_from_file(str(config_path))

    assert config.scripts[0].command == 'printf "// keep /* this */"'


def test_load_from_file_raises_for_missing_file():
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        BansuriConfig.load_from_file("does-not-exist.json")


def test_load_from_file_raises_for_malformed_json(write_config):
    config_path = write_config("{ invalid json", filename="broken.json")

    with pytest.raises(ValueError, match="Error decoding JSON"):
        BansuriConfig.load_from_file(str(config_path))


def test_load_from_file_reports_missing_required_fields_with_script_name(write_config):
    config_path = write_config(
        {
            "scripts": [
                {
                    "name": "missing-command",
                    "timer": "5m",
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="Missing required fields in script 'missing-command'"):
        BansuriConfig.load_from_file(str(config_path))


def test_load_from_file_wraps_validation_errors_with_script_name(write_config):
    config_path = write_config(
        {
            "scripts": [
                {
                    "name": "unscheduled",
                    "command": "echo unscheduled",
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="Validation error in 'unscheduled'"):
        BansuriConfig.load_from_file(str(config_path))


@pytest.mark.parametrize(
    ("notify_config", "expected_message"),
    [
        pytest.param(
            {
                "enabled": True,
                "handler": "email",
                "handler-config": "ops@example.com",
            },
            "notify handler 'email' is not supported yet. Notifications disabled.",
            id="unsupported-handler",
        ),
        pytest.param(
            {
                "enabled": True,
                "handler": "command",
                "handler-config": {"path": "/usr/local/bin/notify"},
            },
            "command notify handler requires string handler-config. Notifications disabled.",
            id="non-string-command-config",
        ),
    ],
)
def test_load_from_file_disables_invalid_notify_config_and_logs_warning(
    write_config, capsys, notify_config, expected_message
):
    config_path = write_config(
        {
            "scripts": [
                {
                    "general": {"name": "notify-task", "command": "echo 1"},
                    "scheduling": {"scheduler": "timer", "params": "5m"},
                    "failure-control": {"notify": notify_config},
                    "logging": {},
                }
            ]
        }
    )

    config = BansuriConfig.load_from_file(str(config_path))
    script = config.scripts[0]

    assert script.notify == "none"
    assert script.notify_command is None

    captured = capsys.readouterr()
    assert expected_message in captured.out


def test_merge_dicts_recursively_merges_nested_values():
    merged = BansuriConfig._merge_dicts(
        {
            "notify": {"enabled": "true", "mode": "after-fail"},
            "timeout": "5m",
        },
        {
            "notify": {"mode": "after-many", "after-threshold": "3"},
            "timer": "10m",
        },
    )

    assert merged == {
        "notify": {
            "enabled": "true",
            "mode": "after-many",
            "after-threshold": "3",
        },
        "timeout": "5m",
        "timer": "10m",
    }
