import argparse
import os
import sys
import time
import signal
import json
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError

from yasinfeed.config import load_config

PID_FILE = "yasinfeed.pid"


def is_pid_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_stored_pid() -> int:
    """Retrieve PID from the pid file if it exists and is valid."""
    if not os.path.exists(PID_FILE):
        return 0
    try:
        with open(PID_FILE, "r") as f:
            pid_str = f.read().strip()
            if pid_str.isdigit():
                return int(pid_str)
    except Exception:
        pass
    return 0


def mask_sensitive_data(data):
    """Recursively mask sensitive values in the configuration."""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(secret_term in k_lower for secret_term in ["key", "secret", "password", "token"]):
                if isinstance(v, str) and v:
                    masked[k] = "********"
                else:
                    masked[k] = v
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def handle_status(args):
    """Show the current status of the YasinFeed engine."""
    config = load_config(args.config)
    api_config = config.get("api", {})
    host = api_config.get("host", "127.0.0.1")
    port = api_config.get("port", 8000)

    # If host is 0.0.0.0, use 127.0.0.1 for local health check
    local_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{local_host}:{port}/api/health"

    # Try calling API first
    api_success = False
    health_data = {}
    try:
        req = Request(url, headers={"User-Agent": "YasinFeed-CLI"})
        with urlopen(req, timeout=1.5) as response:
            if response.status == 200:
                health_data = json.loads(response.read().decode("utf-8"))
                api_success = True
    except Exception:
        # Fallback to general health if api/health is not available
        url_fallback = f"http://{local_host}:{port}/health"
        try:
            req = Request(url_fallback, headers={"User-Agent": "YasinFeed-CLI"})
            with urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    health_data = json.loads(response.read().decode("utf-8"))
                    api_success = True
        except Exception:
            pass

    pid = get_stored_pid()
    pid_alive = is_pid_running(pid) if pid > 0 else False

    if api_success:
        print("YasinFeed Engine status: RUNNING (API is active)")
        # Show PID from health data or local PID file
        system_pid = health_data.get("system", {}).get("pid", pid)
        print(f"PID: {system_pid}")

        # Calculate uptime
        uptime = health_data.get("system", {}).get("uptime_seconds", 0)
        if uptime:
            print(f"Uptime: {int(uptime)} seconds")
        else:
            print("Uptime: N/A")

        print("\nRunning Modules & Health:")
        checks = health_data.get("checks", {})
        if checks:
            for module_name, detail in checks.items():
                status_str = detail.get("status", "unknown").upper()
                message = detail.get("message", "")
                print(f"  - {module_name}: {status_str} ({message})")
        else:
            print("  No active module health details reported.")

        metrics = health_data.get("metrics", {})
        if metrics:
            print("\nMetrics:")
            for m_key, m_val in metrics.items():
                print(f"  - {m_key}: {m_val}")
    else:
        if pid_alive:
            print(f"YasinFeed Engine status: RUNNING (PID: {pid}, but API is unresponsive)")
        else:
            print("YasinFeed Engine status: STOPPED")


def handle_start(args):
    """Start the YasinFeed engine in the background."""
    config = load_config(args.config)
    api_config = config.get("api", {})
    host = api_config.get("host", "127.0.0.1")
    port = api_config.get("port", 8000)

    pid = get_stored_pid()
    if pid > 0 and is_pid_running(pid):
        print(f"YasinFeed Engine is already running (PID: {pid}).")
        return

    print("Starting YasinFeed Engine...")
    env = os.environ.copy()
    if args.config:
        env["YASINFEED_CONFIG_PATH"] = args.config

    # Start engine process in the background
    try:
        # We start the engine as a separate process group on non-Windows to fully detach it
        preexec = None if sys.platform == "win32" else os.setpgrp
        proc = subprocess.Popen(
            [sys.executable, "-m", "yasinfeed.main"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=preexec
        )

        # Write PID file immediately
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))

        print(f"Engine process spawned with PID {proc.pid}.")

        # Wait a bit to ensure it is running and check API
        print("Waiting for engine to initialize...")
        local_host = "127.0.0.1" if host == "0.0.0.0" else host
        url = f"http://{local_host}:{port}/api/health"

        started = False
        for _ in range(10):
            time.sleep(0.5)
            if not is_pid_running(proc.pid):
                print("Error: Engine exited prematurely. Check yasinfeed.log for details.")
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                return

            try:
                with urlopen(url, timeout=0.5) as r:
                    if r.status == 200:
                        started = True
                        break
            except Exception:
                pass

        if started:
            print(f"YasinFeed Engine started successfully (PID: {proc.pid}).")
        else:
            print(f"YasinFeed Engine is running in the background (PID: {proc.pid}), but API is still starting up.")

    except Exception as e:
        print(f"Failed to start YasinFeed Engine: {e}")


def handle_stop(args):
    """Safely stop the YasinFeed engine."""
    pid = get_stored_pid()
    if pid <= 0 or not is_pid_running(pid):
        print("YasinFeed Engine is not running.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return

    print(f"Stopping YasinFeed Engine safely (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)

        # Wait for termination
        stopped = False
        for _ in range(50):
            time.sleep(0.1)
            if not is_pid_running(pid):
                stopped = True
                break

        if not stopped:
            print("Engine did not stop with SIGTERM. Sending SIGKILL...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)

        print("YasinFeed Engine stopped cleanly.")
    except Exception as e:
        print(f"Error stopping engine: {e}")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)


def handle_restart(args):
    """Restart the YasinFeed engine."""
    print("Restarting YasinFeed Engine...")
    handle_stop(args)
    time.sleep(1)
    handle_start(args)


def handle_doctor(args):
    """Check the health of the installation, configuration, storage, and dependencies."""
    print("==================================================")
    print("           YasinFeed Doctor Diagnostic            ")
    print("==================================================")

    # 1. Check Python version
    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 8
    py_status = "[ OK ]" if py_ok else "[ FAIL ]"
    print(f"{py_status} Python Version: {sys.version.split()[0]} (>= 3.8 required)")

    # 2. Check required dependencies
    dep_ok = True
    deps = {
        "yaml": "PyYAML",
        "feedparser": "feedparser",
        "sqlite3": "sqlite3"
    }
    print("\nRequired Dependencies:")
    for mod_name, pkg_name in deps.items():
        try:
            __import__(mod_name)
            print(f"  - {mod_name}: [ OK ]")
        except ImportError:
            print(f"  - {mod_name}: [ FAIL ] ({pkg_name} is missing)")
            dep_ok = False

    # 3. Check configuration availability
    config_ok = False
    config = None
    config_path = args.config or os.environ.get("YASINFEED_CONFIG_PATH", "config/config.yaml")
    print(f"\nConfiguration Availability:")
    if os.path.exists(config_path):
        try:
            config = load_config(args.config)
            print(f"  - Config file found at: {config_path} [ OK ]")
            config_ok = True
        except Exception as e:
            print(f"  - Failed to load config: {e} [ FAIL ]")
    else:
        print(f"  - Config file not found at: {config_path} [ WARNING ] (falling back to defaults)")
        try:
            config = load_config(args.config)
            config_ok = True
        except Exception as e:
            print(f"  - Failed to load default fallback config: {e} [ FAIL ]")

    # 4. Check storage/database status
    storage_ok = False
    print(f"\nStorage/Database Status:")
    if config:
        storage_config = config.get("storage", {})
        storage_type = storage_config.get("type", "sqlite")
        storage_path = storage_config.get("path", "data/yasinfeed.db")
        print(f"  - Type: {storage_type}")
        print(f"  - Path: {storage_path}")

        try:
            if storage_type == "sqlite":
                # Ensure the parent directory exists
                parent_dir = os.path.dirname(storage_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)

                # Test connection directly using sqlite3
                import sqlite3
                conn = sqlite3.connect(storage_path)
                conn.close()
                print("  - Connection Test: [ OK ]")
                storage_ok = True
            elif storage_type == "json":
                parent_dir = os.path.dirname(storage_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                # Check write permissions
                test_file = f"{storage_path}.tmp"
                with open(test_file, "w") as f:
                    f.write("{}")
                os.remove(test_file)
                print("  - Write Permission Test: [ OK ]")
                storage_ok = True
            else:
                print(f"  - Unknown storage type '{storage_type}': [ FAIL ]")
        except Exception as e:
            print(f"  - Database Check: {e} [ FAIL ]")
    else:
        print("  - Storage check skipped (config loaded unsuccessfully)")

    print("\n--------------------------------------------------")
    overall = py_ok and dep_ok and config_ok and storage_ok
    if overall:
        print("Overall Health: HEALTHY [ OK ]")
    else:
        print("Overall Health: ISSUES DETECTED [ FAIL ]")
    print("==================================================")


def handle_config(args):
    """Display the current configuration information (with secrets masked)."""
    config = load_config(args.config)
    masked_config = mask_sensitive_data(config)
    print(json.dumps(masked_config, indent=2))


def handle_version(args):
    """Display CLI and Engine version."""
    print("YasinFeed CLI v0.1")
    print("YasinFeed Engine v0.1.0")


def main():
    parser = argparse.ArgumentParser(
        prog="yasinfeed",
        description="YasinFeed Official Command Line Interface"
    )

    parser.add_argument(
        "-c", "--config",
        help="Path to the configuration file",
        default=None
    )

    subparsers = parser.add_subparsers(dest="command", title="Commands")

    # Engine Status
    subparsers.add_parser("status", help="Show current engine status")

    # Engine Management
    subparsers.add_parser("start", help="Start YasinFeed engine")
    subparsers.add_parser("stop", help="Stop YasinFeed engine safely")
    subparsers.add_parser("restart", help="Restart engine")

    # Diagnostics
    subparsers.add_parser("doctor", help="Check installation health & diagnostics")

    # Configuration
    subparsers.add_parser("config", help="Display current configuration with secrets masked")

    # Version
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    # Default command is status
    cmd = args.command or "status"

    if cmd == "status":
        handle_status(args)
    elif cmd == "start":
        handle_start(args)
    elif cmd == "stop":
        handle_stop(args)
    elif cmd == "restart":
        handle_restart(args)
    elif cmd == "doctor":
        handle_doctor(args)
    elif cmd == "config":
        handle_config(args)
    elif cmd == "version":
        handle_version(args)


if __name__ == "__main__":
    main()
