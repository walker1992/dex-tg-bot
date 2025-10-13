#!/bin/bash

set -euo pipefail

PID_FILE="bot.pid"
LOG_DIR="logs"
OUT_LOG="$LOG_DIR/bot.out"

mkdir -p "$LOG_DIR"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  echo "Bot already running, PID: $(cat "$PID_FILE")"
  exit 0
fi

nohup python3 start_bot.py >>"$OUT_LOG" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"
echo "DEX Trading Bot 已启动，PID: $PID"
echo "日志文件: $OUT_LOG"
