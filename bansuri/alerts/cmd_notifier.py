import subprocess

from bansuri.alerts.notifier import FailureInfo, Notifier

class CommandNotifier(Notifier):
    """Notify via shell command execution."""

    def __init__(self, notify_command: str, timeout: int = 30):
        self.notify_command = notify_command
        self.timeout = timeout

    def notify(self, failure_info: FailureInfo) -> bool:
        output_cmd = self._build_output_command(failure_info)
        full_cmd = f"{self.notify_command} {output_cmd}"

        try:
            print(f"Running: {full_cmd}")
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
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

    def _build_output_command(self, info: FailureInfo) -> str:
        """Build command with message
            It supports multiline text
        """
        lines = [
            f"=== Task Failure ===",
            "",
            f"Task '{info.task_name}' has failed.",
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

        lines.extend(["", "---", "This is an automated message from orchestrator."])

        message = "\\n".join(lines)
        message = message.replace("'", "'\"'\"'")  # ' -> '"'"'
        # FIXME ESCAPE ALL CHARACTERS!

        full_cmd = f"\"printf '%b' '{message}'\""
        #print(full_cmd)
        return full_cmd
