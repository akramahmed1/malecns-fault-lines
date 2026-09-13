#!/bin/bash
# One-shot watchdog for the real MaleCNS battery. Safe to run from cron:
# relaunches the supervisor only if the battery is neither done nor alive.
# All actions are logged to <outdir>/supervisor.log.
set -u
PIPE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTDIR="$PIPE_DIR/real_run_w5_w11"
LOG="$OUTDIR/supervisor.log"
mkdir -p "$OUTDIR"
stamp() { date -u +%FT%TZ; }
if [ -f "$OUTDIR/results_summary.json" ]; then
    exit 0
fi
if pgrep -f "python3 run_real[.]py" >/dev/null 2>&1; then
    exit 0
fi
if pgrep -f "supervise[.]sh" >/dev/null 2>&1; then
    exit 0
fi
echo "$(stamp) supervisor: watchdog found nothing alive, launching supervise.sh" >> "$LOG"
cd "$PIPE_DIR" || exit 1
nohup ./supervise.sh > /dev/null 2>&1 &
echo "$(stamp) supervisor: supervise.sh launched (pid $!)" >> "$LOG"
