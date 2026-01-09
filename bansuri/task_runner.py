import subprocess
import threading
import time
import os
import signal
from datetime import datetime
from typing import Optional
from bansuri.base.config_manager import ScriptConfig
from croniter import croniter


class TaskRunner:
    """
    This class manages the lifecycle of a single task.
    It handles process execution, log redirection, and other policies.
    """

    def __init__(self, config: ScriptConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.attempts = 0
        self.watchdog_timeout = 120  # seconds to wait before force killing

    def log(self, message: str):
        """Fallback formatted log output"""
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
        """Main loop: executes the task and handles job stop-start events"""
        while not self.stop_event.is_set():
            # Attempts control
            if self.config.times > 0 and self.attempts >= self.config.times:
                self.log("Reached max attempts. Giving up...")
                break

            self.attempts += 1
            self._run_process()

            if self.stop_event.is_set():
                break

            if self.config.on_fail != "restart":
                self.log("Task stopped. No automatic restart set")
                break

            self.log("Restarting in 5 secs...")
            # TODO make restart time configurable
            time.sleep(5)

    def _run_process(self):
        """Launches the subprocess and waits for its completion."""
        cmd = self.config.command
        cwd = self.config.working_directory

        # Log config
        stdout_dest = subprocess.PIPE
        stderr_dest = subprocess.PIPE
        stdout_f, stderr_f = None, None
        start_time = time.time()
        timeout_seconds = self._parse_timeout(self.config.timeout)

        try:
            if self.config.stdout:
                stdout_f = open(self.config.stdout, "a")
                stdout_dest = stdout_f

            if self.config.stderr and self.config.stderr != "combined":
                stderr_f = open(self.config.stderr, "a")
                stderr_dest = stderr_f
            elif self.config.stderr == "combined":
                stderr_dest = subprocess.STDOUT

            self.log(f"Executing: {cmd}")
            self.process = subprocess.Popen(
                cmd,
                shell=True,
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
                    break

                if timeout_seconds and (time.time() - start_time > timeout_seconds):
                    self.log(f"Timeout exceeded ({self.config.timeout}). Killing process.")
                    self._kill_process()
                    break
                time.sleep(1)

            # If we exit the loop but the process is still alive (manual stop), kill it
            if self.process.poll() is None:
                self._kill_process()

        except Exception as e:
            self.log(f"Critical error executing process: {e}")
        finally:
            if stdout_f:
                stdout_f.close()
            if stderr_f:
                stderr_f.close()

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
        """Parses a timeout string (e.g., '30s', '5m', '1h') into seconds."""
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
