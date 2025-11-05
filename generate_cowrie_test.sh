#!/usr/bin/env bash
# generate_cowrie_test.sh — Synthetic Cowrie event generator + snapshot

set -euo pipefail

COWRIE_LOG="/opt/cowrie/var/log/cowrie/cowrie.json"
OUT_DIR="/opt/cowrie-bridge/out"
SNAP_DIR="/opt/cowrie-bridge/test-evidence"
SNAP_FILE="$SNAP_DIR/cowrie_events_snapshot.json"
BRIDGE_SVC="cowrie-bridge"
COUNT=20

mkdir -p "$SNAP_DIR"
touch "$COWRIE_LOG"
echo "[*] Generating $COUNT synthetic events into $COWRIE_LOG"

append_event(){
  local event_json="$1"
  printf '%s\n' "$event_json" | sudo tee -a "$COWRIE_LOG" > /dev/null
}

now_ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }

for i in $(seq 1 $COUNT); do
  ts=$(now_ts)
  case $((i % 4)) in
    0)
      ip="10.10.$((i%255)).$((i+10))"
      append_event "{\"timestamp\":\"$ts\",\"event\":\"cowrie.login.failed\",\"src_ip\":\"$ip\",\"username\":\"root\",\"password\":\"pass$i\"}"
      ;;
    1)
      ip="192.168.56.$((i%255))"
      append_event "{\"timestamp\":\"$ts\",\"event\":\"cowrie.login.success\",\"src_ip\":\"$ip\",\"username\":\"admin\",\"password\":\"letmein$i\"}"
      ;;
    2)
      ip="172.16.$((i%255)).$((i+2))"
      append_event "{\"timestamp\":\"$ts\",\"event\":\"cowrie.command.input\",\"session\":\"sess$i\",\"input\":\"uname -a && id\",\"src_ip\":\"$ip\",\"username\":\"root\"}"
      ;;
    3)
      ip="8.8.$((i%255)).$((i+3))"
      append_event "{\"timestamp\":\"$ts\",\"event\":\"cowrie.session.file_download\",\"session\":\"sess$i\",\"url\":\"http://malicious.example/payload$i.sh\",\"filename\":\"payload$i.sh\",\"src_ip\":\"$ip\"}"
      ;;
  esac
  sleep 0.15
done

echo "[*] Restarting bridge service if installed..."
if systemctl list-units --type=service --all | grep -q "^$BRIDGE_SVC"; then
  sudo systemctl restart "$BRIDGE_SVC" || true
  sleep 2
else
  echo "[!] Service $BRIDGE_SVC not found — run bridge manually if needed."
fi

JSON="$OUT_DIR/cowrie_events.json"
SNAP="$SNAP_FILE"

mkdir -p "$OUT_DIR"
mkdir -p "$SNAP_DIR"

timeout=10; elapsed=0
