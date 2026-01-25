# Suggested JSON Configuration Fields

Based on analysis of the current Bansuri configuration, here are recommended fields to enhance functionality:

## Current Fields (Existing)
```json
{
  "name": "task-name",
  "command": "script.sh",
  "user": "username",
  "working_directory": "/path",
  "timer": "300",
  "schedule-cron": "0 2 * * *",
  "timeout": "30s",
  "times": 3,
  "on-fail": "restart",
  "depends-on": ["task1", "task2"],
  "success-codes": [0, 1, 2],
  "environment-file": "/path/to/.env",
  "priority": 1,
  "stdout": "file.log",
  "stderr": "combined",
  "notify": "mail"
}
```

## ✅ NEW RECOMMENDED FIELDS

### 1. **Task Metadata & Grouping**
```json
{
  "description": "Brief task description",
  "group": "backups",
  "tags": ["critical", "database", "daily"],
  "owner": "team@example.com"
}
```
**Benefits:**
- Better organization and documentation
- Easier filtering and searching
- Track responsibility

### 2. **Advanced Scheduling**
```json
{
  "start_time": "2025-01-01T00:00:00",
  "end_time": "2025-12-31T23:59:59",
  "max_runs": 100,
  "skip_on_holiday": true,
  "blackout_windows": ["2025-12-24", "2025-12-25"],
  "jitter": "30s",
  "throttle_max_concurrent": 1
}
```
**Benefits:**
- Time-window restrictions
- Run limits
- Avoid busy periods
- Concurrent execution control

### 3. **Enhanced Failure Handling**
```json
{
  "retry_delay": "5m",
  "retry_backoff": "exponential",
  "max_backoff": "1h",
  "fail_on_timeout": true,
  "catch_signals": ["SIGTERM", "SIGINT"],
  "cleanup_command": "rm -f /tmp/task.lock"
}
```
**Benefits:**
- Smart retry strategies
- Backoff algorithms
- Signal handling
- Post-failure cleanup

### 4. **Resource Management**
```json
{
  "cpu_limit": "50%",
  "memory_limit": "512m",
  "disk_quota": "10g",
  "ulimit": {
    "nofile": 65536,
    "nproc": 1024
  }
}
```
**Benefits:**
- Prevent resource exhaustion
- Container-like limits
- Prevent runaway processes

### 5. **Output & Logging Enhancement**
```json
{
  "log_level": "INFO",
  "log_format": "json",
  "rotate_logs": {
    "enabled": true,
    "max_size": "100m",
    "max_age": "30d",
    "max_backups": 10,
    "compress": true
  },
  "log_retention": "90d"
}
```
**Benefits:**
- Structured logging
- Automatic log rotation
- Storage management
- Retention policies

### 6. **Notifications & Alerts**
```json
{
  "notify": {
    "on_success": "email",
    "on_failure": ["email", "slack"],
    "on_timeout": "pagerduty",
    "webhook": "https://example.com/hook",
    "channels": {
      "email": "team@example.com",
      "slack": "#alerts"
    },
    "include_output": true,
    "max_output_lines": 100
  }
}
```
**Benefits:**
- Conditional notifications
- Multiple channels
- Webhook support
- Output snippets in alerts

### 7. **Task Dependencies & Workflow**
```json
{
  "depends_on": ["task1", "task2"],
  "run_after_task": "task3",
  "parallel_with": ["task4", "task5"],
  "wait_for_completion": true,
  "propagate_failure": false
}
```
**Benefits:**
- Complex workflows
- Parallel execution
- DAG (Directed Acyclic Graph) support
- Better orchestration

### 8. **Secrets & Security**
```json
{
  "secrets": {
    "API_KEY": "vault:secrets/api",
    "DB_PASSWORD": "env:DB_PASS"
  },
  "environment_vars": {
    "NODE_ENV": "production",
    "DEBUG": "false"
  },
  "require_approval": false,
  "audit_log": true
}
```
**Benefits:**
- Secure credential handling
- Environment isolation
- Approval workflows
- Audit trails

### 9. **Performance & Monitoring**
```json
{
  "expected_duration": "5m",
  "alert_if_slower_than": "10m",
  "metrics": {
    "collect": true,
    "emit_to": "prometheus",
    "custom_metrics": ["processed_records", "errors"]
  },
  "health_check": "curl http://localhost:8000/health"
}
```
**Benefits:**
- Performance tracking
- SLA monitoring
- Health checks
- Custom metrics

### 10. **Advanced Control**
```json
{
  "enabled": true,
  "dry_run_only": false,
  "require_manual_trigger": false,
  "require_confirmation": true,
  "isolation_level": "process",
  "execution_environment": "docker:image:tag"
}
```
**Benefits:**
- Enable/disable tasks
- Manual controls
- Container isolation
- Different execution contexts

### 11. **Context & Reporting**
```json
{
  "sla": {
    "response_time": "5m",
    "resolution_time": "1h"
  },
  "incident_severity": "high",
  "runbook": "https://wiki.example.com/task-runbook",
  "related_tickets": ["JIRA-123", "JIRA-456"],
  "business_hours_only": false
}
```
**Benefits:**
- SLA tracking
- Runbook links
- Ticket integration
- Severity levels

## 📊 Complete Enhanced Example

```json
{
  "version": "2.0",
  "scripts": [
    {
      "name": "database-backup",
      "description": "Daily encrypted database backup to S3",
      "group": "backups",
      "tags": ["critical", "database", "daily"],
      "owner": "dba-team@example.com",
      
      "command": "bash /opt/backup/db.sh",
      "working_directory": "/opt/backup",
      "user": "backup-user",
      
      "schedule-cron": "0 2 * * *",
      "start_time": "2025-01-01",
      "end_time": "2026-12-31",
      "blackout_windows": ["2025-12-24", "2025-12-25"],
      "jitter": "30s",
      
      "timeout": "1h",
      "times": 3,
      "retry_delay": "5m",
      "retry_backoff": "exponential",
      "max_backoff": "1h",
      "on-fail": "restart",
      
      "success-codes": [0],
      "expected_duration": "30m",
      "alert_if_slower_than": "1h",
      "fail_on_timeout": true,
      
      "cpu_limit": "50%",
      "memory_limit": "2g",
      "disk_quota": "100g",
      
      "environment_vars": {
        "BACKUP_ENCRYPTION": "AES256",
        "S3_BUCKET": "company-backups"
      },
      "secrets": {
        "DB_PASSWORD": "vault:secrets/db",
        "AWS_ACCESS_KEY": "env:AWS_KEY"
      },
      
      "stdout": "/var/log/backup.log",
      "stderr": "combined",
      "log_level": "INFO",
      "log_format": "json",
      "rotate_logs": {
        "enabled": true,
        "max_size": "500m",
        "max_backups": 5,
        "compress": true
      },
      "log_retention": "90d",
      
      "notify": {
        "on_success": "email",
        "on_failure": ["email", "slack", "pagerduty"],
        "on_timeout": "pagerduty",
        "webhook": "https://monitoring.example.com/alert",
        "channels": {
          "email": "dba-team@example.com",
          "slack": "#database-alerts"
        },
        "include_output": true,
        "max_output_lines": 50
      },
      
      "metrics": {
        "collect": true,
        "emit_to": "prometheus",
        "custom_metrics": ["backup_size_bytes", "backup_duration_seconds"]
      },
      
      "sla": {
        "response_time": "5m",
        "resolution_time": "30m"
      },
      "incident_severity": "high",
      "runbook": "https://wiki.example.com/backup-runbook",
      "audit_log": true,
      
      "enabled": true,
      "dry_run_only": false
    }
  ]
}
```

## 🎯 Implementation Priority

### Phase 1 (High Impact, Easy to Add)
- ✅ `description`, `group`, `tags`, `owner`
- ✅ `log_level`, `log_format`
- ✅ `retry_delay`, `retry_backoff`
- ✅ `enabled`, `dry_run_only`

### Phase 2 (Medium Impact)
- 🔄 `start_time`, `end_time`, `blackout_windows`
- 🔄 Advanced `notify` structure
- 🔄 `cleanup_command`, `health_check`
- 🔄 `secrets`, `environment_vars`

### Phase 3 (Advanced Features)
- 📋 `cpu_limit`, `memory_limit`, `disk_quota`
- 📋 Log rotation with compression
- 📋 Metrics collection
- 📋 SLA tracking

## 🔄 Migration Path

Existing configs remain backward compatible:
- New fields are optional with sensible defaults
- Parser auto-detects old format vs new format
- Gradual migration possible per-task

```python
# Automatic defaults for new fields
config = {
    "name": "task",
    "command": "echo test",
    # ... minimal config ...
    
    # Auto-defaults applied:
    # "description": "No description",
    # "enabled": True,
    # "dry_run_only": False,
    # "log_level": "INFO",
    # "retry_backoff": "linear",
    # ...
}
```

---

**Total Current Fields:** 13  
**Total Recommended Fields:** 50+  
**Backward Compatible:** ✅ Yes  
**Version Bump:** 1.0 → 2.0  
