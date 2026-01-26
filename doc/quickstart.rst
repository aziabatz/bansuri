Quick Start Guide
=================

Get Bansuri running in 5 minutes.

Prerequisites
~~~~~~~~~~~~~

- Python 3.8 or higher
- ``pip`` package manager

Installation
~~~~~~~~~~~~

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/aziabatz/bansuri.git
    cd bansuri

    # Install in development mode
    pip install -e .

    # Verify installation
    bansuri --help

Your First Task
~~~~~~~~~~~~~~~

**Step 1: Create** ``scripts.json``:

.. code-block:: json

    {
      "version": "1.0",
      "scripts": [
        {
          "name": "hello-world",
          "command": "echo 'Hello from Bansuri!'",
          "timer": "30",
          "description": "Prints a greeting every 30 seconds"
        }
      ]
    }

**Step 2: Run Bansuri**:

.. code-block:: bash

    bansuri

**Expected Output**:

.. code-block:: log

    [2026-01-19 10:00:00] [MASTER] ========================================
    [2026-01-19 10:00:00] [MASTER] BANSURI ORCHESTRATOR STARTED
    [2026-01-19 10:00:00] [MASTER] ========================================
    [2026-01-19 10:00:00] [hello-world] Runner started.
    [2026-01-19 10:00:01] [hello-world] Timer configured: running every 30s (30s)
    [2026-01-19 10:00:01] [hello-world] Executing shell command: echo 'Hello from Bansuri!'
    [2026-01-19 10:00:01] [hello-world] Process finished with code 0
    [2026-01-19 10:00:31] [hello-world] Executing shell command: echo 'Hello from Bansuri!'

**Step 3: Stop** with ``Ctrl+C``

What Just Happened?
~~~~~~~~~~~~~~~~~~~

1. Bansuri read ``scripts.json``
2. Found task ``hello-world``
3. Started a ``TaskRunner`` thread for the task
4. Task ran immediately, then every 30 seconds
5. Logs showed each execution

Useful Examples
---------------

Backup Database Every Hour
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add this to your ``scripts.json``:

.. code-block:: json

    {
      "name": "hourly-backup",
      "command": "pg_dump mydb | gzip > /backups/db-$(date +%Y%m%d_%H%M%S).sql.gz",
      "timer": "3600",
      "timeout": "15m",
      "on-fail": "restart",
      "times": 2,
      "working-directory": "/backups",
      "description": "Backs up PostgreSQL database hourly"
    }

Run Health Checks Every Minute
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "name": "health-check",
      "command": "/usr/local/bin/health-check.sh",
      "timer": "60",
      "timeout": "30s",
      "on-fail": "stop",
      "stdout": "/var/log/healthcheck.log",
      "stderr": "combined",
      "description": "System health check every minute"
    }

Data Sync with Retries
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "name": "sync-data",
      "command": "rsync -av /data/source /data/backup",
      "timer": "300",
      "on-fail": "restart",
      "times": 3,
      "timeout": "5m",
      "notify": "mail",
      "description": "Sync data every 5 minutes with retry"
    }

Complete Beginner Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s '[Bansuri] Task Failed' admin@example.com",
      "scripts": [
        {
          "name": "task-1-quick",
          "command": "echo 'Quick task'",
          "timer": "60",
          "description": "Runs every minute"
        },
        {
          "name": "task-2-medium",
          "command": "/opt/scripts/process.sh",
          "timer": "300",
          "timeout": "2m",
          "on-fail": "restart",
          "times": 2,
          "description": "Runs every 5 minutes with retry"
        },
        {
          "name": "task-3-critical",
          "command": "/opt/scripts/critical-job.sh",
          "timer": "3600",
          "timeout": "30m",
          "on-fail": "restart",
          "times": 3,
          "notify": "mail",
          "stdout": "/var/log/critical.log",
          "stderr": "combined",
          "description": "Critical hourly job with monitoring"
        }
      ]
    }

Common Tasks
~~~~~~~~~~~~

**Run once and exit:**

.. code-block:: json

    {
      "name": "one-time-task",
      "command": "setup.sh"
    }

**Run periodically:**

.. code-block:: json

    {
      "name": "periodic-task",
      "command": "cleanup.sh",
      "timer": "86400"
    }

**Run with timeout:**

.. code-block:: json

    {
      "name": "timeout-task",
      "command": "long-running.sh",
      "timeout": "30m"
    }

**Run with retries:**

.. code-block:: json

    {
      "name": "retry-task",
      "command": "api-call.py",
      "on-fail": "restart",
      "times": 3
    }

**Run with logging:**

.. code-block:: json

    {
      "name": "logged-task",
      "command": "data-process.sh",
      "stdout": "/var/log/process.log",
      "stderr": "combined"
    }

**Run with notifications:**

.. code-block:: json

    {
      "name": "monitored-task",
      "command": "critical-check.sh",
      "notify": "mail",
      "on-fail": "restart",
      "times": 2
    }

Verify Your Configuration
--------------------------

Before running:

.. code-block:: bash

    # Validate JSON
    python -m json.tool scripts.json

    # Validate with Bansuri
    python -c "
    from bansuri.base.config_manager import BansuriConfig
    config = BansuriConfig.load_from_file('scripts.json')
    print('✓ Configuration valid')
    for script in config.scripts:
        print(f'  - {script.name}')
    "

Next Steps
~~~~~~~~~~

- 📖 Read :doc:`configuration` for advanced options
- 🔔 Set up :doc:`notifications` for alerts
- 🚀 Deploy to production with :doc:`deployment`
- 🐛 See :doc:`troubleshooting-detailed` if issues arise
- 🧩 Create custom tasks with :doc:`custom-tasks`

Tips and Tricks
---------------

**Use environment variables:**

.. code-block:: bash

    export BACKUP_DIR=/backups
    bansuri

Then in scripts.json:

.. code-block:: json

    {
      "command": "pg_dump mydb > $BACKUP_DIR/db.sql"
    }

**Use cron-like schedules as timer:**

.. code-block:: json

    {
      "timer": "3600"
    }

Conversion guide:
- ``*/5 * * * *`` (every 5 minutes) → ``"timer": "300"``
- ``0 * * * *`` (hourly) → ``"timer": "3600"``
- ``0 0 * * *`` (daily) → ``"timer": "86400"``

**Test commands before adding:**

.. code-block:: bash

    # Run the command manually first
    /usr/local/bin/my-script.sh
    echo $?  # Check exit code

**Redirect verbose output:**

.. code-block:: json

    {
      "command": "./verbose-script.sh 2>/dev/null",
      "stdout": "/var/log/task.log"
    }

Troubleshooting
---------------

Task not running?

1. Check it's in the config: ``grep "name" scripts.json``
2. Verify the command exists: ``which command_name``
3. Test manually: ``/path/to/command``
4. Check permissions: ``ls -la /path/to/command``

See :doc:`troubleshooting-detailed` for more help.

Getting Support
---------------

- 📚 Full documentation: See the other RST files
- 🐛 Report issues: GitHub Issues
- 💬 Discuss: GitHub Discussions

Happy orchestrating! 🎉
