#!/bin/bash
set -e

echo "🚀 Football Tips Bot - Setup Script"
echo "===================================="
echo ""

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your credentials."
    echo ""
fi

echo "🔍 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi
echo "✅ Python $(python3 --version) found"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi
echo "✅ Node.js $(node --version) found"

if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis is not installed. Please install Redis or use a cloud provider."
    echo "   MacOS: brew install redis"
    echo "   Ubuntu: sudo apt-get install redis-server"
    echo ""
fi

echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "📦 Installing Node.js dependencies..."
cd web
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Edit .env file with your credentials:"
echo "   - TELEGRAM_BOT_TOKEN (get from @BotFather)"
echo "   - SUPABASE_URL and keys (from Supabase dashboard)"
echo "   - STRIPE_SECRET_KEY (from Stripe dashboard)"
echo ""
echo "2. Start Redis server:"
echo "   redis-server"
echo ""
echo "3. Run the collector:"
echo "   python collectors/simple_collector.py"
echo ""
echo "4. Run the API:"
echo "   uvicorn pred_service.app:app --reload"
echo ""
echo "5. Run the bot:"
echo "   python bot/app.py"
echo ""
echo "6. Run the web frontend:"
echo "   cd web && npm run dev"
echo ""
echo "🌐 Access the application:"
echo "   Web: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Read README.md for detailed instructions."
echo ""
