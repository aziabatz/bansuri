import subprocess
import threading
import time
import os
import signal
import sys
import importlib.util
from datetime import datetime
from typing import Optional
from pathlib import Path
from bansuri.base.config_manager import ScriptConfig


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
        """Main loop: executes the task and handles job stop-start events

        Supports:
        - timer: Fixed interval execution (e.g., "30s", "5m", "1h")

        NOT IMPLEMENTED:
        - schedule-cron support
        """
        if self.config.schedule_cron:
            self.log("WARNING: schedule-cron NOT IMPLEMENTED. Running once.")
            self._run_process()
            return

        # Check if timer is configured
        if self.config.timer and self.config.timer != 'none':
            self._timer_execution_loop()
        else:
            self._simple_execution_loop()

    def _simple_execution_loop(self):
        """Simple execution loop without timer"""
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
            time.sleep(5)

    def _timer_execution_loop(self):
        """Timer-based execution loop - runs task at fixed intervals"""
        timer_seconds = self._parse_timeout(self.config.timer)

        if not timer_seconds:
            self.log(f"ERROR: Invalid timer format '{self.config.timer}'. Running once.")
            self._run_process()
            return

        self.log(f"Timer configured: running every {self.config.timer} ({timer_seconds}s)")

        while not self.stop_event.is_set():
            # Attempts control
            if self.config.times > 0 and self.attempts >= self.config.times:
                self.log("Reached max attempts. Giving up...")
                break

            self.attempts += 1
            self._run_process()

            if self.stop_event.is_set():
                break

            # Wait for timer interval before next execution
            self.log(f"Waiting {self.config.timer} until next execution...")
            for _ in range(timer_seconds):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _run_process(self):
        """Launches the subprocess or AbstractTask depending on no-interface setting."""
        if self.config.no_interface:
            # Plain command execution (shell/bash)
            self._run_shell_command()
        else:
            # Smart script: Import and run AbstractTask
            self._run_smart_script()

    def _run_shell_command(self):
        """Executes command directly as shell process (no-interface: true)."""
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

            self.log(f"Executing shell command: {cmd}")
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
            self.log(f"Critical error executing shell command: {e}")
        finally:
            if stdout_f:
                stdout_f.close()
            if stderr_f:
                stderr_f.close()

    def _run_smart_script(self):
        """Imports Python script and runs AbstractTask (no-interface: false)."""
        try:
            # Parse command to extract script path
            script_path = self._extract_script_path(self.config.command)
            if not script_path:
                self.log(f"ERROR: Could not extract script path from command: {self.config.command}")
                return

            # Make path absolute if needed
            if self.config.working_directory and not os.path.isabs(script_path):
                script_path = os.path.join(self.config.working_directory, script_path)

            if not os.path.exists(script_path):
                self.log(f"ERROR: Script not found: {script_path}")
                return

            # Import the module
            self.log(f"Loading smart script: {script_path}")
            spec = importlib.util.spec_from_file_location("task_module", script_path)
            if not spec or not spec.loader:
                self.log(f"ERROR: Could not load module spec from {script_path}")
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules["task_module"] = module

            # Add working directory to path
            if self.config.working_directory:
                sys.path.insert(0, self.config.working_directory)

            spec.loader.exec_module(module)

            # Find AbstractTask subclass
            task_class = self._find_abstract_task_class(module)
            if not task_class:
                self.log(f"ERROR: No AbstractTask subclass found in {script_path}")
                return

            # Instantiate task
            self.log(f"Instantiating {task_class.__name__}")
            task_instance = task_class()

            # Get TaskConfig from task (if available)
            if hasattr(task_instance, 'get_task_config'):
                task_config = task_instance.get_task_config()
                self.log(f"Task config loaded from script: {task_config}")
                # TODO: Merge/override with JSON config if needed

            # Run the task
            self.log(f"Running {task_class.__name__}.run()")
            exit_code = task_instance.run()
            self.log(f"Task finished with exit code: {exit_code}")

        except Exception as e:
            self.log(f"ERROR running smart script: {e}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # Cleanup sys.path
            if self.config.working_directory and self.config.working_directory in sys.path:
                sys.path.remove(self.config.working_directory)

    def _extract_script_path(self, command: str) -> Optional[str]:
        """Extracts script path from command string."""
        # Handle cases like:
        # "python script.py"
        # "python /path/to/script.py"
        # "script.py"
        parts = command.strip().split()

        for part in parts:
            if part.endswith('.py'):
                return part

        return None

    def _find_abstract_task_class(self, module):
        """Finds the AbstractTask subclass in the module."""
        from bansuri.base.abstract_task import AbstractTask

        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, AbstractTask) and obj is not AbstractTask:
                return obj

        return None

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
