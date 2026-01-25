Configuration
==============

How to configure tasks in Bansuri.

Configuration File
------------------

Bansuri uses **JSON** configuration files to define tasks.

**Default Location**: ``scripts.json`` in current directory

**Example**:

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s 'Alert' admin@example.com",
      "scripts": [
        {
          "name": "task-1",
          "command": "python script.py",
          "timer": "300"
        }
      ]
    }

Minimal Task
~~~~~~~~~~~~

Only **name** and **command** are required:

.. code-block:: json

    {
      "version": "1.0",
      "scripts": [
        {
          "name": "my-task",
          "command": "bash do_something.sh"
        }
      ]
    }

Task Parameters Reference
--------------------------

**Scheduling** (pick one):

=====================  ====================  ==================================================================
Parameter              Example               Description
=====================  ====================  ==================================================================
``timer``              ``"300"`` or ``"5m"`` Run task every N seconds/minutes/hours
``schedule-cron``      ``"0 2 * * *"``       Run task on cron schedule (requires croniter)
=====================  ====================  ==================================================================

**Execution Control**:

=====================  ====================  ==================================================================
Parameter              Example               Description
=====================  ====================  ==================================================================
``timeout``            ``"30s"`` or ``"5m"`` Kill task if it runs longer than this
``on-fail``            ``"restart"``         What to do on failure: ``"stop"`` or ``"restart"``
``times``              ``3``                 Max attempts (default: 1)
``success-codes``      ``[0, 1, 2]``         Exit codes to treat as success (default: [0])
=====================  ====================  ==================================================================

**Output & Logs**:

=====================  ====================  =====================================================
Parameter              Example               Description
=====================  ====================  =====================================================
``stdout``             ``"task.log"``        File to save stdout
``stderr``             ``"combined"``        File for stderr or "combined" (default: combined)
``working-directory``  ``"/app/scripts"``    Directory to run command in
``description``        ``"Daily backup"``    Human-readable description
=====================  ====================  =====================================================

**Advanced** (not yet implemented):

=====================  ====================  =====================================================
Parameter              Example               Description
=====================  ====================  =====================================================
``depends-on``         ``["task-1"]``        ❌ Run after other tasks complete
``user``               ``"postgres"``        ❌ Run as different user
``priority``           ``10``                ❌ Process priority (nice value)
``environment-file``   ``"/etc/env.json"``   ❌ Load environment variables from file
=====================  ====================  =====================================================

Time Format Examples
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "timer": "30",      // Every 30 seconds
      "timer": "5m",      // Every 5 minutes
      "timer": "1h",      // Every hour
      "timeout": "60s",   // Timeout after 60 seconds
      "timeout": "30m",   // Timeout after 30 minutes
      "schedule-cron": "*/5 * * * *"   // Every 5 minutes (cron)
    }

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s 'Bansuri: {task}' admin@example.com",
      "scripts": [
        {
          "name": "database-backup",
          "command": "pg_dump mydb | gzip > backup.sql.gz",
          "working-directory": "/backups",
          "timer": "86400",
          "timeout": "1h",
          "times": 2,
          "on-fail": "restart",
          "stdout": "backup.log",
          "stderr": "combined",
          "notify": "mail",
          "success-codes": [0],
          "description": "Daily PostgreSQL backup"
        }
      ]
    }

See :doc:`reference` for more examples and :doc:`advanced-config` for complex setups.