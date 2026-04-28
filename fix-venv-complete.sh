#!/bin/bash
# Complete fix for PsyFind virtual environment

set -e

APP_DIR="/opt/psyfind"
APP_USER="psyfind"
SERVICE_NAME="psyfind"

echo "🔧 PsyFind Complete Venv Fix"
echo "============================="

if [[ $EUID -ne 0 ]]; then
    echo "❌ Must run as root: sudo ./fix-venv-complete.sh"
    exit 1
fi

# Stop service first
echo "🛑 Stopping service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

echo ""
echo "🗑️  Removing corrupted virtual environment..."
rm -rf "$APP_DIR/venv"
echo "✅ Old venv removed"

echo ""
echo "🐍 Creating new virtual environment..."
cd "$APP_DIR"

# Install python3-venv if missing
if ! dpkg -l | grep -q python3.*-venv; then
    echo "📦 Installing python3-venv..."
    apt-get update -qq
    apt-get install -y -qq python3-venv python3-full
fi

# Create venv as root, then chown
python3 -m venv venv
chown -R "$APP_USER:$APP_USER" venv
echo "✅ Virtual environment created"

echo ""
echo "📦 Installing dependencies..."

# Install as app user using full paths
sudo -u "$APP_USER" bash << 'EOF'
set -e
APP_DIR="/opt/psyfind"
cd "$APP_DIR"

# Use full paths to avoid activation issues
VENV_PYTHON="$APP_DIR/venv/bin/python"
VENV_PIP="$APP_DIR/venv/bin/pip"

# Upgrade pip
"$VENV_PIP" install --upgrade pip

# Install requirements
"$VENV_PIP" install -r requirements.txt

# Install gunicorn
"$VENV_PIP" install gunicorn

echo ""
echo "📋 Verifying installations:"
"$VENV_PIP" list | grep -iE "(flask|gunicorn|requests|dotenv)" || true
EOF

# Verify gunicorn
if [ -f "$APP_DIR/venv/bin/gunicorn" ]; then
    echo ""
    echo "✅ Gunicorn installed at: $APP_DIR/venv/bin/gunicorn"
    "$APP_DIR/venv/bin/gunicorn" --version
else
    echo ""
    echo "❌ Gunicorn still not found"
    exit 1
fi

# Fix all permissions
echo ""
echo "🔧 Fixing permissions..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env.production"

# Verify the app can start (test import)
echo ""
echo "🧪 Testing application import..."
if sudo -u "$APP_USER" "$APP_DIR/venv/bin/python" -c "import app; print('App imports OK')" 2>&1; then
    echo "✅ Application imports successfully"
else
    echo "⚠️  Application import test failed - may have missing dependencies"
fi

echo ""
echo "🔄 Reloading systemd..."
systemctl daemon-reload

echo "🚀 Starting service..."
if systemctl start "$SERVICE_NAME"; then
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo ""
        echo "✅✅✅ SUCCESS! Service is running!"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        echo "⚠️  Service started but not active"
        journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    fi
else
    echo ""
    echo "❌ Service failed to start"
    echo ""
    echo "📋 Last 20 log lines:"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    
    echo ""
    echo "🔍 Manual test command:"
    echo "  sudo -u psyfind bash -c 'cd /opt/psyfind && ./venv/bin/python -c \"import app\"'"
fi

echo ""
echo "📝 Commands:"
echo "  Status:   sudo systemctl status psyfind"
echo "  Logs:     sudo journalctl -u psyfind -f"
echo "  Restart:  sudo systemctl restart psyfind"
