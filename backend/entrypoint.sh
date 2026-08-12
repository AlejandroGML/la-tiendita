#!/bin/sh
# La Tiendita — container entrypoint
# Starts redis-server in the background, then runs the uvicorn app.
# Single container, single process group: redis lives inside the same
# machine so the app can reach it at localhost.

set -e

# Start Redis in the background if available (sidecar inside one container)
if command -v redis-server >/dev/null 2>&1; then
  redis-server --port 6379 --save 60 1 --appendonly no --daemonize yes
fi

# Run the app (exec keeps PID 1 = uvicorn for proper signal handling)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
