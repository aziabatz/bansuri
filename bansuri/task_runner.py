import subprocess
import threading
import time
import os
import signal
import sys
import importlib.util
from datetime import datetime
from typing import Optional, Any
from bansuri.base.config_manager import BansuriConfig, ScriptConfig
from bansuri.alerts.notifier import FailureInfo, Notifier
from bansuri.alerts.cmd_notifier import CommandNotifier


class TaskRunner:
    """
    This class manages the lifecycle of a single task.
    It handles process execution, log redirection, and other policies.
    """

    def __init__(self, config: ScriptConfig, bansuri_config: BansuriConfig):
        """
        TaskRunner initializer

        :param config: The configuration meant for the task
        :param bansuri_config: global Bansuri configuration
        """
        self.config = config  # The configuration from the JSON as dataclass
        self.bansuri_config = bansuri_config  # Global config
        self.process: Optional[subprocess.Popen] = None  # The process fo the script
        self.thread: Optional[threading.Thread] = (
            None  # The thread responsible for spawning the child process
        )
        self.stop_event = threading.Event()  # The event signal for START/STOP the child process
        self.attempts = 0  # Total attemps done
        self.watchdog_timeout = 120  # seconds to wait before force killing
        self.notifier: Optional[Notifier] = self._create_notifier()

    def log(self, message: str):
        """Fallback formatted log output"""
        # print(self.config)
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{self.config.name}] {message}",
            flush=True,
        )

    def start(self):
        """Starts the control thread if it is stopped"""
        if self.thread and self.thread.is_alive():
            return

        self.stop_event.clear()
        self.attempts = 0
        self.thread = threading.Thread(
            target=self._execution_loop, name=f"Runner-{self.config.name}", daemon=False
        )
        self.thread.start()
        self.log("Runner started.")

    def stop(self):
        """Sends the termination signal"""
        self.log("Stopping task...")
        self.stop_event.set()
        self._kill_process()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.log("Task stopped!")

    def _execution_loop(self):
        """Main loop: executes the task and handles job stop-start events

        Supports:
        - timer: Fixed interval execution
        """
        if self.config.schedule_cron:
            self._cron_execution_loop()
            return

        # Check if timer is configured
        # Treat "0", 0, "none" as service/dameon
        if self.config.timer and str(self.config.timer).lower() not in ["none", "0"]:
            self._timer_execution_loop()
        else:
            self._simple_execution_loop()

    def _check_max_attempts(self) -> bool:
        """Check if max attempts reached. Returns True if should stop."""

        if self.config.schedule_cron:
            return False

        try:
            max_times = int(self.config.times)
        except (ValueError, TypeError):
            max_times = 1

        if max_times > 0 and self.attempts >= max_times:
            self.log("Reached max attempts. Giving up...")
            return True
        return False

    def _create_notifier(self) -> Optional[Notifier]:
        """Create the appropriate notifier based on config."""
        if self.config.notify.lower() != "mail":
            return None

        notify_cmd = self.bansuri_config.notify_command
        if not notify_cmd:
            self.log("Notify is 'mail' but no notify_command configured. Notifications disabled.")
            return None

        return CommandNotifier(notify_cmd)

    def _handle_notify(self, return_code: int, output: str, error: str):
        """Handle notify policy after task failure.

        :param return_code: The process return code
        :param output: The stdout output from the failed process
        :param error: The stderr output from the failed process
        """
        if not self.notifier:
            return

        failure_info = FailureInfo(
            task_name=self.config.name,
            command=self.config.command,
            working_directory=self.config.working_directory,
            return_code=return_code,
            attempt=self.attempts,
            max_attempts=self.config.times,
            timestamp=datetime.now(),
            description=self.config.description,
            stdout=output,
            stderr=error,
        )

        self.log("Sending notification...")
        if self.notifier.notify(failure_info):
            self.log("Notification sent successfully")
        else:
            self.log("Failed to send notification")

    def _handle_on_fail(self) -> bool:
        """Handle on_fail policy after task completion. Returns True if should stop."""
        if self.config.on_fail.lower() != "restart":
            self.log(f"Task stopped. No automatic restart set (on_fail='{self.config.on_fail}')")

            return True
        return False

    def _simple_execution_loop(self):
        """Simple execution loop without timer"""
        while not self.stop_event.is_set():
            if self._check_max_attempts():
                break

            self.attempts += 1
            self._run_process()

            if self.stop_event.is_set():
                break

            if self._handle_on_fail():
                break

            self.log("Restarting in 5 secs...")
            if self.stop_event.wait(timeout=5):
                break

    def _timer_execution_loop(self):
        """Timer-based execution loop - runs task at fixed intervals"""
        timer_seconds = self._parse_timeout(self.config.timer)

        if not timer_seconds:
            self.log(f"ERROR: Invalid timer format '{self.config.timer}'. Running once.")
            self._run_process()
            return

        self.log(f"Timer configured: running every {self.config.timer} ({timer_seconds}s)")

        while not self.stop_event.is_set():
            if self._check_max_attempts():
                break

            self.attempts += 1
            self._run_process()

            if self.stop_event.is_set():
                break

            self.log(f"Waiting {self.config.timer} until next execution...")
            if self.stop_event.wait(timeout=timer_seconds):
                break

    def _cron_execution_loop(self):
        """Cron-based execution loop using croniter"""
        try:
            from croniter import croniter
        except ImportError:
            self.log(
                "ERROR: 'croniter' library is missing"
            )
            return

        if not self.config.schedule_cron or not croniter.is_valid(self.config.schedule_cron):
            self.log(f"ERROR: Invalid cron expression '{self.config.schedule_cron}'")
            return

        self.log(f"Cron configured: '{self.config.schedule_cron}'")

        while not self.stop_event.is_set():
            if self._check_max_attempts():
                break

            now = datetime.now()
            iter_cron = croniter(self.config.schedule_cron, now)
            next_run = iter_cron.get_next(datetime)
            delay = (next_run - now).total_seconds()

            if delay > 0:
                self.log(
                    f"Next execution at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {int(delay)}s)"
                )
                if self.stop_event.wait(timeout=delay):
                    break

            self.attempts += 1
            self._run_process()

    def _run_process(self):
        """Launches the subprocess or AbstractTask"""
        if self.config.no_interface:
            # Plain command execution (shell/bash)
            self._run_command()
        else:
            # Smart script (inherits AbstractTask) later...
            self._run_command()
            # self._run_smart_script() IGNORED FOR NOW!

    def _run_command(self):
        """Executes command directly as shell process"""
        cmd = self.config.command
        cwd = self.config.working_directory

        stdout_dest = subprocess.PIPE
        stderr_dest = subprocess.PIPE
        stdout_f, stderr_f = None, None
        start_time = time.time()
        timeout_seconds = self._parse_timeout(self.config.timeout)

        try:
            if self.config.stdout:
                stdout_path = self.config.stdout
                if cwd and not os.path.isabs(stdout_path):
                    stdout_path = os.path.join(cwd, stdout_path)

                stdout_f = open(stdout_path, "a")
                stdout_dest = stdout_f
                self.log(f"Redirecting stdout to {stdout_path}")

            if self.config.stderr and self.config.stderr != "combined":
                stderr_path = self.config.stderr
                if cwd and not os.path.isabs(stderr_path):
                    stderr_path = os.path.join(cwd, stderr_path)

                stderr_f = open(stderr_path, "a")
                stderr_dest = stderr_f
                self.log(f"Redirecting stderr to {stderr_path}")

            elif self.config.stderr == "combined":
                stderr_dest = subprocess.STDOUT
                self.log("Redirecting stderr to stdout")

            self.log(f"Executing shell command: {cmd}")

            self.process = subprocess.Popen(
                cmd,
                shell=True, # XXX: you better not know what can happen here...
                cwd=cwd,
                stdout=stdout_dest,
                stderr=stderr_dest,
                text=True,
                start_new_session=True,
            )

            # Wait while not stopped
            while not self.stop_event.is_set():
                if self.process.poll() is not None:
                    self.log(f"Process finished with code {self.process.returncode}")

                    if self.process.returncode not in self.config.success_codes:
                        outs, errs = "", ""
                        try:
                            outs, errs = self.process.communicate(timeout=1)
                            if outs:
                                self.log(f"Output:\n{outs.strip()}")
                            if errs:
                                self.log(f"Error:\n{errs.strip()}")
                        except Exception:
                            pass
                        self._handle_notify(self.process.returncode, outs, errs)
                    break

                if timeout_seconds and (time.time() - start_time > timeout_seconds):
                    self.log(f"Timeout exceeded ({self.config.timeout}). Killing process.")
                    self._kill_process()
                    self._handle_notify(-1, "", f"Timeout exceeded ({self.config.timeout})")
                    break
                time.sleep(1)

            # If we exit the loop but the process is still alive (manual stop), kill it
            if self.process.poll() is None:
                self._kill_process()

        except Exception as e:
            self.log(f"Critical error executing shell command: {e}")
        finally:
            if stdout_f:
                stdout_f.close()
            if stderr_f:
                stderr_f.close()

    def _run_smart_script(self):
        pass

    def _kill_process(self):
        """Kills the process gracefully (SIGTERM) -> [watchdog timer...] -> forcefully (SIGKILL)."""
        if not self.process or self.process.poll() is not None:
            return

        try:
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, signal.SIGTERM)

            # Simple watchdog
            for _ in range(self.watchdog_timeout):
                if self.process.poll() is not None:
                    return
                time.sleep(1)

            self.log("Forcing shutdown (SIGKILL)...")
            os.killpg(pgid, signal.SIGKILL)
        except Exception as e:
            self.log(f"Error killing process: {e}")

    def _parse_timeout(self, timeout_str: Optional[str]) -> Optional[int]:
        """Parses a timeout string (e.g., '30s', '5m') into seconds."""
        if not timeout_str:
            return None
        try:
            if str(timeout_str).isdigit():
                return int(timeout_str)

            unit = timeout_str[-1].lower()
            value = int(timeout_str[:-1])

            if unit == "s":
                return value
            if unit == "m":
                return value * 60
            if unit == "h":
                return value * 3600
        except (ValueError, IndexError):
            self.log(f"Warning: Invalid timeout format '{timeout_str}'. Ignoring.")
        return None
