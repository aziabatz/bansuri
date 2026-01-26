.. image:: image.png
   :width: 200px
   :alt: Bansuri Logo
   :align: center

Bansuri Documentation
=====================

.. raw:: html

    <div style="text-align: center; margin: 2em 0;">
        <h2 style="color: #1f77b4; font-size: 1.8em; margin-bottom: 0.5em;">
            Task Orchestration & Management System
        </h2>
        <p style="font-size: 1.2em; color: #666; margin-bottom: 2em;">
            Flexible, reliable task scheduling and monitoring for your scripts
        </p>
    </div>

.. grid:: 1 2 2 3
    :gutter: 2

    .. grid-item-card:: Easy to Use
        :text-align: center

        Simple JSON configuration to start managing tasks in minutes.

    .. grid-item-card:: Flexible Scheduling
        :text-align: center

        Timer-based intervals or cron schedules.

    .. grid-item-card:: Auto-Retry
        :text-align: center

        Automatic failure recovery with configurable retry logic.

    .. grid-item-card:: Smart Alerts
        :text-align: center

        Email notifications on task failure.

    .. grid-item-card:: Monitoring
        :text-align: center

        Real-time logs and execution tracking.

    .. grid-item-card:: Extensible
        :text-align: center

        Support for shell scripts, Python, and custom tasks.

Features
--------

- Run shell commands on timers or cron schedules
- Retry failed tasks automatically with configurable policies
- Monitor task execution with detailed logs and timestamps
- Send email alerts when tasks fail
- Manage multiple tasks from one configuration file
- Set timeouts, working directories, and output redirection
- Define custom success codes for flexible exit handling

.. note::

   **Coming Soon**

   Task dependencies and DAG orchestration, user switching and process priority control, environment file loading, hot reload on configuration changes, and AbstractTask Python script support.

   See :doc:`NOT_IMPLEMENTED` for detailed feature status and workarounds.



**Getting Started**

New to Bansuri? Start here:

.. toctree::
   :maxdepth: 2
   :caption: Start Here

   quickstart
   installation

**Understanding Bansuri**

Learn the core concepts:

.. toctree::
   :maxdepth: 2
   :caption: Core Concepts

   concepts
   architecture

**Configuration & Usage**

Configure your tasks:

.. toctree::
   :maxdepth: 2
   :caption: Configuration & Usage

   configuration
   reference
   advanced-config
   usage

**Features & Extensions**

Advanced features:

.. toctree::
   :maxdepth: 2
   :caption: Features & Extensions

   notifications
   custom-tasks
   reference

**Running Bansuri**

Deploy and manage:

.. toctree::
   :maxdepth: 2
   :caption: Running Bansuri

   deployment
   troubleshooting

**Contributing**

Help improve Bansuri:

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing
   api

---

.. tip::

   New to Bansuri? Check the :doc:`quickstart` for a 5-minute introduction.

.. seealso::

   Found an issue? Visit our `GitHub Issues <https://github.com/aziabatz/bansuri/issues>`_.

   Want to contribute? See :doc:`contributing` for guidelines.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`