Troubleshooting
===============

Common problems and solutions.

Task Issues
-----------

Task Won't Start
~~~~~~~~~~~~~~~~

**Symptom**: Task stays ``PENDING`` or immediately fails

**Checklist**:

1. Does ``scripts.json`` have valid JSON syntax?

   .. code-block:: bash

      python -m json.tool scripts.json

2. Is the ``command`` executable?

   .. code-block:: bash

      # Test the command directly
      bash -x "your-command"

3. Does the file exist and have permissions?

   .. code-block:: bash

      ls -l /path/to/script.sh
      chmod +x /path/to/script.sh

4. Are you using an absolute path?

   ✅ Good:

   .. code-block:: json

      "command": "/usr/local/bin/backup.sh"

   ❌ Bad:

   .. code-block:: json

      "command": "backup.sh"

---

Task Runs But Fails
~~~~~~~~~~~~~~~~~~~

**Symptom**: Task exits with non-zero code

**Checklist**:

1. Check exit code in logs

   .. code-block:: text

      [task] Process finished with code 127   # Command not found
      [task] Process finished with code 1     # General error
      [task] Process finished with code 126   # Permission denied

2. Run command manually to see error:

   .. code-block:: bash

      bash -x /path/to/script.sh

3. Check for missing environment variables:

   .. code-block:: json

      "working-directory": "/app",
      "command": "python main.py"

4. Consider adding to ``success-codes`` if non-zero is acceptable:

   .. code-block:: json

      "success-codes": [0, 1]

---

Task Runs Forever
~~~~~~~~~~~~~~~~~

**Symptom**: Task completes but ``RUNNING`` status persists

**Fix**: Set a ``timeout``

.. code-block:: json

    {
      "name": "hanging-task",
      "command": "python task.py",
      "timeout": "30s"
    }

---

High Memory Usage
~~~~~~~~~~~~~~~~~

**Symptom**: Bansuri process grows in memory

**Causes**:

- Task produces huge output
- Many tasks logging to memory

**Solutions**:

1. Redirect output to files:

   .. code-block:: json

      "stdout": "/var/log/task.log",
      "stderr": "combined"

2. Or in the command itself:

   .. code-block:: json

      "command": "python task.py > /tmp/output.log 2>&1"

3. Limit number of tasks

---

Configuration Issues
--------------------

"croniter not found" Error
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: When using ``schedule-cron``

.. code-block:: text

    ERROR: 'croniter' library is missing

**Fix**:

.. code-block:: bash

    pip install croniter

---

Notification Not Sending
~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: Task fails but no email arrives

**Checklist**:

1. Is ``notify`` set to ``"mail"``?

   .. code-block:: json

      "notify": "mail"

2. Is ``notify_command`` configured?

   .. code-block:: json

      "notify_command": "mail -s 'Alert: {task}' admin@example.com"

3. Is ``mail`` command available?

   .. code-block:: bash

      which mail
      # If missing:
      sudo apt-get install mailutils   # Ubuntu
      sudo yum install mailx            # CentOS

4. Test mail manually:

   .. code-block:: bash

      echo "test" | mail -s "Test" admin@example.com

---

Invalid Configuration
^^^^^^^^^^^^^^^^^^^^^

**Symptom**: Tasks ignored, no error messages

**Check**:

1. JSON syntax:

   .. code-block:: bash

      python -m json.tool scripts.json

2. Required fields:

   .. code-block:: json

      {
        "name": "...",       // REQUIRED
        "command": "...",    // REQUIRED
        "version": "1.0"     // Recommended
      }

3. Validate with Python:

   .. code-block:: python

      from bansuri.base.config_manager import BansuriConfig
      config = BansuriConfig.load_from_file('scripts.json')

---

Cron Not Working
^^^^^^^^^^^^^^^

**Symptom**: ``schedule-cron`` doesn't trigger

**Check cron expression**:

.. code-block:: python

    from croniter import croniter
    from datetime import datetime

    cron = "0 2 * * *"  # Your expression
    if croniter.is_valid(cron):
        print("Valid")
        c = croniter(cron)
        print(f"Next run: {c.get_next(datetime)}")
    else:
        print("Invalid cron expression")

**Common cron patterns**:

.. code-block:: text

    "0 2 * * *"      → Daily at 2 AM
    "*/5 * * * *"    → Every 5 minutes
    "0 */6 * * *"    → Every 6 hours
    "0 0 1 * *"      → Monthly on 1st

---

Restart / Recovery
------------------

Restart Bansuri
~~~~~~~~~~~~~~~

.. code-block:: bash

    # If running systemd
    sudo systemctl restart bansuri

    # If running manually
    Ctrl+C  # Stop
    bansuri # Restart

---

Force Stop Hung Task
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Find process
    ps aux | grep bansuri

    # Send signal
    kill -15 <PID>       # Graceful
    kill -9 <PID>        # Force

---

Reset All Tasks
^^^^^^^^^^^^^^^

Stop Bansuri and remove any state files:

.. code-block:: bash

    # Stop Bansuri
    bansuri stop

    # Optional: Clean logs
    rm /var/log/bansuri.log*

    # Restart
    bansuri

---

Getting Help
------------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Check current logs (follow mode)
    tail -f /var/log/bansuri.log | grep ERROR

    # Look for specific task
    grep "task-name" /var/log/bansuri.log

Check Bansuri Status
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Show running processes
    ps aux | grep bansuri

    # Check ports (if applicable)
    netstat -tlnp | grep bansuri

    # Show config being used
    cat scripts.json | python -m json.tool

Need More Help?
^^^^^^^^^^^^^^^

1. Check :doc:`../NOT_IMPLEMENTED.md` for known limitations
2. Review :doc:`configuration` for correct parameter format
3. See :doc:`reference` for examples
4. Visit GitHub issues: https://github.com/aziabatz/bansuri/issues