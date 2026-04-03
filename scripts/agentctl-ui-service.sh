#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${PID_FILE:-$BASE_DIR/.agentctl-ui.pid}"
LOG_FILE="${LOG_FILE:-$BASE_DIR/outputs/reports/agentctl-ui.log}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8787}"

mkdir -p "$(dirname "$LOG_FILE")"

is_running() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

is_port_active() {
  python3 - "$HOST" "$PORT" <<'PY'
import socket
import sys
host = sys.argv[1]
port = int(sys.argv[2])
try:
    s = socket.socket()
    s.settimeout(0.4)
except Exception:
    sys.exit(1)
try:
    s.connect((host, port))
except Exception:
    sys.exit(1)
else:
    sys.exit(0)
finally:
    s.close()
PY
}

start() {
  if is_running; then
    echo "UI already running (PID $(cat "$PID_FILE"))"
    echo "URL: http://$HOST:$PORT/?lang=pt"
    return 0
  fi
  if is_port_active; then
    echo "Port $PORT already in use and UI appears active."
    echo "URL: http://$HOST:$PORT/?lang=pt"
    return 0
  fi
  cd "$BASE_DIR"
  nohup ./scripts/agentctl-ui --host "$HOST" --port "$PORT" >>"$LOG_FILE" 2>&1 &
  echo "$!" >"$PID_FILE"
  sleep 1
  if is_running; then
    echo "UI started (PID $(cat "$PID_FILE"))"
    echo "URL: http://$HOST:$PORT/?lang=pt"
  else
    echo "Failed to start UI. Check log: $LOG_FILE"
    exit 1
  fi
}

stop() {
  if ! is_running; then
    echo "UI is not running"
    rm -f "$PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  kill "$pid" 2>/dev/null || true
  sleep 1
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  echo "UI stopped"
}

status() {
  if is_running; then
    echo "UI running (PID $(cat "$PID_FILE"))"
    echo "URL: http://$HOST:$PORT/?lang=pt"
    echo "Log: $LOG_FILE"
  elif is_port_active; then
    echo "UI active on port $PORT (process not managed by PID file)"
    echo "URL: http://$HOST:$PORT/?lang=pt"
  else
    echo "UI not running"
  fi
}

install_user_service() {
  local svc_dir="$HOME/.config/systemd/user"
  local svc_file="$svc_dir/agentctl-ui.service"
  mkdir -p "$svc_dir"
  cat >"$svc_file" <<EOF
[Unit]
Description=AgentCtl UI
After=network.target

[Service]
Type=simple
WorkingDirectory=$BASE_DIR
ExecStart=$BASE_DIR/scripts/agentctl-ui --host $HOST --port $PORT
Restart=always
RestartSec=2
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=default.target
EOF
  echo "Created: $svc_file"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user enable --now agentctl-ui.service || true
    echo "If needed, run manually:"
    echo "  systemctl --user enable --now agentctl-ui.service"
  else
    echo "systemctl not found. Use start/status commands in this script."
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  install-user-service) install_user_service ;;
  *)
    echo "Usage: ./scripts/agentctl-ui-service.sh {start|stop|restart|status|install-user-service}"
    exit 1
    ;;
esac
