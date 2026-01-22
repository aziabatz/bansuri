Bansuri Documentation
=====================

**Task Orchestration & Management System**

Bansuri is a flexible, easy-to-use system for running and monitoring multiple scripts with configurable scheduling, timeouts, retries, and notifications.

✅ **What You Can Do**:
  - Run shell commands on timers or cron schedules
  - Retry failed tasks automatically
  - Monitor task execution with detailed logs
  - Send alerts on failures
  - Manage multiple tasks from one configuration file

⚠️ **What's Coming**: Task dependencies, user switching, hot-reload, and more.

See :ref:`Feature Status <not-implemented>` for implementation details.

.. toctree::
   :maxdepth: 2
   :caption: Start Here

   quickstart
   installation

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   concepts
   architecture

.. toctree::
   :maxdepth: 2
   :caption: Configuration & Usage

   configuration
   reference
   advanced-config
   usage

.. toctree::
   :maxdepth: 2
   :caption: Features & Extensions

   notifications
   custom-tasks
   reference

.. toctree::
   :maxdepth: 2
   :caption: Running Bansuri

   deployment
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing
   api

.. note::

   Check :doc:`NOT_IMPLEMENTED.md` for feature status and workarounds.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`