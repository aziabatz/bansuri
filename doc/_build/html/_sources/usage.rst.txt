Usage
=====

Basic Usage
-----------

To start the orchestration system from the command line:

.. code-block:: bash

   bansuri

This will load ``scripts.json`` from the current working directory and start monitoring tasks according to the configuration.

To specify a different configuration file:

.. code-block:: bash

   bansuri --config /path/to/scripts.json

Programmatic Usage
~~~~~~~~~~~~~~~~~~~

You can also use Bansuri as a library:

.. code-block:: python

   from bansuri.master import Orchestrator
   from bansuri.base.config_manager import BansuriConfig

   # Load configuration
   config = BansuriConfig.load_from_file("scripts.json")

   # Create and start orchestrator
   orchestrator = Orchestrator(config_file="scripts.json")
   orchestrator.start()

Configuration
-------------

Bansuri is configured primarily through the ``scripts.json`` file.

For a detailed guide on how to add new scripts or modify existing parameters, please refer to the :doc:`configuration` guide.