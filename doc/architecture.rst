System Architecture
===================

Bansuri is designed as a modular task orchestration system. It separates the concerns of task definition, scheduling, and execution monitoring.

High-Level Overview
-------------------

The system consists of two main components:

1. **Orchestrator**: Reads the configuration from ``scripts.json``, manages the lifecycle of all tasks, synchronizes configuration changes, and coordinates task execution.
2. **TaskRunner**: Encapsulates the logic for spawning a subprocess, managing a control thread, capturing output, and handling lifecycle events (start, stop, timeout, restarts).

.. note::
    Bansuri uses Python's ``subprocess`` module for process isolation, ensuring that a crashing script does not bring down the main orchestrator. Each task runs in its own thread and process.

Execution Models
----------------

Bansuri supports multiple execution models through ``TaskRunner``:

* **Simple Execution**: Run the task once and stop.
* **Timer-based Execution**: Run the task at fixed intervals (configured via ``timer`` parameter).
* **Cron-based Execution**: Run the task on a schedule (configured via ``schedule-cron``). NOT IMPLEMENTED.

Task Lifecycle
--------------

A task goes through several states during its execution:

* **PENDING**: The task is about to start (in the execution loop).
* **RUNNING**: The process has been spawned and has an active PID.
* **COMPLETED**: The process exited with a success code (default: 0).
* **FAILED**: The process exited with a non-zero return code or was killed.
* **TIMED_OUT**: The TaskRunner killed the process because it exceeded its ``timeout`` limit.

Error Handling and Restart Policies
------------------------------------

If a task fails, the **on-fail** policy kicks in:

* **"stop"**: Task execution stops immediately on failure.
* **"restart"**: Task is restarted up to ``times`` attempts with a brief delay between attempts.

The configuration in :doc:`configuration` determines the behavior on task failure.

Output Management
-----------------

Bansuri redirects stdout and stderr according to the task configuration:

* **"combined"** (default): Both stdout and stderr are written to the same file.
* **File path**: Stdout/stderr are redirected to the specified file.
* **None**: Output is not captured.

Extensibility
-------------

Bansuri is built to be extended. You can create custom task implementations by inheriting from the ``AbstractTask`` class and implementing the ``run()`` and ``stop()`` methods. Tasks implementing this interface can be loaded and executed by Bansuri with the ``no-interface`` configuration option.

Notification System
-------------------

Bansuri includes a notification system that can alert you when tasks fail. The system is extensible and supports:

* **Command-based notifications**: Execute any shell command to send alerts (email, Slack, webhooks, etc.)
* **Custom notifiers**: Extend the ``Notifier`` base class to implement custom notification handlers

For detailed information, see :doc:`notifications`.