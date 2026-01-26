Concepts and Terminology
========================

Core Components
---------------

Task
~~~~

A **task** is a unit of work to be executed by Bansuri.

A task consists of:

- **Name**: Unique identifier
- **Command**: What to execute (shell command)
- **Schedule**: When/how often to run (timer, cron, or once)
- **Policies**: Timeout, retries, notifications

Example:

.. code-block:: json

    {
      "name": "backup-database",
      "command": "pg_dump production | gzip > backup.sql.gz",
      "timer": "86400",
      "timeout": "1h",
      "on-fail": "restart",
      "notify": "mail"
    }

Orchestrator
~~~~~~~~~~~~

The **Orchestrator** is the main coordinator. It:

- Reads configuration from ``scripts.json``
- Creates ``TaskRunner`` for each task
- Monitors all tasks continuously
- Handles graceful shutdown (SIGTERM/SIGINT)
- Syncs configuration changes

The Orchestrator runs continuously in a single process.

TaskRunner
~~~~~~~~~~

Each task gets its own **TaskRunner** that:

- Runs in a dedicated thread
- Spawns the task process
- Manages timeouts and retries
- Captures and redirects output
- Sends notifications on failure

Execution Models
----------------

Bansuri supports different scheduling modes:

**One-Time Execution**

Task runs once at startup:

.. code-block:: json

    {
      "name": "initialize",
      "command": "python init.py"
    }

**Timer-Based** (Fixed Interval)

Task runs repeatedly at fixed intervals:

.. code-block:: json

    {
      "name": "monitor",
      "command": "python health_check.py",
      "timer": "300"
    }

Supported formats:
- ``"60"`` → every 60 seconds
- ``"5m"`` → every 5 minutes
- ``"1h"`` → every hour

**Cron-Based** (Scheduled Times)

Task runs on cron schedule (requires ``croniter``):

.. code-block:: json

    {
      "name": "daily-backup",
      "command": "bash backup.sh",
      "schedule-cron": "0 2 * * *"
    }

Cron format: ``"minute hour day month weekday"``

Execution Control
-----------------

**Failure Handling**

When a task fails (non-zero exit code):

- ``on-fail: "stop"`` → Stop and don't retry (default)
- ``on-fail: "restart"`` → Retry immediately

Combined with ``times`` for max retries:

.. code-block:: json

    {
      "name": "api-sync",
      "command": "python sync.py",
      "on-fail": "restart",
      "times": 3
    }

**Timeout Management**

Kill task if it runs too long:

.. code-block:: json

    {
      "name": "long-task",
      "command": "bash slow.sh",
      "timeout": "30m"
    }

Supported formats:
- ``"30s"`` → 30 seconds
- ``"5m"`` → 5 minutes
- ``"1h"`` → 1 hour

**Success Definition**

By default, only exit code 0 is success. Override with:

.. code-block:: json

    {
      "name": "exit-handler",
      "command": "bash script.sh",
      "success-codes": [0, 1, 2]
    }

Exit codes 1 and 2 won't trigger retries or notifications.

Configuration Synchronization
------------------------------

The Orchestrator monitors ``scripts.json`` for changes:

- **New tasks**: Automatically started
- **Deleted tasks**: Automatically stopped

.. note::

   Modified tasks are not yet automatically restarted (requires hot-reload feature).

Configuration Hierarchy
-----------------------

**Global Configuration** (scripts.json root level)

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail ..."
    }

**Per-task Configuration** (scripts[].* level)

.. code-block:: json

    {
      "name": "task-name",
      "command": "...",
      "timer": "300",
      "timeout": "30s",
      "on-fail": "restart",
      ...
    }

Task Lifecycle
--------------

A task progresses through these states:

1. **PENDING**: Registered in config, waiting to run
2. **RUNNING**: Process spawned with active PID
3. **SUCCESS**: Completed with success code (default: 0)
4. **FAILED**: Exited with non-zero code
5. **TIMEOUT**: Killed due to exceeding timeout
6. **RESTARTING**: Retrying after failure (if on-fail=restart)
7. **STOPPED**: Removed from config or shutdown

State Transitions
~~~~~~~~~~~~~~~~~

.. code-block:: text

    PENDING
      ↓
    RUNNING → SUCCESS (end)
      ↓
    FAILED
      ↓
    on-fail=stop? → STOPPED (end)
          │
          ↓ on-fail=restart?
    RESTARTING
      ↓
    (back to RUNNING)

Failure Policies
----------------

**on-fail: "stop"** (default)

Task stops immediately on failure:

.. code-block:: text

    RUNNING → FAILED → STOPPED

**on-fail: "restart"**

Task restarts up to ``times`` attempts:

.. code-block:: text

    RUNNING → FAILED → RESTARTING → RUNNING → FAILED → ... (up to 'times')
    
    If max attempts reached:
    FAILED → STOPPED

Example:

.. code-block:: json

    {
      "on-fail": "restart",
      "times": 3
    }

Timeout Behavior
~~~~~~~~~~~~~~~~

When timeout is exceeded:

.. code-block:: text

    RUNNING → (timeout reached) → FAILED → (apply on-fail policy)

The process is forcefully terminated with SIGKILL.

Success Codes
~~~~~~~~~~~~~

By default, only exit code ``0`` is considered success. You can define custom success codes:

.. code-block:: json

    {
      "success-codes": [0, 2, 137]
    }

Exit codes not in this list are considered failures.

Output Management
-----------------

Bansuri redirects task output according to configuration:

**No redirection**

Output goes to console (Bansuri's stdout/stderr):

.. code-block:: json

    {}

**File redirection**

.. code-block:: json

    {
      "stdout": "/var/log/task.log",
      "stderr": "combined"
    }

**Separate files**

.. code-block:: json

    {
      "stdout": "/var/log/task.out",
      "stderr": "/var/log/task.err"
    }

**Combined output**

Both stdout and stderr go to the same file:

.. code-block:: json

    {
      "stderr": "combined"
    }

Resource Management
-------------------

**Working Directory**

Tasks execute in the specified directory. Affects:

- Relative paths in commands
- File operations
- Working directory of child processes

**Timeout**

Maximum time a task can run. Process killed if exceeded.

Units:
- Seconds: ``"30"`` or ``30``
- Seconds suffix: ``"30s"``
- Minutes: ``"5m"`` = 300 seconds
- Hours: ``"2h"`` = 7200 seconds

**Process Groups**

Each task runs in its own process group. Allows:

- Killing task and all children
- Resource isolation
- Clean shutdown

Notification System
-------------------

Triggered on task failure when ``notify: "mail"`` is set.

Components:

- **FailureInfo**: Data structure with failure details
- **Notifier**: Abstract base class for notification handlers
- **CommandNotifier**: Sends notification via shell command

Failure notification includes:

- Task name and command
- Return code and exit details
- Attempt number
- Timestamp
- Stdout/stderr output
- Task description

See :doc:`notifications` for details.

Abstract Tasks
--------------

Custom task implementations implement the ``AbstractTask`` interface:

.. code-block:: python

    class AbstractTask(ABC):
        @abstractmethod
        def run(self) -> int:
            """Execute task, return exit code"""
            pass
        
        @abstractmethod
        def stop(self) -> None:
            """Stop task if running"""
            pass

Benefits:

- Complex business logic
- Native Python integration
- Stateful operations
- Resource cleanup

See :doc:`custom-tasks` for examples.

Configuration Management
------------------------

**Loading**

Configuration loaded from ``scripts.json`` when Bansuri starts:

1. Parse JSON file
2. Validate schema
3. Create ``BansuriConfig`` object
4. Spawn ``TaskRunner`` for each script

**Validation**

Each script is validated for:

- Required fields (name, command)
- Valid field types
- Sensible values
- Scheduling requirements

**Synchronization**

Bansuri periodically syncs config changes:

1. Detect added tasks → spawn ``TaskRunner``
2. Detect removed tasks → stop and remove ``TaskRunner``
3. Detect modified tasks → restart ``TaskRunner``

Performance Concepts
--------------------

**Concurrency**

Each task runs in its own thread. Multiple tasks execute concurrently.

**I/O-bound tasks** (network, disk):
- Can run many concurrently
- Limited by system I/O, not CPU

**CPU-bound tasks** (computation):
- Limited by CPU cores
- Too many concurrent = resource contention

**Resource Limits**

Monitor and limit:

- Memory: Each process and total system
- CPU: Per-process or total
- File descriptors
- Disk I/O

Observability Concepts
----------------------

**Logging**

Structured logging from:

- Orchestrator: Task lifecycle events
- TaskRunner: Execution events
- Tasks: Custom logs

**Monitoring**

Observable metrics:

- Task execution count
- Success/failure rates
- Execution time
- Resource usage
- Timeout occurrences

**Alerting**

Based on:

- Task failures
- Notification triggers
- System resource issues
- Configuration changes

Security Concepts
-----------------

**Process Isolation**

Each task runs in separate process with:

- Independent memory space
- Own file descriptors
- Own process group

**User Context**

(NOT IMPLEMENTED) Tasks can run as specific users with:

- Reduced privileges
- Different permissions
- Isolated home directories

**Working Directory**

Controls where tasks execute and what files they access.

**Permissions**

- Script execute permissions
- Log directory write permissions
- Output file creation permissions

High Availability Concepts
---------------------------

**Restart Policies**

Automatic recovery from failures:

- ``on-fail: "restart"``
- ``times: N`` attempts
- Configurable retry behavior

**Health Checks**

Monitor task execution:

- Track exit codes
- Detect hangs
- Measure latency

**Graceful Shutdown**

Clean termination:

1. Send SIGTERM to tasks
2. Wait for graceful shutdown
3. Force SIGKILL if needed
4. Flush logs and state

Scaling Concepts
----------------

**Single Instance**

Suitable for:

- < 100 tasks
- < 1000 executions/minute
- Single machine
- Non-critical workloads

**Multiple Instances**

For larger deployments:

- Partition tasks across instances
- Share configuration via version control
- Centralize logging
- Coordinate via monitoring

**Containerized Deployment**

Run in:

- Docker containers
- Kubernetes pods
- Cloud container services

Benefits:

- Reproducible environment
- Easy scaling
- Simplified deployment
- Resource limits

Related Concepts
----------------

**Cron** (traditional Linux scheduling)

Similar to Bansuri's timer-based execution but:

- System-level scheduler
- Separate from process lifecycle
- Limited monitoring

Bansuri advantages:

- Process-level control
- In-memory state
- Unified logging
- Flexible retry logic

**Process Managers** (supervisord, systemd)

Similar in goal but different scope:

- Process managers: Keep services running
- Bansuri: Orchestrate task execution

Bansuri can run under process managers for higher availability.

Terminology Reference
---------------------

===================  ===========================================================
Term                 Definition
===================  ===========================================================
Orchestrator         Central coordinator managing all tasks
TaskRunner           Thread-based executor for a single task
Task                 Unit of work to be executed
Script               Configuration entry for a task
Configuration        JSON file defining tasks and behavior
Exit Code            Process return value (0=success, non-zero=failure)
Timeout              Maximum execution time for a task
Failure Policy       What to do when task fails (stop or restart)
Notification         Alert sent when task fails
FailureInfo          Data structure with task failure details
Process Group        Group of processes from same task
Working Directory    Directory where task executes
Success Codes        Exit codes considered successful
===================  ===========================================================
