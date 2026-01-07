# Daily Football Tips Bot

A comprehensive football betting tips platform with AI-powered predictions, live match analysis, and subscription management.

## Features

- **Pre-Match Predictions**: AI-powered analysis of upcoming matches
- **Live Match Analysis**: Real-time probability updates during games
- **Value Betting**: Identify positive edge opportunities against bookmaker odds
- **Telegram Bot**: Instant notifications and match updates
- **Web Dashboard**: Full-featured website for subscribers
- **Payment Processing**: Stripe integration for subscriptions
- **User Management**: Secure authentication and subscription tracking

## Tech Stack

### Backend
- **FastAPI**: REST API for predictions and payments
- **Python**: Core prediction and data processing
- **Redis**: Real-time data caching
- **Supabase**: PostgreSQL database with Row Level Security

### Frontend
- **React + TypeScript**: Modern web interface
- **Vite**: Fast development and building
- **React Router**: Client-side routing
- **TanStack Query**: Data fetching and caching

### Bot
- **aiogram**: Telegram bot framework
- **aiohttp**: Async HTTP requests

### ML Models
- **scikit-learn**: Machine learning models
- **pandas/numpy**: Data processing
- **joblib**: Model serialization

## Project Structure

```
.
├── bot/                      # Telegram bot
│   └── app.py               # Main bot application
├── collectors/               # Data collection
│   ├── simple_collector.py  # Mock data collector
│   ├── mock_feeds.py        # Mock match generator
│   └── football_api_integration.md  # Real API guide
├── pred_service/            # Prediction API
│   ├── app.py              # FastAPI application
│   ├── payments.py         # Stripe integration
│   └── model/              # ML model artifacts
├── shared/                  # Shared utilities
│   ├── supabase_client.py  # Supabase client
│   └── subscription_manager.py  # Subscription logic
├── web/                     # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── lib/            # API & Supabase clients
│   │   └── App.tsx         # Main app component
│   └── package.json
├── Procfile                 # Heroku process definitions
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis server
- Supabase account
- Stripe account
- Telegram Bot Token

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/dailyfootballtipsbot.git
cd dailyfootballtipsbot
```

### 2. Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Fill in your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
REDIS_URL=redis://localhost:6379/0
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
PRED_API=http://localhost:8000
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
FRONTEND_URL=http://localhost:5173
```

### 3. Install Dependencies

#### Backend:
```bash
pip install -r requirements.txt
```

#### Frontend:
```bash
cd web
npm install
```

### 4. Setup Database

The database migrations have already been applied to your Supabase instance.

### 5. Run Services Locally

#### Terminal 1 - Redis:
```bash
redis-server
```

#### Terminal 2 - Data Collector:
```bash
python collectors/simple_collector.py
```

#### Terminal 3 - Prediction API:
```bash
uvicorn pred_service.app:app --reload
```

#### Terminal 4 - Telegram Bot:
```bash
python bot/app.py
```

#### Terminal 5 - Web Frontend:
```bash
cd web
npm run dev
```

## Deployment

### Heroku Deployment

1. **Create Heroku App**:
```bash
heroku create your-app-name
```

2. **Add Buildpacks**:
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs
```

3. **Set Environment Variables**:
```bash
heroku config:set TELEGRAM_BOT_TOKEN=xxx
heroku config:set SUPABASE_URL=xxx
heroku config:set SUPABASE_KEY=xxx
heroku config:set SUPABASE_SERVICE_KEY=xxx
heroku config:set STRIPE_SECRET_KEY=xxx
heroku config:set STRIPE_WEBHOOK_SECRET=xxx
heroku config:set FRONTEND_URL=https://your-app.herokuapp.com
heroku config:set PRED_API=https://your-app.herokuapp.com
```

4. **Add Redis**:
```bash
heroku addons:create heroku-redis:mini
```

5. **Deploy**:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

6. **Scale Dynos**:
```bash
heroku ps:scale web=1 worker=1 bot=1
```

### Railway / Render Deployment

Both support similar deployment patterns. Connect your GitHub repository and configure environment variables.

## Configuration

### Stripe Setup

1. Get your API keys from Stripe Dashboard
2. Create webhook endpoint: `https://your-domain.com/payments/webhook`
3. Select events: `checkout.session.completed`, `customer.subscription.deleted`
4. Copy webhook secret to environment variables

### Telegram Bot Setup

1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token and add to environment variables
3. Start bot and test with `/start` command

## API Documentation

Access interactive API docs at: `http://localhost:8000/docs`

**Key Endpoints**:
- `GET /pre-match` - Get upcoming match predictions
- `GET /match/{match_id}` - Get live match analysis
- `GET /predictions/top` - Get best value bets
- `POST /payments/create-checkout-session` - Create Stripe checkout
- `POST /payments/webhook` - Handle Stripe webhooks

### Telegram Bot Commands

- `/start` - Start bot and show menu
- `/markets` - View today's best bets (requires subscription)
- `/match <id>` - Get live match analysis (requires subscription)
- `/subscribe <id>` - Subscribe to match updates
- `/mystats` - View your subscription status

## Integrating Real Football Data

See `collectors/football_api_integration.md` for detailed instructions on connecting to real APIs:

- API-Football (RapidAPI)
- Football-Data.org
- The Odds API

## Troubleshooting

### Bot Not Responding
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check bot process is running
- Review logs for errors

### Payments Not Working
- Confirm Stripe keys (test vs live mode)
- Verify webhook endpoint is accessible
- Check webhook secret matches Stripe dashboard

### No Predictions
- Ensure collector is running
- Verify Redis connection
- Test API: `curl localhost:8000/pre-match`

## License

MIT

## Support

For questions: Open an issue on GitHub
