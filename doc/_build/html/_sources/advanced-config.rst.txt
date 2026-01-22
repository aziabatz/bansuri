Advanced Configuration
======================

This guide covers advanced configuration features and patterns for Bansuri.

Timeout Management
------------------

Understanding Timeouts
~~~~~~~~~~~~~~~~~~~~~~

The ``timeout`` parameter controls the maximum execution time for a task. If the task exceeds this time, the process is terminated.

Timeout Format
~~~~~~~~~~~~~~

Timeouts can be specified as:

- **Seconds**: ``"300"`` or ``300`` (5 minutes)
- **Human-readable format**:
  - Seconds: ``"30s"`` → 30 seconds
  - Minutes: ``"5m"`` → 5 minutes (300 seconds)
  - Hours: ``"2h"`` → 2 hours (7200 seconds)

Examples
~~~~~~~~

.. code-block:: json

    {
      "scripts": [
        {
          "name": "quick-task",
          "command": "echo 'Hello'",
          "timeout": "10s"
        },
        {
          "name": "medium-task",
          "command": "/usr/bin/backup.sh",
          "timeout": "30m"
        },
        {
          "name": "long-task",
          "command": "/opt/process/heavy-computation.py",
          "timeout": "1h"
        },
        {
          "name": "very-long-task",
          "command": "mysqldump production | gzip",
          "timeout": "3600"
        }
      ]
    }

Failure Control
---------------

Restart Policies
~~~~~~~~~~~~~~~~

The ``on-fail`` and ``times`` parameters control task retry behavior:

- **on-fail: "stop"** (default): Stop the task immediately on failure
- **on-fail: "restart"**: Restart the task up to ``times`` attempts

The ``success-codes`` parameter specifies which exit codes are considered success (default: ``[0]``).

Example Configurations
~~~~~~~~~~~~~~~~~~~~~~

**Single attempt, stop on failure:**

.. code-block:: json

    {
      "name": "critical-task",
      "command": "deploy.sh",
      "on-fail": "stop",
      "times": 1
    }

**Three retry attempts:**

.. code-block:: json

    {
      "name": "resilient-task",
      "command": "api-call.sh",
      "on-fail": "restart",
      "times": 3
    }

**Custom success codes:**

.. code-block:: json

    {
      "name": "task-with-warnings",
      "command": "./checker.sh",
      "success-codes": [0, 2],
      "on-fail": "restart",
      "times": 2
    }

Output Redirection
-------------------

Log File Management
~~~~~~~~~~~~~~~~~~~

Control where task output goes with ``stdout`` and ``stderr``:

- **stderr: "combined"** (default): Merge stderr into stdout
- **stderr: "/path/to/file"**: Redirect to a specific file
- **stdout: "/path/to/file"**: Redirect stdout separately

Examples
~~~~~~~~

**Combined output to single file:**

.. code-block:: json

    {
      "name": "task-with-logs",
      "command": "backup.sh",
      "stdout": "/var/log/backup.log",
      "stderr": "combined"
    }

**Separate log files:**

.. code-block:: json

    {
      "name": "task-separate-logs",
      "command": "process.py",
      "stdout": "/var/log/process.out",
      "stderr": "/var/log/process.err"
    }

**Log rotation pattern:**

.. code-block:: json

    {
      "name": "task-with-rotation",
      "command": "data-sync.sh",
      "stdout": "/var/log/sync/$(date +%Y-%m-%d).log",
      "stderr": "combined"
    }

Working Directory
-----------------

The ``working-directory`` parameter sets the directory where the command is executed:

.. code-block:: json

    {
      "name": "repo-task",
      "command": "git pull && npm test",
      "working-directory": "/home/deploy/myapp"
    }

This is useful for:

- Scripts that use relative paths
- Repository operations
- Docker container workloads

Task Descriptions
-----------------

Add ``description`` field for documentation:

.. code-block:: json

    {
      "name": "backup-daily",
      "command": "pg_dump production > backup.sql",
      "timer": "86400",
      "description": "Daily PostgreSQL backup at midnight UTC"
    }

Combining Features
-------------------

Here's a comprehensive example using multiple advanced features:

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s '[Bansuri] Alert' ops@company.com",
      "scripts": [
        {
          "name": "critical-api-health-check",
          "command": "/opt/healthcheck/api-check.py",
          "timer": "60",
          "timeout": "30s",
          "working-directory": "/opt/healthcheck",
          "on-fail": "restart",
          "times": 3,
          "notify": "mail",
          "stdout": "/var/log/healthcheck.log",
          "stderr": "combined",
          "success-codes": [0, 1],
          "description": "API health check every minute with retries"
        },
        {
          "name": "nightly-database-backup",
          "command": "/usr/local/bin/backup-db.sh",
          "timer": "86400",
          "timeout": "2h",
          "working-directory": "/backups",
          "on-fail": "restart",
          "times": 2,
          "notify": "mail",
          "stdout": "/var/log/backup-$(date +%Y-%m-%d).log",
          "stderr": "combined",
          "description": "Nightly full database backup with retry"
        }
      ]
    }

Performance Tuning
------------------

Task Concurrency
~~~~~~~~~~~~~~~~

Each task runs in its own thread. The system can handle multiple concurrent tasks:

- **I/O-bound tasks**: Run many concurrently (network calls, file operations)
- **CPU-bound tasks**: Consider limiting concurrency and using appropriate timeouts
- **Resource-intensive tasks**: Monitor system resources

Timer-based Execution
~~~~~~~~~~~~~~~~~~~~~

The ``timer`` parameter defines fixed-interval execution:

.. code-block:: json

    {
      "name": "frequent-task",
      "command": "check.sh",
      "timer": "5",
      "description": "Runs every 5 seconds"
    }

.. code-block:: json

    {
      "name": "hourly-task",
      "command": "hourly-job.sh",
      "timer": "3600",
      "description": "Runs every hour"
    }

Error Handling Patterns
-----------------------

**Pattern 1: Fail-fast**

For critical tasks that should stop immediately:

.. code-block:: json

    {
      "name": "deploy",
      "command": "deploy.sh",
      "on-fail": "stop",
      "times": 1
    }

**Pattern 2: Resilient with retries**

For tasks that might have transient failures:

.. code-block:: json

    {
      "name": "api-call",
      "command": "api-client.py",
      "on-fail": "restart",
      "times": 5,
      "timeout": "30s"
    }

**Pattern 3: Partial success acceptance**

For tasks where certain exit codes are acceptable:

.. code-block:: json

    {
      "name": "data-check",
      "command": "validator.py",
      "success-codes": [0, 2],
      "notify": "mail"
    }

**Pattern 4: Monitored execution with notification**

For important tasks that need monitoring:

.. code-block:: json

    {
      "name": "critical-job",
      "command": "critical.sh",
      "timer": "3600",
      "timeout": "30m",
      "on-fail": "restart",
      "times": 3,
      "notify": "mail",
      "stdout": "/var/log/critical.log",
      "stderr": "combined"
    }

Common Mistakes to Avoid
------------------------

1. **Setting timeout too short**: Leave enough time for normal execution
2. **Ignoring failure modes**: Test on-fail behavior
3. **Not managing logs**: Use log rotation or separate log directories
4. **Forgetting working-directory**: Relative paths may fail
5. **Ignoring resource limits**: Monitor CPU and memory usage

Debugging Configuration Issues
-------------------------------

Enable debug output:

.. code-block:: bash

    export BANSURI_LOG_LEVEL=DEBUG
    bansuri --config scripts.json

Check configuration syntax:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    config = BansuriConfig.load_from_file('scripts.json')
    for script in config.scripts:
        print(f'{script.name}: OK')
    "

Test command execution:

.. code-block:: bash

    bash -c "cd /working/dir && /path/to/command"
