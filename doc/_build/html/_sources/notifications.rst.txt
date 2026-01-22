Notifications
==============

Bansuri includes a built-in notification system to alert you when tasks fail. This allows you to respond quickly to issues in your orchestrated tasks.

Overview
--------

The notification system is triggered when a task fails (returns a non-zero exit code) and the ``notify`` configuration option is set to ``"mail"``. Notifications are sent using a command-based system, allowing integration with any notification service (email, Slack, webhooks, etc.).

Configuration
-------------

To enable notifications, you need to:

1. Set the ``notify`` field in your task configuration to ``"mail"``
2. Configure a global ``notify_command`` in your ``scripts.json``

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "version": "1.0",
      "notify_command": "mail -s '[Bansuri] Task Failed' your-email@example.com",
      "scripts": [
        {
          "name": "critical-backup",
          "command": "/usr/local/bin/backup.sh",
          "timer": "3600",
          "notify": "mail",
          "on-fail": "restart",
          "times": 3
        }
      ]
    }

Configuration Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

- **notify_command** (global): Shell command to execute for sending notifications. The command receives the failure message as input.
  
  Examples:
  
  - Email: ``"mail -s '[Bansuri] Task Failed' admin@example.com"``
  - Slack: ``"curl -X POST -d @- https://hooks.slack.com/services/YOUR/WEBHOOK/URL"``
  - Webhook: ``"curl -X POST -H 'Content-Type: application/json' -d @- https://your-api.example.com/notify"``

- **notify** (per-task): Set to ``"mail"`` to enable notifications for this task, or ``"none"`` to disable.

Failure Information
-------------------

When a task fails, Bansuri sends the following information in the notification:

- **Task Name**: Unique identifier of the failed task
- **Command**: The command that was executed
- **Working Directory**: The directory where the command ran
- **Return Code**: Exit code of the failed process
- **Attempt**: Which attempt this was (e.g., "2/3")
- **Timestamp**: When the failure occurred
- **Description**: Task description (if provided)
- **Stdout**: Standard output captured from the failed task
- **Stderr**: Standard error output captured from the failed task

Notification Message Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The notification is formatted as follows:

.. code-block:: text

    === [Bansuri] Task Failure ===
    
    Task 'task-name' has failed.
    
    --- Task Details ---
    Name:              task-name
    Command:           /path/to/command
    Working Directory: /working/dir
    Return Code:       1
    Attempt:           2/3
    Timestamp:         2026-01-19 14:30:45
    Description:       Optional task description
    
    --- Output ---
    (stdout from task)
    
    --- Error ---
    (stderr from task)
    
    ---
    This is an automated message from Bansuri Orchestrator.

API Reference
-------------

Notifier Base Class
~~~~~~~~~~~~~~~~~~~

.. autoclass:: bansuri.alerts.notifier.Notifier
   :members:
   :undoc-members:
   :show-inheritance:

FailureInfo Data Class
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: bansuri.alerts.notifier.FailureInfo
   :members:
   :undoc-members:

CommandNotifier Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: bansuri.alerts.cmd_notifier.CommandNotifier
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Email Notifications
~~~~~~~~~~~~~~~~~~~

Send notifications via email using the ``mail`` command:

.. code-block:: json

    {
      "notify_command": "mail -s '[Bansuri Alert] Task Failed' ops-team@company.com",
      "scripts": [
        {
          "name": "database-backup",
          "command": "pg_dump production > /backups/db.sql",
          "timer": "86400",
          "notify": "mail",
          "on-fail": "restart",
          "times": 2
        }
      ]
    }

Slack Notifications
~~~~~~~~~~~~~~~~~~~

Send notifications to a Slack channel:

.. code-block:: json

    {
      "notify_command": "curl -X POST -d @- https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "scripts": [
        {
          "name": "critical-service",
          "command": "systemctl restart myservice",
          "timer": "300",
          "notify": "mail",
          "on-fail": "stop"
        }
      ]
    }

Custom Webhook
~~~~~~~~~~~~~~

Send notifications to a custom API endpoint:

.. code-block:: json

    {
      "notify_command": "curl -X POST -H 'Content-Type: application/json' -d @- https://monitoring.company.com/api/alerts",
      "scripts": [
        {
          "name": "health-check",
          "command": "/opt/health-check.py",
          "timer": "600",
          "notify": "mail",
          "on-fail": "restart",
          "times": 3
        }
      ]
    }

Extending the Notification System
----------------------------------

You can create custom notifier implementations by subclassing the ``Notifier`` base class:

.. code-block:: python

    from bansuri.alerts.notifier import Notifier, FailureInfo

    class SlackNotifier(Notifier):
        def __init__(self, webhook_url: str):
            self.webhook_url = webhook_url

        def notify(self, failure_info: FailureInfo) -> bool:
            # Your implementation to send to Slack
            message = f"Task '{failure_info.task_name}' failed with code {failure_info.return_code}"
            # ... send to Slack ...
            return True

Then modify the ``TaskRunner._create_notifier()`` method to use your custom notifier.

Troubleshooting
---------------

Notifications not being sent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Tasks are failing but no notifications are received.

**Solutions**:

1. Verify the ``notify`` field is set to ``"mail"`` in the task configuration
2. Check that ``notify_command`` is defined at the global level in ``scripts.json``
3. Test the notify command manually:

   .. code-block:: bash

      echo "Test message" | mail -s "Test" your-email@example.com

4. Check Bansuri logs for error messages related to notification sending

4. Ensure the user running Bansuri has permissions to execute the notify command

Notification timeout
~~~~~~~~~~~~~~~~~~~~

**Issue**: Notifications are causing tasks to hang or slow down.

**Solution**: The ``CommandNotifier`` has a default 30-second timeout. To increase it, modify the timeout in ``TaskRunner._create_notifier()``:

.. code-block:: python

    return CommandNotifier(notify_cmd, timeout=60)  # 60 seconds

Integration Notes
-----------------

- Notifications are sent **asynchronously** within the task execution thread, so they won't block task execution.
- If a notification fails, it's logged but doesn't affect the task execution flow.
- The notification message is formatted with escaped newlines (``\\n``) for compatibility with shell commands.
