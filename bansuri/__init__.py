"""
Bansuri - Task orchestration and management system.

A flexible system for running and monitoring multiple scripts with configurable
restart policies, timeouts, and logging.
"""

__version__ = "0.1.0"
__author__ = "Blackburn (Ahmed.ZZ)"

from bansuri.task_runner import TaskRunner
from bansuri.base.config_manager import BansuriConfig, ScriptConfig

__all__ = ["TaskRunner", "BansuriConfig", "ScriptConfig"]
