import shlex
from typing import List, Optional


def build_safe_command_array(notify_command: str) -> List[str]:
    """
    Parse notify_command into an argument list for subprocess.run(shell=False).

    The failure message is sent separately via stdin.
    """
    validate_notify_command(notify_command)

    try:
        return shlex.split(notify_command)
    except ValueError as exc:
        raise ValueError(f"Failed to parse notify_command: {exc}")


def validate_notify_command(command: Optional[str]) -> bool:
    """
    Validate that notify_command is in acceptable format.

    Args:
        command: Command string to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    if command is None:
        return True

    if not isinstance(command, str):
        raise ValueError("notify_command must be a string")

    if not command.strip():
        raise ValueError("notify_command cannot be whitespace only")

    try:
        cmd_parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"notify_command has invalid shell syntax: {exc}")

    if not cmd_parts:
        raise ValueError("notify_command resulted in empty command")

    return True
