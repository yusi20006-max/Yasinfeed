#!/bin/sh
# YasinFeed Installation & Setup Script
# Highly compatible with both Linux systems and Termux on Android.

set -e

echo "=================================================="
echo "          YasinFeed Installer & Setup             "
echo "=================================================="

# 1. Detect operating system / shell context
IS_TERMUX=0
if [ -d "/data/data/com.termux/files/usr/bin" ] || [ -n "$TERMUX_VERSION" ]; then
    echo "[*] Termux environment detected."
    IS_TERMUX=1
else
    echo "[*] Standard Linux environment detected."
fi

# 2. Check Python Version (minimum 3.8)
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 command not found. Please install python3 first."
    exit 1
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "[ERROR] Python 3.8+ is required. Detected version: $PYTHON_VER"
    exit 1
fi
echo "[OK] Python version: $PYTHON_VER"

# 3. Create standard directories
echo "[*] Setting up directories..."
mkdir -p data logs config
echo "[OK] Directories 'data', 'logs', 'config' are ready."

# 4. Generate default config/config.yaml if not present
CONFIG_FILE="config/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[*] Initializing default configuration..."
    cat <<EOF > "$CONFIG_FILE"
# YasinFeed Production Configuration
app:
  env: "production"
  name: "YasinFeed"

logging:
  level: "INFO"
  file_path: "logs/yasinfeed.log"
  console: true

api:
  host: "127.0.0.1"
  port: 8000

fetch:
  interval_seconds: 300

rewrite:
  provider: "dummy"
  openai:
    api_key: null
    base_url: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"
    temperature: 0.7
  huggingface:
    api_key: null
    model: "meta-llama/Llama-3-8b-instruct"

storage:
  type: "sqlite"
  path: "data/yasinfeed.db"

scheduler:
  enabled: true

publisher:
  eitaa:
    enabled: false
  pwa:
    enabled: false
  rss:
    enabled: false
EOF
    echo "[OK] Default configuration created at $CONFIG_FILE."
else
    echo "[*] Configuration file $CONFIG_FILE already exists, keeping it."
fi

# 5. Virtual Environment Setup (Recommended for standard Linux, optional/skip for Termux based on user environments)
if [ "$IS_TERMUX" -eq 1 ]; then
    echo "[*] Termux detects system-level execution. Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .[dev]
else
    if [ ! -d "venv" ]; then
        echo "[*] Creating virtual environment (venv)..."
        python3 -m venv venv
        echo "[OK] Virtual environment created."
    fi
    echo "[*] Activating virtual environment and installing dependencies..."
    . venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .[dev]
fi

echo "[OK] Dependencies successfully installed!"

echo "--------------------------------------------------"
echo "Setup is complete! You can run diagnostics with:"
if [ "$IS_TERMUX" -eq 1 ]; then
    echo "  python -m yasinfeed.cli.main doctor"
else
    echo "  ./venv/bin/python -m yasinfeed.cli.main doctor"
fi
echo "=================================================="
