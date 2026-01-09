#!/usr/bin/env python3
import os
import time
import signal
import sys
from datetime import datetime
from typing import Dict

from .base.misc.header import HEADER
from .base.misc.help import print_help
from .base.config_manager import BansuriConfig
from .task_runner import TaskRunner


class Orchestrator:

    def __init__(self, config_file="scripts.json", check_interval=30):
        self.config_file = config_file
        self.check_interval = check_interval
        self.runners: Dict[str, TaskRunner] = {}
        self.should_stop = False

        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

        self._log("Orchestrator initialized")

    def _log(self, message):
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [MASTER] {message}",
            flush=True,
        )

    def signal_handler(self, signum, frame):
        self._log(f"Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)

    def sync_tasks(self):

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

        # start added tasks
        for name in new_names - current_names:
            self._log(f"New task found: {name}")
            runner = TaskRunner(new_configs[name])
            self.runners[name] = runner
            runner.start()

        # TODO detect changes on existing tasks and restart if needed

    def stop_all(self):
        self._log("Stopping all tasks...")
        for runner in self.runners.values():
            runner.stop()

    def run(self):
        #print(HEADER)
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


def main():
    config_path = os.path.join(os.path.dirname(__file__), "scripts.json")

    orchestrator = Orchestrator(config_file=config_path, check_interval=5)
    orchestrator.run()


if __name__ == "__main__":
    main()
