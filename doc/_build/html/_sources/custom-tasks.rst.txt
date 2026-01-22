Creating Custom Tasks
======================

Bansuri provides a powerful extension system that allows you to create custom task implementations beyond simple shell commands. This is perfect for complex business logic, Python scripts with special requirements, or integrations with other systems.

Overview
--------

The base class ``AbstractTask`` defines the interface for all executable tasks in Bansuri. By inheriting from this class and implementing the required methods, you can create sophisticated task handlers.

Abstract Base Class
~~~~~~~~~~~~~~~~~~~

.. autoclass:: bansuri.base.task_base.AbstractTask
   :members:
   :undoc-members:
   :show-inheritance:

Basic Example: Logging Task
----------------------------

Here's a simple custom task that logs messages to a file:

.. code-block:: python

    from bansuri.base.task_base import AbstractTask
    from bansuri.base.config.task_config import TaskConfig
    from datetime import datetime

    class LoggingTask(AbstractTask):
        """A simple task that logs to a file."""
        
        def __init__(self, config: TaskConfig):
            super().__init__(config)
            self.running = False
        
        def run(self) -> int:
            """Execute the logging task."""
            self.running = True
            try:
                log_file = self.config.logging.stdout_path or "/tmp/task.log"
                message = f"[{datetime.now()}] Task executed: {self.config.identification.name}"
                
                with open(log_file, "a") as f:
                    f.write(message + "\n")
                
                return 0  # Success
            except Exception as e:
                print(f"Error: {e}")
                return 1  # Failure
            finally:
                self.running = False
        
        def stop(self) -> None:
            """Stop the task if running."""
            self.running = False

Advanced Example: Database Backup Task
--------------------------------------

A more realistic example that backs up a PostgreSQL database:

.. code-block:: python

    import subprocess
    import os
    from datetime import datetime
    from bansuri.base.task_base import AbstractTask
    from bansuri.base.config.task_config import TaskConfig

    class PostgresBackupTask(AbstractTask):
        """Backs up a PostgreSQL database with compression."""
        
        def __init__(self, config: TaskConfig):
            super().__init__(config)
            self.process = None
        
        def run(self) -> int:
            """Execute the backup."""
            try:
                # Get configuration from task config
                db_name = os.environ.get("DB_NAME", "production")
                backup_dir = self.config.logging.stdout_path or "/backups"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{backup_dir}/{db_name}_{timestamp}.sql.gz"
                
                # Create backup command
                cmd = f"pg_dump {db_name} | gzip > {backup_file}"
                
                # Execute with timeout
                timeout = self._parse_timeout()
                self.process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.config.identification.working_directory
                )
                
                try:
                    stdout, stderr = self.process.communicate(timeout=timeout)
                    return self.process.returncode
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    return -1  # Timeout
                    
            except Exception as e:
                print(f"Backup failed: {e}")
                return 1
        
        def stop(self) -> None:
            """Terminate the backup process."""
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
        
        def _parse_timeout(self) -> int:
            """Parse timeout from config."""
            timeout_str = self.config.scheduling.timeout
            if not timeout_str:
                return 3600  # Default 1 hour
            
            if isinstance(timeout_str, int):
                return timeout_str
            
            # Parse formats like "30s", "5m", "1h"
            timeout_str = str(timeout_str).lower()
            if timeout_str.endswith("s"):
                return int(timeout_str[:-1])
            elif timeout_str.endswith("m"):
                return int(timeout_str[:-1]) * 60
            elif timeout_str.endswith("h"):
                return int(timeout_str[:-1]) * 3600
            else:
                return int(timeout_str)

Advanced Example: Health Check Task
-----------------------------------

A task that performs system health checks and reports metrics:

.. code-block:: python

    import json
    import subprocess
    from datetime import datetime
    from bansuri.base.task_base import AbstractTask
    from bansuri.base.config.task_config import TaskConfig

    class HealthCheckTask(AbstractTask):
        """Performs system health checks and sends metrics."""
        
        def __init__(self, config: TaskConfig):
            super().__init__(config)
            self.metrics = {}
        
        def run(self) -> int:
            """Execute health checks."""
            try:
                # CPU usage
                cpu_result = subprocess.run(
                    "grep 'cpu ' /proc/stat",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Memory usage
                mem_result = subprocess.run(
                    "free -b | grep Mem",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Disk usage
                disk_result = subprocess.run(
                    "df -B1 /",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                self.metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": cpu_result.stdout.strip(),
                    "memory": mem_result.stdout.strip(),
                    "disk": disk_result.stdout.strip()
                }
                
                # Send metrics to monitoring system
                return self._send_metrics()
                
            except Exception as e:
                print(f"Health check failed: {e}")
                return 1
        
        def stop(self) -> None:
            """Clean up health check task."""
            pass
        
        def _send_metrics(self) -> int:
            """Send metrics to a monitoring backend."""
            # This would integrate with your monitoring system
            # (Prometheus, Grafana, InfluxDB, etc.)
            print(json.dumps(self.metrics))
            return 0

Configuration for Custom Tasks
-------------------------------

When using custom tasks, you need to:

1. **Set ``no-interface`` to ``true``** in the task configuration
2. **Reference the module path** in the command field (Python import path)

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "scripts": [
        {
          "name": "custom-logging-task",
          "command": "myapp.tasks:LoggingTask",
          "no-interface": true,
          "timer": "3600",
          "description": "Runs custom logging task every hour"
        },
        {
          "name": "postgres-backup",
          "command": "myapp.tasks:PostgresBackupTask",
          "no-interface": true,
          "timer": "86400",
          "timeout": "2h",
          "on-fail": "restart",
          "times": 2,
          "description": "Daily PostgreSQL backup with retry"
        }
      ]
    }

Best Practices
--------------

1. **Exception Handling**: Always wrap your logic in try-except blocks
2. **Return Codes**: Use 0 for success, non-zero for failure
3. **Graceful Shutdown**: Implement proper cleanup in the ``stop()`` method
4. **Logging**: Use standard logging for debugging and error tracking
5. **Timeout Support**: Parse and respect the timeout configuration
6. **Resource Cleanup**: Close files, connections, and processes properly

Example with Logging
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import logging
    from bansuri.base.task_base import AbstractTask

    class BestPracticeTask(AbstractTask):
        def __init__(self, config):
            super().__init__(config)
            self.logger = logging.getLogger(config.identification.name)
        
        def run(self) -> int:
            try:
                self.logger.info(f"Starting task: {self.config.identification.name}")
                # Do work
                self.logger.info("Task completed successfully")
                return 0
            except Exception as e:
                self.logger.error(f"Task failed: {e}", exc_info=True)
                return 1
        
        def stop(self) -> None:
            self.logger.info("Stopping task")

Testing Custom Tasks
--------------------

Example test for a custom task:

.. code-block:: python

    import unittest
    from myapp.tasks import LoggingTask
    from bansuri.base.config.task_config import TaskConfig
    from bansuri.base.config.proc_id_config import IdentificationConfig

    class TestLoggingTask(unittest.TestCase):
        def setUp(self):
            self.config = TaskConfig(
                identification=IdentificationConfig(
                    name="test-task",
                    command="test"
                )
            )
            self.task = LoggingTask(self.config)
        
        def test_run_success(self):
            result = self.task.run()
            self.assertEqual(result, 0)
        
        def test_stop(self):
            self.task.stop()  # Should not raise

    if __name__ == "__main__":
        unittest.main()

Integration with Bansuri
------------------------

Custom tasks are automatically detected and loaded by the ``TaskRunner`` when:

1. ``no-interface`` is set to ``true``
2. The ``command`` field contains a valid Python module path and class name (format: ``module.path:ClassName``)

The system will:

1. Import the module
2. Instantiate the class with the ``TaskConfig``
3. Call ``run()`` in a thread
4. Call ``stop()`` when the orchestrator shuts down or the task is removed

See :doc:`notifications` for how failures are handled and notifications are sent.
