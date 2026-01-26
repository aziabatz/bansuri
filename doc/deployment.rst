Deployment Guide
================

This guide covers deployment strategies for production use of Bansuri.

Systemd Service Setup
---------------------

Running as a Systemd Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a systemd unit file at ``/etc/systemd/system/bansuri.service``:

.. code-block:: ini

    [Unit]
    Description=Bansuri Task Orchestrator
    After=network.target
    Wants=network-online.target

    [Service]
    Type=simple
    User=bansuri
    Group=bansuri
    WorkingDirectory=/opt/bansuri
    ExecStart=/opt/bansuri/venv/bin/python -m bansuri
    
    # Restart policy
    Restart=on-failure
    RestartSec=10
    
    # Resource limits
    MemoryLimit=1G
    CPUQuota=80%
    
    # Logging
    StandardOutput=journal
    StandardError=journal
    SyslogIdentifier=bansuri
    
    # Environment
    Environment="BANSURI_ENV=production"
    Environment="BANSURI_LOG_LEVEL=INFO"

    [Install]
    WantedBy=multi-user.target

Enable and start the service:

.. code-block:: bash

    sudo systemctl daemon-reload
    sudo systemctl enable bansuri
    sudo systemctl start bansuri
    sudo systemctl status bansuri

View logs:

.. code-block:: bash

    journalctl -u bansuri -f

Docker Deployment
-----------------

Dockerfile
~~~~~~~~~~

.. code-block:: dockerfile

    FROM python:3.11-slim

    # Create bansuri user
    RUN useradd -m -u 1000 bansuri

    # Install dependencies
    RUN apt-get update && apt-get install -y \
        git \
        curl \
        && rm -rf /var/lib/apt/lists/*

    # Install Bansuri
    RUN mkdir -p /opt/bansuri && chown bansuri:bansuri /opt/bansuri
    WORKDIR /opt/bansuri

    COPY --chown=bansuri:bansuri . .
    RUN pip install --no-cache-dir -e .

    # Create log directory
    RUN mkdir -p /var/log/bansuri && chown bansuri:bansuri /var/log/bansuri

    USER bansuri

    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD python -c "import sys; sys.exit(0)" || exit 1

    CMD ["python", "-m", "bansuri"]

Docker Compose
~~~~~~~~~~~~~~

.. code-block:: yaml

    version: '3.8'

    services:
      bansuri:
        build: .
        container_name: bansuri
        user: bansuri
        volumes:
          - ./scripts.json:/opt/bansuri/scripts.json:ro
          - ./logs:/var/log/bansuri
          - /var/run/docker.sock:/var/run/docker.sock:ro
        environment:
          - BANSURI_ENV=production
          - BANSURI_LOG_LEVEL=INFO
        restart: unless-stopped
        logging:
          driver: "json-file"
          options:
            max-size: "10m"
            max-file: "3"

Kubernetes Deployment
---------------------

ConfigMap for Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: bansuri-config
      namespace: default
    data:
      scripts.json: |
        {
          "version": "1.0",
          "notify_command": "curl -X POST https://alerts.example.com/notify",
          "scripts": [
            {
              "name": "health-check",
              "command": "/usr/local/bin/health-check.sh",
              "timer": "60",
              "timeout": "30s"
            }
          ]
        }

Deployment
~~~~~~~~~~

.. code-block:: yaml

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: bansuri
      namespace: default
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: bansuri
      template:
        metadata:
          labels:
            app: bansuri
        spec:
          containers:
          - name: bansuri
            image: myregistry.azurecr.io/bansuri:latest
            imagePullPolicy: Always
            resources:
              limits:
                memory: "1Gi"
                cpu: "500m"
              requests:
                memory: "512Mi"
                cpu: "250m"
            env:
            - name: BANSURI_ENV
              value: "production"
            - name: BANSURI_LOG_LEVEL
              value: "INFO"
            volumeMounts:
            - name: config
              mountPath: /opt/bansuri/scripts.json
              subPath: scripts.json
            - name: logs
              mountPath: /var/log/bansuri
            livenessProbe:
              exec:
                command:
                - python
                - -c
                - "import sys; sys.exit(0)"
              initialDelaySeconds: 30
              periodSeconds: 10
          volumes:
          - name: config
            configMap:
              name: bansuri-config
          - name: logs
            emptyDir: {}
          serviceAccountName: bansuri

ServiceAccount
~~~~~~~~~~~~~~

.. code-block:: yaml

    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: bansuri
      namespace: default

Production Checklist
--------------------

Before deploying to production, verify:

**Configuration**

- ☐ All task commands are absolute paths
- ☐ Working directories are correctly specified
- ☐ Timeouts are realistic for your infrastructure
- ☐ Notification endpoints are configured and tested
- ☐ Log directories exist and are writable

**Security**

- ☐ Run as non-root user
- ☐ Use restrictive file permissions (600-755)
- ☐ Verify all scripts are from trusted sources
- ☐ Use secrets management for credentials
- ☐ Enable audit logging

**Monitoring**

- ☐ Set up log aggregation (ELK, Splunk, etc.)
- ☐ Configure alerting for task failures
- ☐ Monitor system resources (CPU, memory, disk)
- ☐ Set up health checks for Bansuri itself
- ☐ Create dashboards for task execution metrics

**Resilience**

- ☐ Test failure scenarios (network, timeout, out of memory)
- ☐ Verify restart policies
- ☐ Test graceful shutdown (SIGTERM handling)
- ☐ Ensure log rotation is working
- ☐ Validate recovery time objectives

**Documentation**

- ☐ Document all tasks and their purpose
- ☐ Document task dependencies
- ☐ Maintain runbooks for common issues
- ☐ Document escalation procedures
- ☐ Keep version history of configurations

Backup and Recovery
-------------------

Configuration Backup
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Backup scripts.json with timestamp
    cp scripts.json "scripts.json.backup.$(date +%Y%m%d_%H%M%S)"

    # Keep last 30 days of backups
    find . -name "scripts.json.backup.*" -mtime +30 -delete

Log Backup
~~~~~~~~~~

.. code-block:: bash

    # Archive logs older than 7 days
    find /var/log/bansuri -name "*.log" -mtime +7 -exec gzip {} \;
    find /var/log/bansuri -name "*.log.gz" -mtime +30 -delete

Recovery Procedure
~~~~~~~~~~~~~~~~~~

1. Stop Bansuri: ``systemctl stop bansuri``
2. Restore configuration: ``cp scripts.json.backup.* scripts.json``
3. Verify configuration: ``python -c "from bansuri.base.config_manager import BansuriConfig; BansuriConfig.load_from_file('scripts.json')"`
4. Start Bansuri: ``systemctl start bansuri``
5. Verify status: ``systemctl status bansuri``

Scaling Considerations
----------------------

Single Instance
~~~~~~~~~~~~~~~

- Suitable for < 100 concurrent tasks
- Sufficient for < 1000 events per minute
- Simple deployment and management

Multiple Instances
~~~~~~~~~~~~~~~~~~

For larger deployments:

1. **Task Distribution**: Partition tasks across instances
2. **Configuration Sync**: Use centralized config storage (Git, S3, etc.)
3. **Log Aggregation**: Send logs to centralized location
4. **Health Monitoring**: Monitor all instances

Example multi-instance setup:

.. code-block:: bash

    # Instance 1: High-priority critical tasks
    bansuri --config scripts-critical.json

    # Instance 2: Background/batch tasks
    bansuri --config scripts-batch.json

    # Instance 3: Monitoring/health-check tasks
    bansuri --config scripts-monitoring.json

Performance Tuning
------------------

Memory Management
~~~~~~~~~~~~~~~~~

Monitor memory usage:

.. code-block:: bash

    # Monitor Bansuri process
    watch -n 1 'ps aux | grep bansuri'

Set limits in systemd:

.. code-block:: ini

    [Service]
    MemoryLimit=2G
    MemoryAccounting=yes

CPU Affinity
~~~~~~~~~~~~

Bind Bansuri to specific CPU cores:

.. code-block:: ini

    [Service]
    CPUAffinity=0-3

For systemd systems with taskset:

.. code-block:: bash

    taskset -cp 0-3 $(pgrep -f "python -m bansuri")

Troubleshooting Deployment Issues
---------------------------------

Service won't start
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Check syntax
    systemctl status bansuri
    journalctl -u bansuri -n 50

    # Verify permissions
    ls -la /opt/bansuri
    sudo -u bansuri python -m bansuri --help

High memory usage
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Check for zombie processes
    ps aux | grep defunct

    # Monitor task output
    tail -f /var/log/bansuri/task.log

    # Reduce concurrency
    # Modify scripts.json to reduce number of concurrent tasks

Tasks not running
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Verify configuration
    python -m bansuri --validate-config

    # Check file permissions on log directories
    ls -la /var/log/bansuri

    # Check if user has execute permissions
    sudo -u bansuri which /path/to/command
