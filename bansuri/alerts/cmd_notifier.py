import subprocess

from bansuri.alerts.notifier import FailureInfo, Notifier
from bansuri.alerts.command_safety import build_safe_command_array


class CommandNotifier(Notifier):
    """Notify via shell command execution."""

    def __init__(self, notify_command: str, timeout: int = 30):
        self.notify_command = notify_command
        self.timeout = timeout

    def notify(self, failure_info: FailureInfo) -> bool:
        message = self._build_message(failure_info)

        try:
            command = build_safe_command_array(self.notify_command)
            print(f"Running: {self.notify_command}")
            result = subprocess.run(
                command,
                capture_output=True,
                input=message,
                shell=False,
                text=True,
                timeout=self.timeout,
            )

            print(f"returncode: {result.returncode}")
            if result.returncode == 0:
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return True
            else:
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"Exception: {e}")
            return False

    def _build_message(self, info: FailureInfo) -> str:
        """Build the notification message sent to the notify command."""
        lines = [
            f"=== Task Failure ===",
            "",
            f"Task {info.task_name} has failed.",
            "",
            "--- Task Details ---",
            f"Name:              {info.task_name}",
            f"Command:           {info.command}",
            f"Working Directory: {info.working_directory or 'N/A'}",
            f"Return Code:       {info.return_code}",
            f"Attempt:           {info.attempt}/{info.max_attempts}",
            f"Timestamp:         {info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if info.description:
            lines.append(f"Description:       {info.description}")

        if info.stdout:
            lines.extend(["", "--- Output ---", info.stdout.strip()])

        if info.stderr:
            lines.extend(["", "--- Error ---", info.stderr.strip()])

        lines.extend(["", "---", "This is an automated message from Orchestrator."])

        return "\n".join(lines)
