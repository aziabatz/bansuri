Contributing to Bansuri
=======================

Thank you for your interest in contributing! We welcome pull requests from developers of all skill levels.

Setting up the Development Environment
--------------------------------------

1. **Clone the repository**

   .. code-block:: bash

      git clone https://github.com/aziabatz/bansuri.git
      cd bansuri

2. **Create a virtual environment**

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate

3. **Install the package in editable mode**

   .. code-block:: bash

      pip install -e .

Project Structure
-----------------

* ``bansuri/``: Main package source code.
  * ``master.py``: Orchestrator - main orchestration logic and task coordination.
  * ``task_runner.py``: TaskRunner - task execution and subprocess management.
  * ``base/``: Base classes and configuration management.
    * ``task_base.py``: AbstractTask - base class for custom task implementations.
    * ``config_manager.py``: BansuriConfig and ScriptConfig - configuration data structures.
    * ``config/``: Configuration component classes (Identification, Scheduling, Failure Control, etc.).
    * ``misc/``: Miscellaneous utilities (header, help).
  * ``alerts/``: Notification system.
    * ``notifier.py``: Base notifier interface.
    * ``cmd_notifier.py``: Command-based notifications.
* ``tests/``: Unit and integration tests.
* ``doc/``: Sphinx documentation source.
* ``examples/``: Example scripts and configurations.

Running Tests
-------------

We use ``pytest`` for testing. Ensure all tests pass before submitting a PR:

.. code-block:: bash

   pytest test_scripts.py
   pytest test_notify.py

Documentation
-------------

If you modify the code, please update the docstrings and regenerate the documentation to ensure consistency.

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

To build the Sphinx documentation:

.. code-block:: bash

   cd doc
   make html

The generated documentation will be in ``doc/_build/html/``.