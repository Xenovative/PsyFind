#!/bin/bash
# Fix script for PsyFind virtual environment and dependencies

set -e

APP_DIR="/opt/psyfind"
APP_USER="psyfind"
SERVICE_NAME="psyfind"

echo "🔧 PsyFind Virtual Environment Fix"
echo "==================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root"
    echo "Usage: sudo ./fix-venv.sh"
    exit 1
fi

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found at $APP_DIR"
    exit 1
fi

echo "📋 Checking virtual environment..."

# Check if venv exists
if [ ! -d "$APP_DIR/venv" ]; then
    echo "⚠️  Virtual environment not found"
    echo "📝 Creating virtual environment..."
    
    cd "$APP_DIR"
    sudo -u "$APP_USER" python3 -m venv venv
    
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Check if requirements.txt exists
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

echo ""
echo "📦 Installing Python dependencies..."
echo "   (This may take a few minutes)"

# Install dependencies as app user
sudo -u "$APP_USER" bash << EOF
cd "$APP_DIR"
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install gunicorn explicitly
pip install gunicorn

echo ""
echo "✅ Dependencies installed"
echo ""
echo "📋 Installed packages:"
pip list | grep -E "(flask|gunicorn|requests)" || true
EOF

# Verify gunicorn is installed
if [ -f "$APP_DIR/venv/bin/gunicorn" ]; then
    echo ""
    echo "✅ Gunicorn installed successfully"
    echo "   Path: $APP_DIR/venv/bin/gunicorn"
    
    # Show version
    "$APP_DIR/venv/bin/gunicorn" --version
else
    echo ""
    echo "❌ Gunicorn installation failed"
    exit 1
fi

# Fix ownership
echo ""
echo "🔧 Fixing file ownership..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
echo "✅ Ownership fixed"

# Reload systemd and restart service
echo ""
echo "🔄 Reloading systemd..."
systemctl daemon-reload

echo "🚀 Starting service..."
if systemctl start "$SERVICE_NAME"; then
    echo ""
    echo "✅ Service started successfully"
    
    # Wait a moment and check status
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✅ Service is running"
        echo ""
        echo "📊 Service Status:"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        echo "⚠️  Service started but not active"
    fi
else
    echo ""
    echo "❌ Service failed to start"
    echo ""
    echo "📋 Recent logs:"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    
    echo ""
    echo "🔍 Checking for common issues..."
    
    # Check if port is in use
    APP_PORT=$(grep -oP "APP_PORT=\K[0-9]+" "$APP_DIR/.env.production" 2>/dev/null || echo "5000")
    if ss -tlnp | grep -q ":$APP_PORT "; then
        echo "⚠️  Port $APP_PORT is already in use"
        ss -tlnp | grep ":$APP_PORT "
    fi
    
    # Check app.py syntax
    echo ""
    echo "🔍 Checking app.py for syntax errors..."
    if ! sudo -u "$APP_USER" "$APP_DIR/venv/bin/python3" -m py_compile "$APP_DIR/app.py" 2>&1; then
        echo "❌ Syntax errors found in app.py"
    else
        echo "✅ app.py syntax OK"
    fi
fi

echo ""
echo "📝 Useful Commands:"
echo "   Test app manually:  sudo -u psyfind bash -c 'cd $APP_DIR && source venv/bin/activate && python app.py'"
echo "   Check logs:         sudo journalctl -u psyfind -f"
echo "   Restart service:    sudo systemctl restart psyfind"
echo "   Check status:       sudo systemctl status psyfind"
echo ""
echo "✅ Fix complete!"
