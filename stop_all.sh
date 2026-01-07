#!/bin/bash

echo "🛑 Stopping all services..."

if [ -f .pids ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo "✅ Stopped process $pid"
        fi
    done < .pids
    rm .pids
    echo "✅ All services stopped"
else
    echo "⚠️  No .pids file found. Services may still be running."
    echo "   Find and kill manually: ps aux | grep python"
fi
