# YasinFeed - Production Release & Deployment Checklist

Use this checklist to verify that a YasinFeed installation is fully configured, secured, and ready for public production deployment on Linux or Termux.

---

## 1. Environment and Prerequisites
- [ ] **Python Version Check:** Confirm Python version is `>= 3.8` by running `python --version`.
- [ ] **System Dependencies:** Core dependencies (`PyYAML`, `feedparser`) are installed in the production context.
- [ ] **Diagnostics Execution:** Running `python -m yasinfeed.cli.main doctor` yields `HEALTHY [ OK ]` across all sub-checks.
- [ ] **Virtual Environment Active:** YasinFeed is executing within an isolated virtual environment (`venv`) to prevent system namespace pollution.

---

## 2. Configuration Auditing
- [ ] **Configuration File Location:** `config/config.yaml` is populated with host-specific production values rather than standard developer defaults.
- [ ] **Sensitive Key Masking:** Run `python -m yasinfeed.cli.main config` to double-check that all passwords, secrets, tokens, and keys are successfully masked as `********` in console output.
- [ ] **Environment Overrides:** Production-specific environmental parameters (such as database paths, thread counts, or scheduling intervals) are passed via secure `YASINFEED_` system environment variables.

---

## 3. Storage & Permissions
- [ ] **Storage Backend Selection:** The `storage.type` value is set to `sqlite` for safe, transaction-protected SQL writes.
- [ ] **Write Permissions:** The user executing YasinFeed has read & write permissions to the configured DB storage folder (e.g. `data/`).
- [ ] **Schema Initialization:** The SQLite database is properly initialized and can execute standard transactional CRUD commands without errors.

---

## 4. Security & Network Isolation
- [ ] **Port Binding:** The REST API `api.host` is bound to `127.0.0.1` (localhost) rather than `0.0.0.0` (all interfaces), unless explicitly protected by a reverse proxy (like Nginx) or a packet filter (like `iptables` / `ufw`).
- [ ] **Authentication Services:** Secure user credentials persist safely. Default system credentials are changed or deactivated.
- [ ] **Credential Hashing:** User passwords have been registered using standard high-entropy cryptographically-salted PBKDF2 with SHA-256 (100,000 iterations).

---

## 5. Background Process Persistence & Monitoring
- [ ] **Daemon Management:** The service is configured to run continuously in the background:
  - **On Linux:** A systemd service configuration (`yasinfeed.service`) is registered, enabled, and started.
  - **On Termux:** Wakelock is acquired (`termux-wake-lock`) and battery optimization is disabled for Termux in Android settings.
- [ ] **PID Tracking:** The pid tracking file (`yasinfeed.pid`) is correctly written to and updated by the background process runner.
- [ ] **Log Isolation:** Log level is set to `INFO` or `WARNING` in production to prevent disk exhaustion. Standard error and output logs are routed to `logs/yasinfeed.log`.
- [ ] **API Health Endpoint Check:** Querying `/api/health` yields a `200 OK` JSON response indicating that the scheduler, database, and monitoring counters are alive and healthy.
