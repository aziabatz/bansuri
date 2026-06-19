import pytest

from bansuri.alerts.command_safety import build_safe_command_array, validate_notify_command


def test_validate_notify_command_accepts_none_and_normal_command():
    assert validate_notify_command(None) is True
    assert validate_notify_command("send-alert --channel ops") is True


@pytest.mark.parametrize(
    ("command", "expected_message"),
    [
        pytest.param(123, "notify_command must be a string", id="non-string"),
        pytest.param("   ", "notify_command cannot be whitespace only", id="blank"),
        pytest.param('echo "unterminated', "notify_command has invalid shell syntax", id="bad-shell"),
    ],
)
def test_validate_notify_command_rejects_invalid_values(command, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        validate_notify_command(command)


def test_build_safe_command_array_splits_shell_words():
    command = 'send-alert --channel ops "task failed"'

    assert build_safe_command_array(command) == [
        "send-alert",
        "--channel",
        "ops",
        "task failed",
    ]
