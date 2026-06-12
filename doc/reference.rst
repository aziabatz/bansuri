Reference
=========

Complete reference for configuration and command-line usage.

Quick Configuration Examples
-----------------------------

Minimal Task
~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "scripts": [
        {
          "name": "my-task",
          "command": "echo 'hello'"
        }
      ]
    }

**Result**: Task runs once at startup.

---

Timer-Based Task (Every 5 Minutes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "name": "monitor",
      "command": "python monitor.py",
      "timer": "300"
    }

---

Cron-Scheduled Task (Daily at 2 AM)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "name": "backup",
      "command": "bash backup.sh",
      "schedule-cron": "0 2 * * *"
    }

**Requirements**: ``pip install croniter``

---

Task with Retry Logic
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "name": "api-call",
      "command": "curl -f https://api.example.com/sync",
      "timer": "3600",
      "timeout": "30s",
      "on-fail": "restart",
      "max-attempts": 3,
      "notify": "mail",
      "success-codes": [0]
    }

**Behavior**: Runs hourly, retries 3 times on failure, kills if > 30s, notifies on final failure.

---

Complete Task Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s 'Alert: {task}' admin@example.com",
      "scripts": [
        {
          "name": "database-maintenance",
          "command": "python /app/maintenance.py",
          "working-directory": "/app",
          "timer": "86400",
          "timeout": "2h",
          "times": 2,
          "max-attempts": 3,
          "on-fail": "restart",
          "stdout": "/var/log/maintenance.log",
          "stderr": "combined",
          "notify": "mail",
          "notify-after": "600s",
          "success-codes": [0],
          "description": "Daily database maintenance"
        }
      ]
    }

Parameter Reference
--------------------

Required Parameters
~~~~~~~~~~~~~~~~~~~

=====================  ==========================================
Parameter              Description
=====================  ==========================================
``version``            Config version (usually "1.0")
``scripts``            Array of task definitions
``name`` (per-task)    Unique task identifier
``command``            Command or script to execute
=====================  ==========================================

Optional Scheduling
~~~~~~~~~~~~~~~~~~~

=====================  ==========================================
Parameter              Description
=====================  ==========================================
``timer``              Interval in seconds (e.g., "300", "5m")
``schedule-cron``      Cron expression (e.g., "0 2 * * *")
=====================  ==========================================

**Note**: Pick ONE scheduling method. If none specified, runs once at startup.

Optional Execution Control
~~~~~~~~~~~~~~~~~~~~~~~~~~

=====================  ==========================================
Parameter              Default        Description
=====================  ==========================================
``timeout``            None           Max execution time (e.g., "5m")
``on-fail``            "stop"         Behavior: "stop" or "restart"
``times``              0              Max successful executions (0 = unlimited)
``max-attempts``       1              Max retry attempts on failure
``success-codes``      [0]            Acceptable exit codes (array)
``notify``             "none"         Notification on fail: "mail" or "none"
``notify-after``       None           Wait time before notifying (e.g., "300s")
=====================  ==========================================

Optional Output
~~~~~~~~~~~~~~~

=====================  ==========================================
Parameter              Default        Description
=====================  ==========================================
``stdout``             None           File to save stdout
``stderr``             "combined"     File for stderr or "combined"
``working-directory``  None           Directory to run command in
``description``        ""             Human-readable description
=====================  ==========================================

Time Format Reference
~~~~~~~~~~~~~~~~~~~~~

All time-based parameters support flexible formats:

=========  ============================
Format     Means
=========  ============================
"30"       30 seconds
"30s"      30 seconds
"5m"       5 minutes (= 300 seconds)
"1h"       1 hour (= 3600 seconds)
"86400"    1 day in seconds
=========  ============================

Common Intervals
~~~~~~~~~~~~~~~~

=================  ==============  ===================
Interval           Timer Value     Alternative Formats
=================  ==============  ===================
Every 30 seconds   "30"            "30s"
Every minute       "60"            "1m"
Every 5 minutes    "300"           "5m"
Every hour         "3600"          "1h"
Every day          "86400"         "24h"
=================  ==============  ===================

Command-Line Reference
----------------------

Start Bansuri
~~~~~~~~~~~~~

.. code-block:: bash

    # Use default scripts.json
    bansuri

    # Use custom config file
    bansuri --config /path/to/config.json

    # Show help
    bansuri --help

Validation
~~~~~~~~~~

Check if config file is valid JSON:

.. code-block:: bash

    python -m json.tool scripts.json

Quick Validation Script:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    try:
        config = BansuriConfig.load_from_file('scripts.json')
        print('Configuration is valid')
        for task in config.scripts:
            print(f'   - {task.name}')
    except Exception as e:
        print(f'Error: {e}')
    "

Testing Commands
~~~~~~~~~~~~~~~~

Before adding to Bansuri, test your command:

.. code-block:: bash

    # Test shell command
    bash -x /path/to/script.sh

    # Check Python syntax
    python -m py_compile my_script.py

    # Run with timeout
    timeout 30s python my_script.py

Common Mistakes
---------------

1. **Missing croniter library**

   .. code-block:: text

      ERROR: 'croniter' library is missing

   Fix:

   .. code-block:: bash

      pip install croniter

2. **Invalid JSON**

   Symptom: Task doesn't start, no error message

   Fix:

   .. code-block:: bash

      python -m json.tool scripts.json

3. **Command not found**

   Symptom: Exit code 127

   Fix: Use absolute path to script

   .. code-block:: json

      "command": "/usr/local/bin/my_script.sh"

4. **Permission denied**

   Symptom: Exit code 126

   Fix: Make script executable

   .. code-block:: bash

      chmod +x /path/to/script.sh

See :doc:`troubleshooting` for more help.

View Logs
~~~~~~~~~

For systemd:

.. code-block:: bash

    # Live logs
    journalctl -u bansuri -f

    # Last 50 lines
    journalctl -u bansuri -n 50

    # Since specific time
    journalctl -u bansuri --since "2024-01-19 10:00:00"

    # Only errors
    journalctl -u bansuri -p err

For file logging:

.. code-block:: bash

    # Live logs
    tail -f /var/log/bansuri.log

    # Last 100 lines
    tail -100 /var/log/bansuri.log

    # Follow and grep
    tail -f /var/log/bansuri.log | grep FAILED

System Management
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Start
    systemctl start bansuri

    # Stop
    systemctl stop bansuri

    # Restart
    systemctl restart bansuri

    # Status
    systemctl status bansuri

    # Enable on boot
    systemctl enable bansuri

    # Disable on boot
    systemctl disable bansuri

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

Validate configuration syntax:

.. code-block:: bash

    python -m json.tool scripts.json

Validate with Bansuri:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    try:
        config = BansuriConfig.load_from_file('scripts.json')
        print('Valid')
    except Exception as e:
        print(f'Error: {e}')
    "

Testing
~~~~~~~

Test a command before adding to config:

.. code-block:: bash

    bash -x /path/to/script.sh

Profile execution time:

.. code-block:: bash

    time /path/to/script.sh

Monitor in real-time:

.. code-block:: bash

    watch -n 1 'ps aux | grep python'

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

===================  ================  ==========================================
Variable             Default           Description
===================  ================  ==========================================
BANSURI_ENV          production        Environment (dev/staging/production)
BANSURI_LOG_LEVEL    INFO              Logging verbosity (DEBUG/INFO/WARNING/ERROR)
===================  ================  ==========================================

Set before running:

.. code-block:: bash

    export BANSURI_LOG_LEVEL=DEBUG
    bansuri

Configuration Examples
----------------------

Example 1: Simple Health Check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "scripts": [
        {
          "name": "health-check",
          "command": "curl -f https://example.com/health",
          "timer": "60",
          "timeout": "10s"
        }
      ]
    }

Example 2: Database Backup with Retry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s 'Backup Alert' ops@example.com",
      "scripts": [
        {
          "name": "backup-db",
          "command": "pg_dump mydb | gzip > backup.sql.gz",
          "timer": "86400",
          "timeout": "2h",
          "on-fail": "restart",
          "times": 3,
          "notify": "mail",
          "stdout": "/var/log/backup.log"
        }
      ]
    }

Example 3: Multiple Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s '[Bansuri]' admin@example.com",
      "scripts": [
        {
          "name": "quick-task",
          "command": "echo 'Quick'",
          "timer": "60"
        },
        {
          "name": "medium-task",
          "command": "sh /opt/process.sh",
          "timer": "300",
          "timeout": "2m",
          "on-fail": "restart",
          "times": 2
        },
        {
          "name": "critical-task",
          "command": "python /opt/critical.py",
          "timer": "3600",
          "timeout": "30m",
          "on-fail": "restart",
          "times": 3,
          "notify": "mail",
          "stdout": "/var/log/critical.log"
        }
      ]
    }

Exit Codes Reference
--------------------

Standard Exit Codes:

=========  ==================
Code       Meaning
=========  ==================
0          Success
1          General error
2          Misuse of shell command
126        Command invoked cannot execute
127        Command not found
128+N      Fatal signal N
130        Terminated (SIGINT/Ctrl+C)
137        Killed (SIGKILL)
143        Terminated (SIGTERM)
=========  ==================

Testing Patterns
----------------

Test script exit code:

.. code-block:: bash

    /path/to/script.sh
    echo "Exit code: $?"

Test with different arguments:

.. code-block:: bash

    /path/to/script.sh arg1 arg2
    echo $?

Test with timeout:

.. code-block:: bash

    timeout 30 /path/to/script.sh
    echo $?

Test output redirection:

.. code-block:: bash

    /path/to/script.sh > /tmp/out.log 2>&1
    cat /tmp/out.log

Debugging Checklist
-------------------

Task not running:

- [ ] Command is valid: ``which command_name``
- [ ] Script is executable: ``ls -la /path/to/script``
- [ ] Path is absolute in config
- [ ] Working directory exists: ``ls -la /path/to/workdir``
- [ ] Timer is set (if periodic task)

Task failing repeatedly:

- [ ] Test command manually
- [ ] Check exit code: ``/path/to/script.sh; echo $?``
- [ ] Check permissions: ``ls -la /path/to/script``
- [ ] Check output: ``tail -f /var/log/task.log``
- [ ] Check dependencies exist

Timeout issues:

- [ ] Measure actual execution: ``time /path/to/script.sh``
- [ ] Increase timeout value
- [ ] Check system resources: ``free -h``, ``df -h``
- [ ] Check for blocking operations

Notifications not working:

- [ ] ``notify`` is set to ``"mail"``
- [ ] ``notify_command`` is configured
- [ ] Test command: ``echo "test" | mail -s "test" email@example.com``
- [ ] Check network connectivity
- [ ] Check Bansuri logs

Performance Tuning Checklist
-----------------------------

Memory usage high:

- [ ] Redirect task output to files
- [ ] Reduce number of concurrent tasks
- [ ] Monitor: ``ps aux | grep python``

CPU usage high:

- [ ] Increase timer intervals
- [ ] Check for infinite loops
- [ ] Profile: ``python -m cProfile``

Tasks running slow:

- [ ] Check system load: ``uptime``
- [ ] Monitor I/O: ``iotop``
- [ ] Check network: ``netstat -s``
- [ ] Profile execution: ``time`` command

Common Commands Cheat Sheet
----------------------------

.. code-block:: bash

    # View configuration
    cat scripts.json | python -m json.tool

    # Validate configuration
    python -c "from bansuri.base.config_manager import BansuriConfig; BansuriConfig.load_from_file('scripts.json')"

    # Find Bansuri process
    pgrep -f "python -m bansuri"

    # Kill Bansuri
    pkill -f "python -m bansuri"

    # Check system resources
    free -h && df -h && uptime

    # Monitor process
    watch -n 1 'ps aux | grep bansuri'

    # View recent logs
    tail -50 /var/log/bansuri.log

    # Search logs
    grep "ERROR" /var/log/bansuri.log

    # Count task executions
    grep -c "started\|completed" /var/log/bansuri.log

Useful Aliases
~~~~~~~~~~~~~~

Add to ``.bashrc``:

.. code-block:: bash

    alias bansuri-status='systemctl status bansuri'
    alias bansuri-logs='journalctl -u bansuri -f'
    alias bansuri-restart='systemctl restart bansuri'
    alias bansuri-config='cat ~/bansuri/scripts.json | python -m json.tool'
    alias bansuri-validate='python -c "from bansuri.base.config_manager import BansuriConfig; BansuriConfig.load_from_file(\"scripts.json\"); print(\"Valid\")"'
