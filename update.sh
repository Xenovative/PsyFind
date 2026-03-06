#!/bin/bash
set -euo pipefail

# Lightweight updater: sync current working tree into APP_DIR and restart service
# Defaults match deploy.sh
APP_DIR="${APP_DIR:-/opt/psyfind}"
SERVICE_NAME="${SERVICE_NAME:-psyfind}"
# PYTHON_BIN can be provided, otherwise we'll try to discover it.
PYTHON_BIN="${PYTHON_BIN:-}"
RSYNC_EXCLUDES=(".git" "__pycache__" "*.pyc" ".venv" "node_modules")

# Precompute requirements hash (before sync) to decide on pip install
SRC_REQ_HASH=""
DEST_REQ_HASH=""
if [[ -f "requirements.txt" ]]; then
  SRC_REQ_HASH="$(sha256sum requirements.txt | awk '{print $1}')"
fi
if [[ -f "$APP_DIR/requirements.txt" ]]; then
  DEST_REQ_HASH="$(sha256sum "$APP_DIR/requirements.txt" | awk '{print $1}')"
fi

log()  { printf "[INFO] %s\n" "$*"; }

create_venv() {
  local venv_dir="$APP_DIR/venv"
  local base_py

  base_py="$(command -v python3 || command -v python || true)"
  if [[ -z "$base_py" ]]; then
    err "No python3/python found to create virtualenv"
    return 1
  fi

  log "Creating virtualenv at $venv_dir using $base_py"
  if ! "$base_py" -m venv "$venv_dir"; then
    err "Failed to create venv. Install python3-venv or ensure venv module is available."
    return 1
  fi

  printf '%s' "$venv_dir/bin/python3"
}
err()  { printf "[ERROR] %s\n" "$*" >&2; }
success(){ printf "[OK] %s\n" "$*"; }

find_python() {
  # If user provided and exists, use it
  if [[ -n "$PYTHON_BIN" && -x "$PYTHON_BIN" ]]; then
    printf '%s' "$PYTHON_BIN"
    return 0
  fi

  # Common virtualenv locations
  local candidates=(
    "$APP_DIR/venv/bin/python3" "$APP_DIR/venv/bin/python"
    "$APP_DIR/.venv/bin/python3" "$APP_DIR/.venv/bin/python"
    "/opt/psyfind/venv/bin/python3" "/opt/psyfind/venv/bin/python"
    "$(command -v python3 2>/dev/null)" "$(command -v python 2>/dev/null)"
  )

  for cand in "${candidates[@]}"; do
    if [[ -n "$cand" && -x "$cand" ]]; then
      printf '%s' "$cand"
      return 0
    fi
  done

  return 1
}

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
  if [[ -n "$SRC_REQ_HASH" && "$SRC_REQ_HASH" == "$DEST_REQ_HASH" ]]; then
    log "requirements.txt unchanged; skipping pip install"
  else
    PY_BIN_RESOLVED="$(find_python || true)"

    # If we only found a system python (likely PEP 668 managed), create a project venv
    if [[ -z "$PY_BIN_RESOLVED" || "$PY_BIN_RESOLVED" != "$APP_DIR"/*/bin/python* ]]; then
      PY_BIN_RESOLVED="$(create_venv || true)"
    fi

    if [[ -n "$PY_BIN_RESOLVED" ]]; then
      log "Installing Python deps using $PY_BIN_RESOLVED"
      "$PY_BIN_RESOLVED" -m pip install --upgrade -r "$APP_DIR/requirements.txt"
    else
      err "No usable python found (set PYTHON_BIN or install python3-venv); skipping pip install"
    fi
  fi
fi

# Restart service
log "Restarting systemd service: $SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl status --no-pager "$SERVICE_NAME"

success "Update complete"
