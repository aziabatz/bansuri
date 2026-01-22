# Bansuri Task System

This project implements a modular task execution system designed for the Bansuri process manager. It separates configuration data from execution logic using a declarative approach.

## Core Components

The system is built around two main components defined in `task_base.py`:

1.  **`TaskConfig`**: A data structure that validates and organizes task settings into logical categories (Identification, Scheduling, Failure Control, Resources, Logging).
2.  **`AbstractTask`**: An abstract base class that defines the interface (`run`, `stop`) for any executable task.

## Configuration

Tasks are configured using a dictionary (typically loaded from a JSON file) that matches the schema defined in `scripts.config.template.json`.

### Example Configuration Dictionary

```json
{
  "name": "backup-service",
  "command": "/usr/local/bin/backup.sh",
  "user": "admin",
  "schedule-cron": "0 2 * * *",
  "times": 3,
  "on-fail": "restart",
  "notify": "on-fail"
}
```

## Implementing a Task

To create a runnable task, you must subclass `AbstractTask` and implement the `run()` and `stop()` methods.

### Example Implementation

Here is how to create a simple shell-based task:

```python
import subprocess
from task_base import AbstractTask, TaskConfig

class ShellTask(AbstractTask):
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self._process = None

    def run(self) -> int:
        cmd = self.config.identification.command
        print(f"Starting task: {self.config.identification.name}")
        
        self._process = subprocess.Popen(
            cmd, 
            shell=True,
            cwd=self.config.identification.working_directory
        )
        
        # Wait for completion
        return_code = self._process.wait()
        return return_code

    def stop(self) -> None:
        if self._process:
            print(f"Stopping {self.config.identification.name}...")
            self._process.terminate()
```

## Usage

### 1. Load Configuration
Use `TaskConfig.from_dict()` to convert a raw dictionary into a structured configuration object.

```python
from task_base import TaskConfig

raw_config = {
    "name": "data-processor",
    "command": "python process_data.py",
    "times": 5,
    "timeout": "10m"
}

config = TaskConfig.from_dict(raw_config)
```

### 2. Instantiate and Run
Pass the configuration object to your concrete task implementation.

```python
task = ShellTask(config)

# Access configuration properties easily
if task.config.scheduling.is_periodic:
    print(f"Task runs on schedule: {task.config.scheduling.schedule_cron}")

# Execute
exit_code = task.run()
print(f"Task finished with code: {exit_code}")
```