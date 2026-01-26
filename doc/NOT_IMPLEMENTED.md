# Feature Status Reference

Quick implementation status for all Bansuri features with examples.

## Status Summary

| Status | Count | Features |
|--------|-------|----------|
| Implemented | 9 | schedule-cron, timer, timeout, on-fail, times, success-codes, notify, stdout/stderr, working-directory |
| Partial | 1 | no-interface (shell works, AbstractTask pending) |
| Not Implemented | 5 | depends-on, user, priority, environment-file, hot-reload |

## Implemented Features (9)

### 1. Timer-Based Scheduling
**Field**: `timer`  
**Example**: `"30s"`, `"5m"`, `"1h"`

Runs task repeatedly at fixed intervals.

```json
{
  "name": "worker",
  "command": "python worker.py",
  "timer": "5m"
}
```

---

### 2. Cron-Based Scheduling ✅
**Field**: `schedule-cron`  
**Example**: `"*/5 * * * *"`

Runs task on cron schedule (requires `pip install croniter`).

```json
{
  "name": "backup",
  "command": "bash backup.sh",
  "schedule-cron": "0 2 * * *"
}
```

---

### 3. Timeout Management ✅
**Field**: `timeout`  
**Example**: `"30s"`, `"5m"`, `"1h"`

Kills task if it runs too long.

```json
{
  "name": "api-call",
  "command": "python api.py",
  "timeout": "30s"
}
```

---

### 4. Restart on Failure ✅
**Field**: `on-fail`  
**Values**: `"stop"` (default), `"restart"`

Action to take when task fails.

```json
{
  "name": "sync",
  "command": "python sync.py",
  "on-fail": "restart",
  "times": 3
}
```

---

### 5. Attempt Limiting ✅
**Field**: `times`  
**Example**: `3`

Max number of execution attempts.

```json
{
  "name": "upload",
  "command": "python upload.py",
  "times": 3,
  "on-fail": "restart"
}
```

---

### 6. Custom Success Codes ✅
**Field**: `success-codes`  
**Default**: `[0]`

Exit codes to treat as success (won't trigger notifications/retries).

```json
{
  "name": "check",
  "command": "bash check.sh",
  "success-codes": [0, 1, 2]
}
```

---

### 7. Notifications ✅
**Field**: `notify`  
**Value**: `"mail"` or `"none"`

Send email alerts on task failure.

**Global Config**:
```json
{
  "version": "1.0",
  "notify_command": "mail -s 'Alert: {task}' admin@example.com",
  "scripts": [...]
}
```

**Task Config**:
```json
{
  "name": "critical",
  "command": "python critical.py",
  "notify": "mail"
}
```

---

### 8. File Redirection ✅
**Fields**: `stdout`, `stderr`  
**Values**: file path or `"combined"`

Redirect output to files.

```json
{
  "name": "logger",
  "command": "python log.py",
  "stdout": "output.log",
  "stderr": "combined"
}
```

---

### 9. Working Directory ✅
**Field**: `working-directory`  
**Example**: `/path/to/workdir`

Set task execution directory.

```json
{
  "name": "worker",
  "command": "python main.py",
  "working-directory": "/app/scripts"
}
```

### No-Interface: Shell Command Execution ⚠️
**Field**: `no-interface`  
**Status**: Shell ✅ | AbstractTask ❌

**Shell Commands Work**:
```json
{
  "name": "ls-task",
  "command": "ls -la /tmp",
  "no-interface": true
}
```

**AbstractTask Import NOT YET** (falls back to shell):
```json
{
  "name": "python-task",
  "command": "python my_script.py",
  "no-interface": false
}
```
*Note: Currently runs as shell command, not smart Python task*

---

## ❌ NOT Implemented (5)

### 1. Task Dependencies ❌
**Field**: `depends-on`

Wait for other tasks to complete before starting.

```json
{
  "name": "task-b",
  "command": "python task_b.py",
  "depends-on": ["task-a"],
  "timer": "1h"
}
```

**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Run tasks in separate orchestrator or use external scheduler

---

### 2. User Switching ❌
**Field**: `user`

Run task as different Unix user.

```json
{
  "name": "db-task",
  "command": "python db.py",
  "user": "postgres"
}
```

**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Use `sudo -u postgres` in command, or adjust file permissions

---

### 3. Process Priority ❌
**Field**: `priority`

Set process nice value (-20 to 19).

```json
{
  "name": "background",
  "command": "python heavy.py",
  "priority": 10
}
```

**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Use `nice -n 10` in command

---

### 4. Environment File Loading ❌
**Field**: `environment-file`

Load environment variables from JSON/YAML file.

```json
{
  "name": "api-task",
  "command": "python api.py",
  "environment-file": "/etc/bansuri/env.json"
}
```

**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Export ENV vars before running or use wrapper script

---

### 5. Hot Reload on Config Change ❌

Automatically restart tasks when config changes.

**Current Behavior**: Adds new tasks, removes deleted ones, but doesn't restart changed tasks  
**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Manually restart Bansuri or use `SIGHUP` signal handler

---

## Common Use Cases & Status

### Use Case 1: Repeat Every N Minutes
```json
{
  "name": "worker",
  "command": "python worker.py",
  "timer": "5m",
  "timeout": "4m30s"
}
```
**Status**: ✅ Works perfectly

---

### Use Case 2: Run at Specific Times (Cron)
```json
{
  "name": "daily-sync",
  "command": "bash sync.sh",
  "schedule-cron": "0 9,17 * * *"
}
```
**Status**: ✅ Works (requires `croniter`)

---

### Use Case 3: Retry Failed Task
```json
{
  "name": "api-sync",
  "command": "curl https://api.example.com/sync",
  "on-fail": "restart",
  "times": 3,
  "timeout": "30s"
}
```
**Status**: ✅ Works perfectly

---

### Use Case 4: Custom Success Codes
```json
{
  "name": "backup-check",
  "command": "python check_backup.py",
  "success-codes": [0, 1]
}
```
**Status**: ✅ Works (exit code 1 won't trigger notifications)

---

### Use Case 5: Send Alert on Failure
```json
{
  "version": "1.0",
  "notify_command": "mail -s 'Bansuri: {task} FAILED' admin@example.com",
  "scripts": [{
    "name": "critical",
    "command": "python critical.py",
    "notify": "mail",
    "timer": "1h"
  }]
}
```
**Status**: ✅ Works (mail command required)

---

### Use Case 6: Run Task as Different User
```json
{
  "name": "db-maintenance",
  "command": "python maintenance.py",
  "user": "postgres"
}
```
**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Use `sudo -u postgres` or adjust permissions

---

### Use Case 7: Wait for Task A Before Running Task B
```json
{
  "name": "task-a",
  "command": "python download.py",
  "timer": "1h"
}
{
  "name": "task-b",
  "command": "python process.py",
  "depends-on": ["task-a"]
}
```
**Status**: ❌ NOT IMPLEMENTED  
**Workaround**: Use external scheduler or separate orchestrator

---

## Installation Requirements

### Core
- Python 3.7+
- `subprocess`, `threading`, `signal` (standard library)

### Optional Features
- **Cron Scheduling**: `pip install croniter`
- **Notifications**: System `mail` command
- **AbstractTask**: Python module with class extending `AbstractTask`

---

## Troubleshooting

### "croniter not found" Error
```
ERROR: 'croniter' library is missing
```
**Fix**: `pip install croniter`

### Notifications Not Sending
```
[task] Notify is 'mail' but no notify_command configured
```
**Fix**: Add `notify_command` to scripts.json global config

### Task Not Running
Check:
1. Config syntax is valid JSON
2. `timer` or `schedule-cron` is set
3. No unsupported features blocking task start