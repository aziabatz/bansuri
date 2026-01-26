import json
import pytest
import os
from bansuri.base.config_manager import ScriptConfig, BansuriConfig


def test_script_config_defaults():
    config = ScriptConfig(name="test", command="echo 1")
    assert config.times == 1
    assert config.on_fail == "stop"
    assert config.notify == "none"
    assert config.working_directory is None
    assert config.success_codes == [0]


def test_script_config_validation_success():
    c1 = ScriptConfig(name="t1", command="ls", timer="10s")
    c1.validate()

    c2 = ScriptConfig(name="t2", command="ls", schedule_cron="* * * * *")
    c2.validate()

    c3 = ScriptConfig(name="t3", command="ls", depends_on=["t1"])
    c3.validate()


def test_script_config_validation_failure():
    c = ScriptConfig(name="fail", command="ls")
    with pytest.raises(ValueError, match="requires 'schedule-cron', 'timer' or 'depends-on'"):
        c.validate()


def test_script_config_is_smart_script():
    c = ScriptConfig(name="t1", command="python script.py", timer="10s")
    assert c.is_smart_script is False


def test_bansuri_config_load(tmp_path):
    f = tmp_path / "scripts.json"
    content = {
        "version": "1.0",
        "notify_command": "mail -s",
        "scripts": [
            {
                "name": "task1",
                "command": "echo hello",
                "timer": "5m",
                "unknown-field": "ignored",
            }
        ],
    }
    f.write_text(json.dumps(content), encoding="utf-8")

    config = BansuriConfig.load_from_file(str(f))
    assert config.version == "1.0"
    assert config.notify_command == "mail -s"
    assert len(config.scripts) == 1
    assert config.scripts[0].name == "task1"


def test_bansuri_config_load_missing_file():
    with pytest.raises(FileNotFoundError):
        BansuriConfig.load_from_file("does_not_exist.json")


def test_bansuri_config_malformed_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{ invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Error decoding JSON"):
        BansuriConfig.load_from_file(str(f))


def test_bansuri_config_missing_required_fields(tmp_path):
    f = tmp_path / "missing.json"
    content = {"scripts": [{"command": "echo 1"}]}
    f.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required fields"):
        BansuriConfig.load_from_file(str(f))
