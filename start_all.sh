#!/bin/bash

echo "🚀 Starting Football Tips Bot"
echo "=============================="
echo ""

check_env() {
    if [ ! -f .env ]; then
        echo "❌ .env file not found!"
        echo "Run ./setup.sh first or copy .env.example to .env"
        exit 1
    fi
}

check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "❌ Redis is not running!"
        echo "Start Redis with: redis-server"
        exit 1
    fi
}

check_env
check_redis

echo "✅ Prerequisites OK"
echo ""
echo "Starting services in background..."
echo ""

python collectors/simple_collector.py > logs/collector.log 2>&1 &
COLLECTOR_PID=$!
echo "✅ Collector started (PID: $COLLECTOR_PID)"

uvicorn pred_service.app:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
echo "✅ API started (PID: $API_PID)"

sleep 2

python bot/app.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "✅ Bot started (PID: $BOT_PID)"

cd web && npm run dev > ../logs/web.log 2>&1 &
WEB_PID=$!
cd ..
echo "✅ Web started (PID: $WEB_PID)"

echo ""
echo "📋 Service Status:"
echo "   Collector: PID $COLLECTOR_PID"
echo "   API: PID $API_PID"
echo "   Bot: PID $BOT_PID"
echo "   Web: PID $WEB_PID"
echo ""
echo "🌐 Access Points:"
echo "   Web: http://localhost:5173"
echo "   API: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Collector: logs/collector.log"
echo "   API: logs/api.log"
echo "   Bot: logs/bot.log"
echo "   Web: logs/web.log"
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo ""

cat > .pids <<EOF
$COLLECTOR_PID
$API_PID
$BOT_PID
$WEB_PID
EOF

echo "✅ All services started!"
