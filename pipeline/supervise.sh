#!/bin/bash
# Supervisor for the real MaleCNS battery (run_real.py).
#
# The VM reboots without warning. run_real.py checkpoints every finished
# unit to <outdir>/checkpoints/, so a relaunch resumes instead of
# restarting. This supervisor keeps the battery alive: every 60 seconds it
# checks whether run_real.py is running and results_summary.json is still
# absent, and relaunches (up to 15 times) if the process died.
#
# Launch once with: nohup ./supervise.sh > /dev/null 2>&1 &
# All actions are logged to <outdir>/supervisor.log.
set -u

PIPE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTDIR="$PIPE_DIR/real_run_w5_w11"
LOG="$OUTDIR/supervisor.log"
MAX_RELAUNCHES=15
SLEEP_SECS=60

mkdir -p "$OUTDIR"

stamp() { date -u +%FT%TZ; }

log() { echo "$(stamp) supervisor: $1" >> "$LOG"; }

alive() {
    # bracket trick: the regex run_real[.]py does not match this script's
    # own command line, and pgrep never matches itself
    pgrep -f "python3 run_real[.]py" >/dev/null 2>&1
}

log "started (pid $$), watching $OUTDIR, max relaunches $MAX_RELAUNCHES"

relaunches=0
while true; do
    if [ -f "$OUTDIR/results_summary.json" ]; then
        log "results_summary.json present, battery complete. Exiting."
        exit 0
    fi
    if alive; then
        sleep "$SLEEP_SECS"
        continue
    fi
    if [ "$relaunches" -ge "$MAX_RELAUNCHES" ]; then
        log "relaunch cap ($MAX_RELAUNCHES) reached and process still dead. Exiting."
        exit 1
    fi
    relaunches=$((relaunches + 1))
    log "run_real.py not alive, launching (relaunch #$relaunches)"
    cd "$PIPE_DIR" || { log "cannot cd to $PIPE_DIR"; exit 1; }
    nohup python3 run_real.py --config config_real.yaml --outdir "$OUTDIR" \
        >> "$OUTDIR/stdout.log" 2>&1 &
    newpid=$!
    sleep 5
    if alive; then
        log "relaunched, new pid $newpid (shell pid), process confirmed alive"
    else
        log "WARNING: launched pid $newpid but no run_real.py found after 5s"
    fi
    sleep "$SLEEP_SECS"
done
