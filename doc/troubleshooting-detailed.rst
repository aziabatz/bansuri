Troubleshooting Guide
=====================

Common problems and their solutions.

Task Execution Issues
---------------------

Task fails to start
~~~~~~~~~~~~~~~~~~~

**Symptoms**: Task status is ``FAILED`` immediately or doesn't run at all.

**Possible Causes**:

1. **Invalid command path**: Command doesn't exist or isn't in PATH
2. **Missing permissions**: User running Bansuri can't execute the command
3. **Incorrect working directory**: Directory doesn't exist or isn't readable
4. **Syntax errors in scripts**: Shell scripts have errors

**Solutions**:

Test the command manually:

.. code-block:: bash

    # As the bansuri user
    sudo -u bansuri bash -c "cd /working/dir && /path/to/command"

Verify command exists:

.. code-block:: bash

    which command_name
    ls -la /path/to/command

Check file permissions:

.. code-block:: bash

    ls -la /path/to/command
    # Should be executable: -rwxr-xr-x or similar

Check working directory:

.. code-block:: bash

    ls -la /working/directory
    # Ensure directory exists and is readable

Verify shell script syntax:

.. code-block:: bash

    bash -n /path/to/script.sh

Task timeout issues
~~~~~~~~~~~~~~~~~~~

**Symptoms**: Tasks are killed unexpectedly or run too long.

**Possible Causes**:

1. **Timeout too short**: Legitimate tasks exceed configured timeout
2. **Hanging process**: Process is blocked waiting for I/O or network
3. **Zombie processes**: Child processes not properly cleaned up
4. **Resource contention**: System is under heavy load

**Solutions**:

Increase timeout:

.. code-block:: json

    {
      "name": "slow-task",
      "command": "heavy-operation.sh",
      "timeout": "30m"
    }

Debug process hanging:

.. code-block:: bash

    # Monitor the process
    strace -p <PID> -e trace=network,open,read,write

    # Check system load
    uptime
    free -h
    df -h

Check for zombie processes:

.. code-block:: bash

    ps aux | grep defunct
    # If found, restart Bansuri

Task returns wrong exit code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Task shows as failed but should be success, or vice versa.

**Possible Causes**:

1. **Script returns non-zero for success**: Script's exit logic is reversed
2. **Unexpected errors**: Script encountered error but doesn't propagate
3. **Missing success code configuration**: Success codes not configured correctly

**Solutions**:

Configure success codes:

.. code-block:: json

    {
      "name": "task-with-warnings",
      "command": "checker.sh",
      "success-codes": [0, 2, 3]
    }

Test script exit codes:

.. code-block:: bash

    ./script.sh
    echo $?  # Print exit code

    # Test different scenarios
    ./script.sh arg1 arg2
    echo $?

Configuration Issues
--------------------

JSON parsing errors
~~~~~~~~~~~~~~~~~~~

**Symptoms**: "Error decoding JSON" message.

**Solutions**:

Validate JSON syntax:

.. code-block:: bash

    python -m json.tool scripts.json

Use online JSON validator:

.. code-block:: bash

    curl -X POST https://jsonlint.com/api/validate \
         -d @scripts.json

Check for common mistakes:

.. code-block:: bash

    # Trailing commas
    grep -n ",$" scripts.json | tail -10

    # Mixed quotes
    grep -n "'" scripts.json

Missing required fields
~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: "Missing required fields" error.

**Solutions**:

Verify all required fields are present:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    config = BansuriConfig.load_from_file('scripts.json')
    "

Check schema:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import ScriptConfig
    import inspect
    print(inspect.signature(ScriptConfig))
    "

Invalid timeout format
~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Timeout is parsed incorrectly.

**Valid formats**:

.. code-block:: json

    {
      "timeout": "30"
    },
    {
      "timeout": "30s"
    },
    {
      "timeout": "5m"
    },
    {
      "timeout": "1h"
    }

Performance Issues
------------------

High memory usage
~~~~~~~~~~~~~~~~~

**Symptoms**: Process consumes excessive memory, system OOM killer triggers.

**Possible Causes**:

1. **Large log files**: Stderr/stdout buffering too much data
2. **Memory leak in task**: Task is leaking memory
3. **Too many concurrent tasks**: Running too many tasks simultaneously

**Solutions**:

Redirect output to files:

.. code-block:: json

    {
      "name": "verbose-task",
      "command": "data-process.sh",
      "stdout": "/var/log/output.log",
      "stderr": "combined"
    }

Limit task concurrency:

.. code-block:: bash

    # Monitor concurrent tasks
    ps aux | grep python | wc -l

    # Increase timer intervals to reduce concurrency
    "timer": "3600"  # Run hourly instead of frequently

Monitor memory in real-time:

.. code-block:: bash

    watch -n 1 'ps aux | grep bansuri | head -1'

High CPU usage
~~~~~~~~~~~~~~

**Symptoms**: Bansuri or tasks consume excessive CPU.

**Solutions**:

Identify which task uses CPU:

.. code-block:: bash

    # In another terminal, monitor processes
    watch -n 1 'ps aux --sort=-%cpu | head -10'

Reduce execution frequency:

.. code-block:: json

    {
      "timer": "300"
    }

Check for tight loops:

.. code-block:: bash

    # Profile the task
    python -m cProfile -s cumtime task.py

Slow task execution
~~~~~~~~~~~~~~~~~~~

**Symptoms**: Tasks take longer than expected.

**Solutions**:

Profile task execution:

.. code-block:: bash

    time ./script.sh

Check system resources during execution:

.. code-block:: bash

    # Terminal 1: Run task
    ./script.sh

    # Terminal 2: Monitor
    watch -n 1 'top -p $(pgrep -f script.sh)'

Check for I/O bottlenecks:

.. code-block:: bash

    iotop -o -b -n 1

Logging and Debugging
---------------------

Enable debug logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    export BANSURI_LOG_LEVEL=DEBUG
    python -m bansuri

View logs
~~~~~~~~~

For systemd:

.. code-block:: bash

    # Live logs
    journalctl -u bansuri -f

    # Last 100 lines
    journalctl -u bansuri -n 100

    # Since specific time
    journalctl -u bansuri --since "2024-01-19 10:00:00"

For file logging:

.. code-block:: bash

    tail -f /var/log/bansuri/bansuri.log

Debug specific task
~~~~~~~~~~~~~~~~~~~

Run task manually with debugging:

.. code-block:: bash

    # With bash debugging
    bash -x ./script.sh

    # With Python debugging
    python -u -m pdb task.py

    # With strace (system calls)
    strace -f ./script.sh

Notification Issues
-------------------

Notifications not being sent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Task fails but no notification received.

**Possible Causes**:

1. ``notify`` field not set to ``"mail"``
2. ``notify_command`` not configured
3. Notification command fails
4. Network connectivity issues

**Solutions**:

Verify configuration:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    config = BansuriConfig.load_from_file('scripts.json')
    print(f'notify_command: {config.notify_command}')
    for script in config.scripts:
        print(f'{script.name}: notify={script.notify}')
    "

Test notification command:

.. code-block:: bash

    # Test email
    echo 'Test message' | mail -s 'Test' your-email@example.com

    # Test curl webhook
    curl -X POST https://your-webhook-url \
         -d 'Test message'

Check notification in logs:

.. code-block:: bash

    journalctl -u bansuri | grep -i notif

Connection Issues
-----------------

Cannot connect to remote services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Task fails when connecting to external services.

**Solutions**:

Test connectivity:

.. code-block:: bash

    # Test DNS
    nslookup example.com

    # Test port connectivity
    nc -zv example.com 443

    # Test HTTP request
    curl -v https://api.example.com

Check firewall rules:

.. code-block:: bash

    # Check iptables (if using Linux firewall)
    sudo iptables -L -n

    # Check firewall status
    sudo systemctl status firewalld  # Red Hat
    sudo ufw status                  # Ubuntu

Restart Issues
--------------

Bansuri won't restart
~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Service fails to start after configuration change.

**Solutions**:

Validate configuration before restart:

.. code-block:: bash

    python -c "
    from bansuri.base.config_manager import BansuriConfig
    try:
        config = BansuriConfig.load_from_file('scripts.json')
        print('Configuration is valid')
    except Exception as e:
        print(f'Configuration error: {e}')
    "

Check logs:

.. code-block:: bash

    journalctl -u bansuri -n 50 -p err

Force-stop if stuck:

.. code-block:: bash

    sudo systemctl stop bansuri
    pkill -9 -f "python -m bansuri"
    sleep 2
    sudo systemctl start bansuri

Getting Help
------------

Collecting diagnostic information:

.. code-block:: bash

    # System information
    uname -a
    python --version
    pip list | grep bansuri

    # Configuration
    cat scripts.json

    # Recent logs
    journalctl -u bansuri -n 100

    # Running processes
    ps aux | grep bansuri

    # Resource usage
    ps aux | grep bansuri | head -1
    free -h
    df -h

Report issues with this information to help diagnose problems faster.
