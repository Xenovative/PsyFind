#!/bin/bash
set -euo pipefail

# Lightweight updater: sync current working tree into APP_DIR and restart service
# This script does NOT touch the venv - it only syncs code files
SERVICE_NAME="${SERVICE_NAME:-psyfind}"
APP_DIR_ENV="${APP_DIR:-}"
APP_DIR="${APP_DIR:-}"

log()  { printf "[INFO] %s\n" "$*"; }
err()  { printf "[ERROR] %s\n" "$*" >&2; }
success(){ printf "[OK] %s\n" "$*"; }

detect_app_dir() {
  # 1) explicit env
  if [[ -n "$APP_DIR_ENV" ]]; then
    printf '%s' "$APP_DIR_ENV"
    return 0
  fi

  # 2) systemd WorkingDirectory
  local wd
  wd="$(systemctl show "$SERVICE_NAME" -p WorkingDirectory --value 2>/dev/null || true)"
  if [[ -n "$wd" && -d "$wd" ]]; then
    printf '%s' "$wd"
    return 0
  fi

  # 3) parse unit file
  local unit_file="/etc/systemd/system/${SERVICE_NAME}.service"
  if [[ -f "$unit_file" ]]; then
    wd="$(awk -F= '/^WorkingDirectory=/ {print $2; exit}' "$unit_file" 2>/dev/null)"
    if [[ -n "$wd" && -d "$wd" ]]; then
      printf '%s' "$wd"
      return 0
    fi
  fi

  # 4) fallback to /opt/<service>
  printf '/opt/%s' "$SERVICE_NAME"
}

# Resolve application directory
APP_DIR="$(detect_app_dir)"

if [[ ! -d "$APP_DIR" ]]; then
  err "APP_DIR '$APP_DIR' does not exist"
  exit 1
fi

# Ensure we run from repo root (has app.py or requirements.txt)
if [[ ! -f "app.py" && ! -f "requirements.txt" ]]; then
  err "Run this from the project root (app.py or requirements.txt missing)"
  exit 1
fi

# Sync code to APP_DIR, preserving venv/data/env
log "Syncing code to $APP_DIR"
rsync -a --delete \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".venv" \
  --exclude="venv" \
  --exclude="node_modules" \
  --exclude=".env.production" \
  --exclude="data" \
  ./ "$APP_DIR"/

# Fix permissions only for app code (not venv)
log "Fixing permissions..."
app_user="$(systemctl show "$SERVICE_NAME" -p User --value 2>/dev/null || true)"
app_user="${app_user:-$SERVICE_NAME}"
find "$APP_DIR" -not -path "$APP_DIR/venv/*" -exec chown "$app_user:$app_user" {} + 2>/dev/null || true

# Restart or start service
log "Reloading systemd units"
systemctl daemon-reload

if systemctl is-active --quiet "$SERVICE_NAME"; then
  log "Restarting service: $SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"
else
  log "Starting service: $SERVICE_NAME"
  systemctl start "$SERVICE_NAME"
fi

sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
  success "Update complete - service is running"
else
  err "Service failed to start - check logs: sudo journalctl -u $SERVICE_NAME -n 20"
  exit 1
fi

systemctl status --no-pager "$SERVICE_NAME"
