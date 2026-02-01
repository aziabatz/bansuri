import subprocess
import threading
import time
import os
import signal
from datetime import datetime, timedelta
from typing import Optional, Any
from bansuri.base.config_manager import BansuriConfig, ScriptConfig
from bansuri.alerts.notifier import FailureInfo, Notifier
from bansuri.alerts.cmd_notifier import CommandNotifier

try:
    import psutil
except ImportError:
    psutil = None


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
        self.attempts = 0  # Total successful executions
        self.failed_attempts = 0
        self.watchdog_timeout = 120  # seconds to wait before force killing
        self.notifier: Optional[Notifier] = self._create_notifier()
        self._psutil_proc = None  # Cache for psutil process object
        self._children_cache = {}  # Cache for children processes to track CPU correctly

        # Dashboard properties
        self._status = "STOPPED"
        self._last_run = None
        self._next_run = None

    @property
    def status(self):
        return self._status

    @property
    def last_run(self):
        return self._last_run

    @property
    def next_run(self):
        return self._next_run

    def get_resource_usage(self):
        """Returns CPU percent and Memory usage (bytes) safely."""
        if not self.process or self.process.poll() is not None:
            self._psutil_proc = None
            self._children_cache = {}
            return {"cpu": 0.0, "memory": 0}

        if psutil is None:
            return {"cpu": 0.0, "memory": 0}

        try:
            # Re-create psutil object only if PID changed (optimization)
            if not self._psutil_proc or self._psutil_proc.pid != self.process.pid:
                self._psutil_proc = psutil.Process(self.process.pid)
                self._children_cache = {}

            # Main process stats (The Shell)
            total_cpu = self._psutil_proc.cpu_percent(interval=None)
            total_mem = self._psutil_proc.memory_info().rss

            # Children stats (The actual command)
            # We must cache children objects because cpu_percent needs state (interval=None)
            try:
                current_children = self._psutil_proc.children(recursive=True)
            except psutil.NoSuchProcess:
                return {"cpu": total_cpu, "memory": total_mem}

            current_pids = set()
            for child in current_children:
                current_pids.add(child.pid)
                if child.pid not in self._children_cache:
                    self._children_cache[child.pid] = child
                    child.cpu_percent(interval=None)  # Prime the CPU counter

            # Remove dead children from cache
            self._children_cache = {
                pid: proc for pid, proc in self._children_cache.items() if pid in current_pids
            }

            # Sum up children resources
            for child in self._children_cache.values():
                try:
                    total_cpu += child.cpu_percent(interval=None)
                    total_mem += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return {
                "cpu": total_cpu,
                "memory": total_mem,
            }
        except Exception as e:
            # Fallback if psutil missing or process died during call
            if not isinstance(e, psutil.NoSuchProcess):
                self.log(f"Resource stats error: {e}")
            return {"cpu": 0.0, "memory": 0}

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
        self.failed_attempts = 0
        self.thread = threading.Thread(
            target=self._execution_loop, name=f"Runner-{self.config.name}", daemon=False
        )
        self._status = "STARTING"
        self.thread.start()
        self.log("Runner started.")

    def stop(self):
        """Sends the termination signal"""
        self.log("Stopping task...")
        self._status = "STOPPING"
        self.stop_event.set()
        self._kill_process()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.log("Task stopped!")
        self._status = "STOPPED"

    def _execution_loop(self):
        """Main loop: executes the task and handles job stop-start events

        Supports:
        - timer: Fixed interval execution
        """
        try:
            if self.config.schedule_cron:
                self._cron_execution_loop()
                return

            # Check if timer is configured
            # Treat "0", 0, "none" as service/dameon
            if self.config.timer and str(self.config.timer).lower() not in ["none", "0"]:
                self._timer_execution_loop()
            else:
                self._simple_execution_loop()
        finally:
            self._status = "STOPPED"

    def _check_max_executions(self) -> bool:
        """Checks if max successful executions reached. Returns True if should stop.

        Applies to all execution modes (simple, timer, cron).
        times=0 means unlimited executions.
        For cron, runs counts are ignored
        """
        if self.config.schedule_cron:
            return False

        if self.config.times > 0 and self.attempts >= self.config.times:
            self.log(f"Reached max executions ({self.config.times}). Stopping...")
            return True
        return False

    def _check_max_failed_attempts(self) -> bool:
        """Checks if max failed retry attempts reached. Returns True if should stop.

        Only for simple mode when on_fail is 'restart'.
        max_attempts=1 means no retries (stop after first failure).
        """
        if self.failed_attempts >= self.config.max_attempts:
            self.log(f"Reached max attempts ({self.config.max_attempts}). Giving up...")
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
            attempt=self.failed_attempts,
            max_attempts=self.config.max_attempts,
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
        """Handle on_fail policy after task completion. Returns True if should stop.

        Returns True if we should stop (either on_fail != 'restart' or max retries reached).
        """
        if self.config.on_fail.lower() != "restart":
            self.log(f"Task stopped. No automatic restart set (on_fail='{self.config.on_fail}')")
            return True

        # Check if we've exceeded max failed attempts
        if self._check_max_failed_attempts():
            return True

        return False

    def _simple_execution_loop(self):
        """Simple execution loop without timer"""
        self._status = "RUNNING"
        while not self.stop_event.is_set():
            if self._check_max_executions():
                break

            self.attempts += 1
            self.failed_attempts = 0

            self._status = "EXECUTING"
            self._last_run = datetime.now()
            self._run_process()

            if self.stop_event.is_set():
                break

            if self.process and self.process.returncode not in self.config.success_codes:
                self.failed_attempts += 1
                if self._handle_on_fail():
                    self._status = "FAILED"
                    break
                self.log("Restarting in 5 secs...")
                self._status = "WAITING_RETRY"
                if self.stop_event.wait(timeout=5):
                    break
            else:
                self.failed_attempts = 0
                self.log("Task completed successfully.")
                self._status = "COMPLETED"

    def _timer_execution_loop(self):
        """Timer-based execution loop - runs task at fixed intervals"""
        timer_seconds = self._parse_timeout(self.config.timer)

        if not timer_seconds:
            self.log(f"ERROR: Invalid timer format '{self.config.timer}'. Running once.")
            self._status = "EXECUTING"
            self._last_run = datetime.now()
            self._run_process()
            self._status = "COMPLETED"
            return

        self.log(f"Timer configured: running every {self.config.timer} ({timer_seconds}s)")

        self._status = "RUNNING"
        while not self.stop_event.is_set():
            if self._check_max_executions():
                break

            self.attempts += 1
            self._status = "EXECUTING"
            self._last_run = datetime.now()
            self._run_process()

            if self.stop_event.is_set():
                break

            self.log(f"Waiting {self.config.timer} until next execution...")
            self._status = "WAITING"
            self._next_run = datetime.now() + timedelta(seconds=timer_seconds)
            if self.stop_event.wait(timeout=timer_seconds):
                break

    def _cron_execution_loop(self):
        """Cron-based execution loop using croniter"""
        try:
            from croniter import croniter
        except ImportError:
            self.log("ERROR: 'croniter' library is missing")
            return

        if not self.config.schedule_cron or not croniter.is_valid(self.config.schedule_cron):
            self.log(f"ERROR: Invalid cron expression '{self.config.schedule_cron}'")
            return

        self.log(f"Cron configured: '{self.config.schedule_cron}'")

        self._status = "RUNNING"
        while not self.stop_event.is_set():
            if self._check_max_executions():
                break

            now = datetime.now()
            iter_cron = croniter(self.config.schedule_cron, now)
            next_run = iter_cron.get_next(datetime)
            self._next_run = next_run
            delay = (next_run - now).total_seconds()

            if delay > 0:
                self.log(
                    f"Next execution at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {int(delay)}s)"
                )
                self._status = "WAITING"
                if self.stop_event.wait(timeout=delay):
                    break

            self.attempts += 1
            self._status = "EXECUTING"
            self._last_run = datetime.now()
            self._run_process()

    def _run_process(self):
        """Launches the subprocess or AbstractTask"""
        self._run_command()
        # TODO Smart script (inherits AbstractTask) later -> _run_smart_script...

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
                shell=True,  # XXX: you better not know what can happen here...
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
        raise NotImplementedError

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
