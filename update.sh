#!/bin/bash
set -euo pipefail

# Lightweight updater: sync current working tree into APP_DIR and restart service
# Defaults match deploy.sh
APP_DIR="${APP_DIR:-/opt/psyfind}"
SERVICE_NAME="${SERVICE_NAME:-psyfind}"
PYTHON_BIN="${PYTHON_BIN:-/opt/psyfind/venv/bin/python3}"
RSYNC_EXCLUDES=(".git" "__pycache__" "*.pyc" ".venv" "node_modules")

log()  { printf "[INFO] %s\n" "$*"; }
err()  { printf "[ERROR] %s\n" "$*" >&2; }
success(){ printf "[OK] %s\n" "$*"; }

if [[ ! -d "$APP_DIR" ]]; then
  err "APP_DIR '$APP_DIR' does not exist"
  exit 1
fi

# Ensure we run from repo root (has app.py or requirements.txt)
if [[ ! -f "app.py" && ! -f "requirements.txt" ]]; then
  err "Run this from the project root (app.py or requirements.txt missing)"
  exit 1
fi

# Sync code to APP_DIR, preserving venv/data
log "Syncing code to $APP_DIR"
rsync -a --delete \
  $(printf -- "--exclude=%s " "${RSYNC_EXCLUDES[@]}") \
  ./ "$APP_DIR"/

# Install dependencies if requirements present
if [[ -f "$APP_DIR/requirements.txt" ]]; then
  log "Installing Python deps"
  "$PYTHON_BIN" -m pip install --upgrade -r "$APP_DIR/requirements.txt"
fi

# Restart service
log "Restarting systemd service: $SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl status --no-pager "$SERVICE_NAME"

success "Update complete"
