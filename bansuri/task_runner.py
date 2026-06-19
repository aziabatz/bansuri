import subprocess
import threading
import time
import os
import signal
from datetime import datetime, timedelta
from typing import Any, Optional
from bansuri.base.config_manager import BansuriConfig, ScriptConfig
from bansuri.alerts.notifier import FailureInfo, Notifier
from bansuri.alerts.cmd_notifier import CommandNotifier

try:
    import psutil  # type: ignore[import-untyped]
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
        self.times = 0  # Total executions
        self.successful_times = 0
        self.failed_attempts = 0
        self.watchdog_timeout = 120  # seconds to wait before force killing
        self.notifier: Optional[Notifier] = self._create_notifier()
        self._psutil_proc = None
        self._children_cache: dict[int, Any] = {}  # cache for children procs
        self._last_stdout = ""
        self._last_stderr = ""
        self._last_return_code: Optional[int] = None

        self._status = "STOPPED"
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None

    @property
    def status(self):
        return self._status

    @property
    def last_run(self):
        return self._last_run

    @property
    def next_run(self):
        return self._next_run

    @property
    def attempts(self):
        """Backward-compatible alias for the total execution counter."""
        return self.times

    @attempts.setter
    def attempts(self, value):
        self.times = value

    def _has_timer_schedule(self) -> bool:
        """Return True when timer mode should be used."""
        return bool(self.config.timer and str(self.config.timer).lower() not in {"none", "0"})

    def _select_execution_loop(self):
        """Pick the execution loop that matches the current config."""
        if self.config.schedule_cron:
            return self._cron_execution_loop
        if self._has_timer_schedule():
            return self._timer_execution_loop
        return self._simple_execution_loop

    def _begin_execution(self):
        """Record the start of a new execution."""
        self.times += 1
        self._status = "EXECUTING"
        self._last_run = datetime.now()

    def _process_failed(self) -> bool:
        """Return True when the latest process finished with a failure code."""
        return bool(
            self._last_return_code is not None
            and self._last_return_code not in self.config.success_codes
        )

    def _record_failed_execution(self):
        """Track a failed execution and trigger notifications if needed."""
        self.failed_attempts += 1
        self._maybe_notify_failure()

    def _record_successful_execution(self):
        """Track a successful execution."""
        self.successful_times += 1
        self.failed_attempts = 0

    def _finalize_single_execution(self):
        """Finalize a one-shot execution without scheduling another run."""
        if self.stop_event.is_set():
            return

        if self._process_failed():
            self._record_failed_execution()
            self._status = "FAILED"
            return

        self._record_successful_execution()
        self._status = "COMPLETED"

    def _mark_simple_execution_success(self):
        """Finalize a successful simple execution."""
        self._record_successful_execution()
        self.log("Task completed successfully.")
        self._status = "COMPLETED"

    def _wait_for_restart_delay(self) -> bool:
        """Wait before retrying a failed execution."""
        restart_delay = self.config.restart_delay or "5s"
        restart_delay_seconds = self._parse_timeout(restart_delay) or 5
        self.log(f"Restarting in {restart_delay}...")
        self._status = "WAITING_RETRY"
        return self.stop_event.wait(timeout=restart_delay_seconds)

    def _handle_simple_failure(self) -> bool:
        """Handle failure policy for the simple execution loop."""
        self._record_failed_execution()

        if self.config.on_fail.lower() == "ignore":
            self._status = "COMPLETED"
            return True

        if self._handle_on_fail():
            self._status = "FAILED"
            return True

        return self._wait_for_restart_delay()

    def _handle_scheduled_failure(self) -> bool:
        """Handle failure policy for timer and cron loops."""
        self._record_failed_execution()
        if self._handle_on_fail():
            self._status = "FAILED"
            return True
        return False

    def get_resource_usage(self):
        """Returns resource stats from psutil cache"""
        if not self.process or self.process.poll() is not None:
            self._psutil_proc = None
            self._children_cache = {}
            return {"cpu": 0.0, "memory": 0}

        if psutil is None:
            return {"cpu": 0.0, "memory": 0}

        try:
            # we recreate the psutil object if the pid changed
            if not self._psutil_proc or self._psutil_proc.pid != self.process.pid:
                self._psutil_proc = psutil.Process(self.process.pid)
                self._children_cache = {}

            # shell stats (ignored most of the time)
            total_cpu = self._psutil_proc.cpu_percent(interval=None)
            total_mem = self._psutil_proc.memory_info().rss

            # Here is the worthy of tracking!
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

            # if the pid changes, then the children cache must change too
            self._children_cache = {
                pid: proc for pid, proc in self._children_cache.items() if pid in current_pids
            }

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
        self.times = 0
        self.successful_times = 0
        self.failed_attempts = 0
        self.thread = threading.Thread(
            target=self._execution_loop, name=f"Runner-{self.config.name}", daemon=False
        )
        self._status = "STARTING"
        self.thread.start()
        self.log("Runner started.")

    def stop(self) -> bool:
        """Stop the runner and report whether the worker thread fully exited."""
        self.log("Stopping task...")
        self._status = "STOPPING"
        self.stop_event.set()
        self._kill_process()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        if self.thread and self.thread.is_alive():
            self.log("Task is still stopping after 5 seconds.")
            return False
        self.log("Task stopped!")
        self._status = "STOPPED"
        return True

    def _execution_loop(self):
        """Main loop: executes the task and handles job stop-start events

        Supports:
        - timer: Fixed interval execution
        """
        try:
            execution_loop = self._select_execution_loop()
            execution_loop()
        finally:
            if self._status not in ["FAILED", "COMPLETED"]:
                self._status = "STOPPED"

    def _check_max_executions(self) -> bool:
        """Checks if max successful executions reached. Returns True if should stop.

        Applies to all execution modes (simple, timer, cron).
        times=0 means unlimited successful executions.
        For cron, runs counts are ignored
        """
        if self.config.schedule_cron:
            return False

        if self.config.times > 0 and self.successful_times >= self.config.times:
            self.log(f"Reached max successful executions ({self.config.times}). Stopping...")
            return True
        return False

    def _check_max_failed_attempts(self) -> bool:
        """Checks if max failed retry attempts reached. Returns True if should stop.

        Only for simple mode when on_fail is 'restart'.
        max_attempts=1 means no retries (stop after first failure).
        """
        if self.failed_attempts < self.config.max_attempts:
            return False

        self._status = "FAILED"
        self.log(f"Reached max attempts ({self.config.max_attempts}). Giving up...")
        return True

    def _create_notifier(self) -> Optional[Notifier]:
        """Create the appropriate notifier based on config."""
        notify_kind = self.config.notify.lower()
        if notify_kind not in ["mail", "command"]:
            return None

        notify_cmd = self.config.notify_command or self.bansuri_config.notify_command
        if not notify_cmd:
            self.log("Notifications enabled but no notify command configured. Notifications disabled.")
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

    def _maybe_notify_failure(self):
        """Send a failure notification only when the configured mode allows it."""
        if not self.notifier:
            return

        notify_mode = self.config.notify_mode.lower()
        threshold = max(1, self.config.notify_threshold)
        if notify_mode == "after-fail":
            should_notify = True
        elif notify_mode == "after-many":
            should_notify = self.failed_attempts == threshold
        elif notify_mode == "on-exhausted":
            should_notify = (
                self.failed_attempts >= self.config.max_attempts
                if self.config.on_fail.lower() == "restart"
                else True
            )
        else:
            should_notify = False

        if not should_notify:
            return

        self._handle_notify(
            self._last_return_code if self._last_return_code is not None else -1,
            self._last_stdout,
            self._last_stderr,
        )

    def _handle_on_fail(self) -> bool:
        """Handle on_fail policy after task completion. Returns True if should stop.

        Returns True if we should stop (either on_fail != 'restart' or max retries reached).
        """
        action = self.config.on_fail.lower()

        if action == "ignore":
            self.log("Task failed. Ignoring failure and continuing.")
            return False

        if action != "restart":
            self.log(f"Task stopped. No automatic restart set (on_fail='{self.config.on_fail}')")
            return True

        return self._check_max_failed_attempts()

    def _simple_execution_loop(self):
        """Simple execution loop without timer"""
        self._status = "RUNNING"
        while not self.stop_event.is_set():
            if self._check_max_executions():
                break

            self._begin_execution()
            self._run_process()

            if self.stop_event.is_set():
                break

            if self._process_failed():
                if self._handle_simple_failure():
                    break
                continue

            self._mark_simple_execution_success()
            break

    def _timer_execution_loop(self):
        """Timer-based execution loop - runs task at fixed intervals"""
        timer_seconds = self._parse_timeout(self.config.timer)

        if not timer_seconds:
            self.log(f"ERROR: Invalid timer format '{self.config.timer}'. Running once.")
            self._begin_execution()
            self._run_process()
            self._finalize_single_execution()
            return

        self.log(f"Timer configured: running every {self.config.timer} ({timer_seconds}s)")

        self._status = "RUNNING"
        while not self.stop_event.is_set():
            if self._check_max_executions():
                break

            self._begin_execution()
            self._run_process()

            if self._process_failed():
                if self._handle_scheduled_failure():
                    break
            else:
                self._record_successful_execution()

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
            from croniter import croniter  # type: ignore[import-untyped]
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

            self._begin_execution()
            self._run_process()

            if self._process_failed():
                if self._handle_scheduled_failure():
                    break
            else:
                self._record_successful_execution()

    def _run_process(self):
        """Launches the subprocess or AbstractTask"""
        self._run_command()
        # TODO Smart script (inherits AbstractTask) later -> _run_smart_script...

    def _reset_last_process_result(self):
        """Reset cached process output before starting a new command."""
        self.process = None
        self._last_stdout = ""
        self._last_stderr = ""
        self._last_return_code = None

    def _resolve_log_path(self, path: str, cwd: Optional[str]) -> str:
        """Resolve relative log paths against the task working directory."""
        if cwd and not os.path.isabs(path):
            return os.path.join(cwd, path)
        return path

    def _open_log_file(self, path: str, stream_name: str, cwd: Optional[str]):
        """Open and announce a redirected log file."""
        resolved_path = self._resolve_log_path(path, cwd)
        log_file = open(resolved_path, "a")
        self.log(f"Redirecting {stream_name} to {resolved_path}")
        return log_file

    def _configure_stdout_destination(self, cwd: Optional[str]):
        """Return the destination and file handle for stdout."""
        if self.config.stdout == "ignore":
            self.log("Ignoring stdout")
            return subprocess.DEVNULL, None

        if not self.config.stdout:
            return subprocess.PIPE, None

        stdout_file = self._open_log_file(self.config.stdout, "stdout", cwd)
        return stdout_file, stdout_file

    def _configure_stderr_destination(self, cwd: Optional[str]):
        """Return the destination and file handle for stderr."""
        if self.config.stderr == "ignore":
            self.log("Ignoring stderr")
            return subprocess.DEVNULL, None

        if self.config.stderr in ["combined", "$$combined"]:
            self.log("Redirecting stderr to stdout")
            return subprocess.STDOUT, None

        if not self.config.stderr:
            return subprocess.PIPE, None

        stderr_file = self._open_log_file(self.config.stderr, "stderr", cwd)
        return stderr_file, stderr_file

    def _capture_failed_process_output(self, process: subprocess.Popen):
        """Collect process output for failed executions."""
        outs, errs = "", ""
        try:
            outs, errs = process.communicate(timeout=1)
            outs = outs or ""
            errs = errs or ""
            if outs:
                self.log(f"Output:\n{outs.strip()}")
            if errs:
                self.log(f"Error:\n{errs.strip()}")
        except Exception:
            pass

        self._last_stdout = outs
        self._last_stderr = errs

    def _handle_process_exit(self) -> bool:
        """Return True once the current process has exited."""
        process = self.process
        if not process or process.poll() is None:
            return False

        self._last_return_code = process.returncode
        self.log(f"Process finished with code {process.returncode}")

        if process.returncode not in self.config.success_codes:
            self._capture_failed_process_output(process)

        return True

    def _handle_process_timeout(self, start_time: float, timeout_seconds: Optional[float]) -> bool:
        """Kill the process when it exceeds the configured timeout."""
        if not timeout_seconds or time.time() - start_time <= timeout_seconds:
            return False

        timeout_message = f"Timeout exceeded ({self.config.timeout})"
        self.log(f"{timeout_message}. Killing process.")
        self._kill_process()
        self._last_return_code = -1
        self._last_stderr = timeout_message
        return True

    def _wait_for_process_completion(self, start_time: float, timeout_seconds: Optional[float]):
        """Wait until the process exits, times out, or the runner is stopped."""
        while not self.stop_event.is_set():
            if self._handle_process_exit():
                return
            if self._handle_process_timeout(start_time, timeout_seconds):
                return
            time.sleep(1)

    def _ensure_process_stopped(self):
        """Stop the process if the monitoring loop exited while it was still running."""
        if self.process and self.process.poll() is None:
            self._kill_process()

    def _run_command(self):
        """Executes command directly as shell process"""
        cmd = self.config.command
        cwd = self.config.working_directory

        self._reset_last_process_result()

        stdout_dest = subprocess.PIPE
        stderr_dest = subprocess.PIPE
        stdout_f, stderr_f = None, None
        start_time = time.time()
        timeout_seconds = self._parse_timeout(self.config.timeout)

        try:
            stdout_dest, stdout_f = self._configure_stdout_destination(cwd)
            stderr_dest, stderr_f = self._configure_stderr_destination(cwd)

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

            self._wait_for_process_completion(start_time, timeout_seconds)
            self._ensure_process_stopped()

        except Exception as e:
            error_message = f"Critical error executing shell command: {e}"
            self.log(error_message)
            self._last_return_code = -1
            self._last_stderr = error_message
            self._ensure_process_stopped()
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
            self.process.wait(timeout=self.watchdog_timeout)
            return

        except subprocess.TimeoutExpired:
            self.log("Forcing shutdown (SIGKILL)...")
            os.killpg(pgid, signal.SIGKILL)
        except Exception as e:
            self.log(f"Error killing process: {e}")

    def _parse_timeout(self, timeout_str: Optional[str]) -> Optional[float]:
        """Parses a timeout string (e.g., '30s', '5m') into seconds."""
        if not timeout_str:
            return None
        try:
            if str(timeout_str).isdigit():
                return int(timeout_str)

            normalized = str(timeout_str).strip().lower()

            if normalized.endswith("ms"):
                return int(normalized[:-2]) / 1000

            unit = normalized[-1]
            value = int(normalized[:-1])

            if unit == "s":
                return value
            if unit == "m":
                return value * 60
            if unit == "h":
                return value * 3600
            if unit == "d":
                return value * 86400
        except (ValueError, IndexError):
            self.log(f"Warning: Invalid timeout format '{timeout_str}'. Ignoring.")
        return None
