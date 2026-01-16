#!/usr/bin/env python3
import os
import time
import signal
import sys
from datetime import datetime
from typing import Dict


from bansuri.base.misc.header import HEADER
from bansuri.base.misc.help import print_help
from bansuri.base.config_manager import BansuriConfig
from bansuri.task_runner import TaskRunner



class Orchestrator:

    def __init__(self, config_file="scripts.json", check_interval=30):
        """Orchestrator init

        Args:
            config_file (str, optional): Path to config file. Defaults to "scripts.json".
            check_interval (int, optional): Check interval in seconds. Defaults to 30.
        """
        self.config_file = config_file
        self.check_interval = check_interval
        self.runners: Dict[str, TaskRunner] = {}
        self.should_stop = False

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self._log("Orchestrator initialized")

    def _log(self, message):
        # TODO add pluggable logger
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MASTER] {message}",
            flush=True,
        )

    def signal_handler(self, signum, frame):
        """
        POSIX signal handling

        :param signum: Signal identifier
        :param frame: Unused
        """
        self._log(f"Received signal {signum}, shutting down...")
        # TODO shutdown only on SIGTERM
        self.stop_all()
        sys.exit(0)

    def sync_tasks(self):
        """
        Synchronize tasks from config file.
        """

        try:

            config = BansuriConfig.load_from_file(self.config_file)
        except Exception as e:
            self._log(f"Error loading config: {e}")
            return

        # Map config fields by name
        new_configs = {s.name: s for s in config.scripts}

        current_names = set(self.runners.keys())
        new_names = set(new_configs.keys())

        # we stop tasks which are no longer in config
        for name in current_names - new_names:
            self._log(f"Task removed from config: {name}")
            self.runners[name].stop()
            del self.runners[name]

        # Check for updates in existing tasks
        for name in current_names.intersection(new_names):
            current_runner = self.runners[name]
            new_config = new_configs[name]

            if current_runner.config != new_config:
                self._log(f"Configuration changed for task: {name}. Restarting...")
                current_runner.stop()
                del self.runners[name]
                # It will be re-added in the next loop (actually no, we must add it here or treat it as new)
                # Better approach: restart it immediately here
                runner = TaskRunner(new_config, config)
                self.runners[name] = runner
                runner.start()

        # Start added tasks
        # The set 'new_names - current_names' is strictly for NEW task names.
        # The updated ones are handled above.
        for name in new_names - current_names:
            self._log(f"New task found: {name}")

            # Check for NOT IMPLEMENTED features
            cfg = new_configs[name]
            if cfg.depends_on:
                self._log(f"WARNING [{name}]: depends-on NOT IMPLEMENTED")
            if cfg.user:
                self._log(f"WARNING [{name}]: user switching NOT IMPLEMENTED")
            if cfg.priority:
                self._log(f"WARNING [{name}]: priority NOT IMPLEMENTED")
            if cfg.environment_file:
                # TODO implement
                self._log(f"WARNING [{name}]: environment-file NOT IMPLEMENTED")
            if cfg.success_codes:
                # TODO implement
                self._log(f"WARNING [{name}]: success-codes NOT IMPLEMENTED")
            if cfg.notify:
                # TODO implement
                self._log(f"WARNING [{name}]: notify NOT IMPLEMENTED")

            runner = TaskRunner(new_configs[name], config)
            self.runners[name] = runner
            runner.start()

    def stop_all(self):
        self._log("Stopping all tasks...")
        for runner in self.runners.values():
            runner.stop()

    def run(self):
        # print(HEADER)
        self._log("=" * 40)
        self._log("BANSURI ORCHESTRATOR STARTED")
        self._log("=" * 40)
        self._log(f"Monitoring config file: {self.config_file}")

        while not self.should_stop:
            try:
                self.sync_tasks()
                time.sleep(self.check_interval)
            except Exception as e:
                self._log(f"ERROR in main loop: {e}")
                time.sleep(self.check_interval)


# TODO add -c option for specifying configfile
def main():
    config_path = os.path.join(os.path.dirname(__file__), "scripts.json")

    orchestrator = Orchestrator(config_file=config_path, check_interval=5)
    orchestrator.run()


if __name__ == "__main__":
    main()
