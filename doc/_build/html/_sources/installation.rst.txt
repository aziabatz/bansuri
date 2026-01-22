Installation
=============

Install Bansuri and its optional dependencies.

Requirements
~~~~~~~~~~~~

- Python 3.8 or higher
- ``pip`` package manager
- ``git`` (for source installation)

Installation Methods
--------------------

From Source (Recommended for Development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    git clone https://github.com/aziabatz/bansuri.git
    cd bansuri
    pip install -e .

Verify installation:

.. code-block:: bash

    bansuri --help

Optional Dependencies
---------------------

**For Cron Scheduling**:

.. code-block:: bash

    pip install croniter

This enables ``schedule-cron`` field in tasks.

**For Email Notifications**:

You need system ``mail`` command (usually pre-installed):

.. code-block:: bash

    # Ubuntu/Debian
    sudo apt-get install mailutils

    # CentOS/RHEL
    sudo yum install mailx

    # macOS
    # Usually pre-installed

**For Python Script Tasks** (Future):

Install any dependencies your Python scripts need.

Verify Installation
-------------------

Check that Bansuri is installed correctly:

.. code-block:: bash

    python -c "import bansuri; print(bansuri.__version__)"

Expected output:

.. code-block:: text

    0.1.0

Next Steps
----------

1. Read the :doc:`quickstart` guide
2. Check :doc:`configuration` documentation
3. Explore :doc:`reference` for all options
4. See :doc:`troubleshooting` if issues arise