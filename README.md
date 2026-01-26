# Bansuri

Task orchestration and management system for running and monitoring multiple scripts.

## Overview

Bansuri is a flexible system for running and monitoring multiple scripts with configurable restart policies, timeouts, and logging. It provides a simple way to orchestrate tasks and manage their lifecycle.

## Features

### Implemented
- ✅ Task orchestration with configurable restart policies
- ✅ Automatic task monitoring and recovery
- ✅ Flexible timeout management
- ✅ Comprehensive logging support
- ✅ Graceful shutdown handling (SIGTERM/SIGINT)
- ✅ Process group management
- ✅ Stdout/stderr redirection
- ✅ Timer-based execution (timer) - runs task at fixed intervals
- ✅ Cron-based scheduling (schedule-cron) - runs task on cron schedule (requires croniter)
- ✅ Custom success codes (success-codes) - define which exit codes are considered successful
- ✅ Failure notifications (notify) - send alerts on task failure via mail command
- ✅ Working directory support (working-directory)
- ✅ Timeout handling (timeout) - with flexible time units (s/m/h)
- ✅ Attempt limiting (times) - limit number of execution attempts
- ✅ Restart on failure (on-fail) - configurable failure recovery

### Partially Implemented
- ⚠️ Smart script detection (no-interface) - shell commands work, AbstractTask pending

### NOT Implemented (See [NOT_IMPLEMENTED.md](doc/NOT_IMPLEMENTED.md))
- ❌ Task dependencies (depends-on) - wait for other tasks to complete
- ❌ User switching (user) - run task as different user
- ❌ Process priority (priority/nice) - set process priority
- ❌ Environment file loading (environment-file) - load env vars from file
- ❌ AbstractTask interface for Python scripts - smart script execution
- ❌ Hot reload / change detection - restart tasks on config changes

## Installation

### From PyPI (once published)

```bash
pip install bansuri
```

### From source

```bash
git clone https://github.com/aziabatz/bansuri.git
cd bansuri
pip install -e .
```

## Quick Start

1. Create a configuration file `scripts.json`:

```json
{
  "version": "1.0",
  "scripts": [
    {
      "name": "example-task",
      "command": "python my_script.py",
      "working-directory": "/path/to/workdir",
      "timeout": "5m",
      "on-fail": "restart",
      "times": 3
    }
  ]
}
```

2. Run the orchestrator:

```bash
bansuri
```

## Configuration

### Script Configuration Options

- `name`: Unique identifier for the task
- `command`: Command to execute
- `working-directory`: Working directory for the task (optional)
- `timeout`: Maximum execution time (e.g., "30s", "5m", "1h")
- `on-fail`: Action on failure - "stop" or "restart"
- `times`: Number of execution attempts (default: 1)
- `schedule-cron`: Cron expression for scheduling
- `depends-on`: List of task dependencies
- `stdout`: File path for stdout redirection
- `stderr`: File path for stderr redirection or "combined"

See `help.py` for full details on configuration.

## Usage as Library

```python
from bansuri import TaskRunner, BansuriConfig, ScriptConfig

# Load configuration
config = BansuriConfig.load_from_file("scripts.json")

# Create and start a task runner
runner = TaskRunner(config.scripts[0])
runner.start()

# Stop the runner
runner.stop()
```

## Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
black .
```

## License

BSD v3 License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.