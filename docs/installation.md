# YasinFeed - Installation Guide

YasinFeed is designed to be lightweight, pure-Python, and zero-dependency at its core to ensure flawless out-of-the-box compatibility with both standard Linux distributions and Termux on Android. This guide covers how to prepare your environment and install YasinFeed.

---

## 1. System & Python Requirements

Before starting, ensure your system meets the minimum requirements:

- **Python Version:** `>= 3.8` (Python 3.11+ is recommended; Python 3.14 fully supported)
- **Permissions:**
  - Standard user permissions for installing dependencies and running the service.
  - Root/sudo access is **not** required, making it highly secure and easy to deploy in sandbox environments or restricted mobile terminals (Termux).

---

## 2. Platform-Specific Prerequisites

### Linux (Ubuntu, Debian, CentOS, etc.)

Update your package manager and ensure Python 3, pip, and virtual environment utilities are installed:

```bash
# Debian/Ubuntu systems
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### Termux (Android)

Termux is a terminal emulator and Linux environment for Android. Make sure Termux packages are up to date and install Python and git:

```bash
# Update Termux repository index and upgrade packages
pkg update && pkg upgrade -y

# Install Python and git
pkg install -y python git
```

---

## 3. Dependency Installation

### Step 1: Clone the Repository

Clone the YasinFeed repository to your local directory:

```bash
git clone https://github.com/yusi20006-max/Yasinfeed.git
cd Yasinfeed
```

### Step 2: Create a Virtual Environment (Recommended for Linux)

Creating a virtual environment ensures isolation from system-wide Python packages:

```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

*Note: In Termux, you can run directly inside a virtual environment or run system-wide depending on your setup.*

### Step 3: Install Required Packages

Install dependencies declared in the project's requirements:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Core Dependencies Explained:
- **PyYAML (`>= 6.0`):** Used by the configuration loader module to read YAML config files.
- **feedparser:** Used by the fetcher module to parse RSS/Atom feeds cleanly.
- **sqlite3:** (Built-in standard library) Used by the persistent database layer.

---

## 4. Configuration Setup

YasinFeed employs a multi-tiered configuration system. The configuration loads fallback defaults first, then parses a YAML file, and finally overrides with environment variables.

### YAML Configuration File

Copy the template configuration file or modify the existing file located at `config/config.yaml`:

```yaml
# config/config.yaml Example
app:
  env: "production"

api:
  host: "127.0.0.1"
  port: 8000

storage:
  type: "sqlite"               # options: "sqlite", "json"
  path: "data/yasinfeed.db"

logging:
  level: "INFO"
  path: "logs/yasinfeed.log"
```

Ensure the output log and database directories exist and are writable:

```bash
mkdir -p data logs config
```

### Environment Variables Overrides

Any configuration parameter can be overridden using environment variables prefixed with `YASINFEED_`. Use double underscores (`__`) for nested configurations:

```bash
# Override host and port
export YASINFEED_PORT=8080
export YASINFEED_HOST=0.0.0.0

# Override nested options
export YASINFEED__STORAGE__TYPE=sqlite
export YASINFEED__LOGGING__LEVEL=DEBUG
```

---

## 5. Running YasinFeed

YasinFeed provides a unified Command Line Interface (CLI) for simple daemon management and diagnostics.

### Method A: Running via CLI (Recommended)

Using the built-in CLI allows daemonizing the engine and running diagnostics easily:

```bash
# Check installation health first (YasinFeed Doctor)
python -m yasinfeed.cli.main doctor

# Start YasinFeed Engine in the background
python -m yasinfeed.cli.main start

# Check engine and active modules status
python -m yasinfeed.cli.main status

# Stop YasinFeed Engine cleanly
python -m yasinfeed.cli.main stop
```

### Method B: Direct Main Module Execution (Foreground)

To run the engine directly in your terminal foreground (useful for development and real-time debugging):

```bash
python -m yasinfeed.main
```

You can stop the foreground engine anytime using `Ctrl+C` (SIGINT), which triggers a graceful cleanup process.
