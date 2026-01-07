# Quick Start Guide

Get the Football Tips Bot running in under 10 minutes.

## Prerequisites

You'll need accounts/credentials for:
- ✅ Supabase (free tier works)
- ✅ Telegram Bot Token
- ✅ Stripe (test mode is fine)
- ✅ Redis (local or cloud)

## Step 1: Get Your Credentials

### Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Copy URL and anon key from Settings → API

### Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token

### Stripe
1. Go to [stripe.com](https://stripe.com)
2. Create account
3. Copy test mode secret key from Developers → API Keys

## Step 2: Clone and Setup

```bash
git clone https://github.com/yourusername/dailyfootballtipsbot.git
cd dailyfootballtipsbot

./setup.sh
```

## Step 3: Configure Environment

Edit `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here
STRIPE_SECRET_KEY=sk_test_xxxxxx
REDIS_URL=redis://localhost:6379/0
PRED_API=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

## Step 4: Start Services

Open 5 terminal windows:

### Terminal 1: Redis
```bash
redis-server
```

### Terminal 2: Collector
```bash
python collectors/simple_collector.py
```

### Terminal 3: API
```bash
uvicorn pred_service.app:app --reload
```

### Terminal 4: Bot
```bash
python bot/app.py
```

### Terminal 5: Web
```bash
cd web
npm run dev
```

## Step 5: Test It Out

### Test the Web App
1. Open http://localhost:5173
2. Click "Sign Up"
3. Create an account
4. Browse predictions

### Test the Telegram Bot
1. Find your bot on Telegram
2. Send `/start`
3. Try `/markets` (will ask for subscription)

### Test Payments
1. Go to http://localhost:5173/subscribe
2. Click "Subscribe Now"
3. Use test card: `4242 4242 4242 4242`
4. Any future date and CVC

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
cd web && npm install
```

### Redis connection error
Start Redis: `redis-server`

### Bot not responding
- Check token in `.env`
- Verify bot process is running
- Check logs for errors

### No predictions showing
- Ensure collector is running
- Wait 30 seconds for data
- Check: `redis-cli GET odds:latest`

## Next Steps

1. **Read full documentation**: `README.md`
2. **Setup real football data**: See `collectors/football_api_integration.md`
3. **Deploy to production**: See `DEPLOYMENT.md`
4. **Configure Stripe webhook**: See deployment guide

## Common Questions

**Q: Can I use this with real money?**
A: Switch to Stripe live mode and connect real football data APIs.

**Q: How do I add more leagues?**
A: Configure your data collector to fetch from multiple leagues.

**Q: Can I customize the ML models?**
A: Yes, see `model_training/` directory for training scripts.

**Q: How do I backup data?**
A: Supabase handles database backups automatically.

## Getting Help

- Read the full README
- Check deployment guide
- Open GitHub issue
- Review logs for errors

## Development Tips

### View Logs
```bash
tail -f logs/*.log
```

### Reset Database
Via Supabase dashboard: Table Editor → Reset

### Test Payments Locally
```bash
stripe listen --forward-to localhost:8000/payments/webhook
```

### Debug Bot
Add logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## That's It!

You now have a fully functional football tips bot. The next step is connecting real football data and deploying to production.