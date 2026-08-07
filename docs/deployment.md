# YasinFeed - Deployment Guide

This guide describes how to deploy YasinFeed to production, manage background processes, understand directory structures, and configure storage and security parameters for robust, continuous uptime on Linux and Termux environments.

---

## 1. Production Directory Structure

In a production deployment, the recommended layout is designed to separate application logic, configurations, stateful database storage, and transient process and log files:

```
/opt/yasinfeed/                # Root installation directory (or home/yasinfeed in Termux)
├── config/
│   └── config.yaml            # Active production config parameters
├── data/
│   └── yasinfeed.db           # Persistent SQLite Database storage file
├── logs/
│   └── yasinfeed.log          # Operational and runtime logs
├── yasinfeed/                 # Core Python engine packages & modules
│   ├── api/
│   ├── cli/
│   ├── database/
│   ├── scheduler/
│   └── ... (other module directories)
├── requirements.txt           # Python package requirements
├── yasinfeed.pid              # Dynamically created engine process ID file
└── venv/                      # Virtual environment containing dependencies
```

Ensure correct file and directory permissions exist, restricting read/write access to the specific service user:

```bash
chmod 700 /opt/yasinfeed/data
chmod 600 /opt/yasinfeed/config/config.yaml
```

---

## 2. Configuration & Storage Specifications

### Storage Requirements
YasinFeed supports two backends for persistence: SQLite and JSON flat-files.
- **SQLite Database (`sqlite`):** Highly recommended for production. It uses `yasinfeed/database/` routines to execute atomic writes and transactional operations. Ensure that the parent directory (`data/`) has write permissions.
- **JSON Storage (`json`):** Supported for low-power contexts. Writes models to flat JSON objects.

### Security Configurations
1. **API Port Binding:** In production, do not bind the API server directly to public interfaces (`0.0.0.0`) unless protected by a firewall or API gateway. Bind to localhost (`127.0.0.1`) and use a reverse proxy (like Nginx) if routing external traffic.
2. **Key Masking:** YasinFeed CLI automatically masks sensitive environment or configuration keys containing terms like `key`, `secret`, `password`, or `token` before printing or exporting configuration lists.
3. **Password Security:** The built-in authentication system (`yasinfeed/auth/`) stores user credentials securely using PBKDF2 with SHA-256 (100,000 iterations) and cryptographic salts.

---

## 3. Starting and Stopping the Service

YasinFeed processes can be daemonized and controlled using various strategies depending on your host OS.

### Method 1: Using the Built-in YasinFeed CLI

The easiest way to start, check, or stop YasinFeed in the background across both Linux and Termux:

```bash
# Start the background process (spawns sys.executable in background and writes yasinfeed.pid)
python -m yasinfeed.cli.main start

# Check background status and active modules
python -m yasinfeed.cli.main status

# Stop background process cleanly
python -m yasinfeed.cli.main stop

# Restart process
python -m yasinfeed.cli.main restart
```

### Method 2: Systemd Integration (Linux Production Standard)

For Linux systems, integrating with systemd allows automatically starting YasinFeed on boot, auto-restarting on failure, and centralizing log rotation.

Create a systemd unit file at `/etc/systemd/system/yasinfeed.service`:

```ini
[Unit]
Description=YasinFeed Core Engine
After=network.target

[Service]
Type=simple
User=yasinfeed
WorkingDirectory=/opt/yasinfeed
ExecStart=/opt/yasinfeed/venv/bin/python -m yasinfeed.main
Restart=always
RestartSec=5
Environment=YASINFEED_CONFIG_PATH=/opt/yasinfeed/config/config.yaml

[Install]
WantedBy=multi-user.target
```

Enable and manage the service:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Start the service and enable startup on boot
sudo systemctl enable --now yasinfeed

# Check status and logs
sudo systemctl status yasinfeed
journalctl -u yasinfeed -f
```

### Method 3: Termux Service Boot Integration (Android Production Standard)

In Termux on Android, background processes might be interrupted by Android's battery optimizer. Follow these steps for stable execution:

1. **Disable Battery Optimization:** In Android system settings, whitelist the Termux app from battery optimizations.
2. **Acquire Wakelock:** Open Termux and run `termux-wake-lock` to prevent the device CPU from sleeping.
3. **Use `termux-services` (Optional):** You can manage the background lifecycle using Termux service scripts.

To run with `nohup` on boot:

```bash
nohup python -m yasinfeed.main > logs/stdout.log 2>&1 &
echo $! > yasinfeed.pid
```

---

## 4. Operational Monitoring and Diagnostics

YasinFeed includes built-in diagnostics to check environmental health:

```bash
# Run doctor diagnostic checklist
python -m yasinfeed.cli.main doctor
```

The `doctor` utility validates:
- Python version requirements.
- Core package dependency availability.
- Write permissions for configured DB storage.
- Standard YAML parsing capabilities.
