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

    .. grid-item-card:: 🚀 Easy to Use
        :text-align: center

        Start managing tasks in minutes with simple JSON configuration.

    .. grid-item-card:: ⏱️ Flexible Scheduling
        :text-align: center

        Timer-based intervals or cron schedules for perfect timing.

    .. grid-item-card:: 🔄 Auto-Retry
        :text-align: center

        Automatic failure recovery with configurable retry logic.

    .. grid-item-card:: 📧 Smart Alerts
        :text-align: center

        Email notifications when tasks fail or need attention.

    .. grid-item-card:: 📊 Full Monitoring
        :text-align: center

        Real-time logs and execution tracking for all tasks.

    .. grid-item-card:: 🛠️ Extensible
        :text-align: center

        Support for shell scripts, Python, and custom implementations.

---

**✅ What You Can Do**:

- ⏰ Run shell commands on timers or cron schedules
- 🔄 Retry failed tasks automatically with configurable policies
- 📝 Monitor task execution with detailed logs and timestamps
- 📧 Send email alerts when tasks fail
- 🎛️ Manage multiple tasks from one configuration file
- ⚙️ Set timeouts, working directories, and output redirection
- ✔️ Define custom success codes for flexible exit handling

**⚠️ Coming Soon**:

- Task dependencies and DAG orchestration
- User switching and process priority control
- Environment file loading
- Hot reload on configuration changes
- AbstractTask Python script support

See :doc:`NOT_IMPLEMENTED.md` for detailed feature status and workarounds.

---

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

.. note::

   📖 **New to documentation?** Check the :doc:`quickstart` for a 5-minute introduction.
   
   🐛 **Found an issue?** Visit our `GitHub Issues <https://github.com/aziabatz/bansuri/issues>`_.
   
   📝 **Want to contribute?** See :doc:`contributing` for guidelines.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`