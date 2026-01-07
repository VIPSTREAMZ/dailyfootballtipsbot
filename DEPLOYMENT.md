# Deployment Guide

Complete guide for deploying the Football Tips Bot to production.

## Pre-Deployment Checklist

- [ ] Supabase project created and configured
- [ ] Stripe account setup with products created
- [ ] Telegram bot token obtained
- [ ] Redis instance available (or will be provisioned)
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (automatic with most platforms)

## Environment Variables Reference

```env
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Redis
REDIS_URL=redis://user:password@host:port/0

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Application URLs
FRONTEND_URL=https://your-domain.com
PRED_API=https://your-domain.com
```

## Platform-Specific Deployments

### Heroku

#### Step 1: Create Application

```bash
heroku login
heroku create football-tips-bot
```

#### Step 2: Add Buildpacks

```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs
```

#### Step 3: Provision Add-ons

```bash
heroku addons:create heroku-redis:mini
```

#### Step 4: Configure Environment

```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key
heroku config:set SUPABASE_SERVICE_KEY=your_service_key
heroku config:set STRIPE_SECRET_KEY=your_stripe_key
heroku config:set STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

#### Step 5: Deploy

```bash
git push heroku main
```

#### Step 6: Scale Dynos

```bash
heroku ps:scale web=1:standard-1x
heroku ps:scale worker=1:standard-1x
heroku ps:scale bot=1:standard-1x
```

#### Step 7: Monitor

```bash
heroku logs --tail
heroku ps
```

### Railway

#### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

#### Step 2: Initialize Project

```bash
railway init
```

#### Step 3: Add Services

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn pred_service.app:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Step 4: Add Redis

```bash
railway add redis
```

#### Step 5: Set Variables

```bash
railway variables set TELEGRAM_BOT_TOKEN=xxx
railway variables set SUPABASE_URL=xxx
```

#### Step 6: Deploy

```bash
railway up
```

### Render

#### Step 1: Create Web Service

1. Connect GitHub repository
2. Select "Web Service"
3. Configure:
   - **Build Command**: `pip install -r requirements.txt && cd web && npm install && npm run build`
   - **Start Command**: `uvicorn pred_service.app:app --host 0.0.0.0 --port $PORT`

#### Step 2: Create Background Workers

Create two additional services:
- **Collector**: Start command `python collectors/simple_collector.py`
- **Bot**: Start command `python bot/app.py`

#### Step 3: Add Redis

1. Go to Dashboard → New → Redis
2. Copy internal URL to `REDIS_URL` environment variable

#### Step 4: Set Environment Variables

Add all required environment variables in service settings.

### Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cd web && npm install && npm run build

EXPOSE 8000

CMD ["uvicorn", "pred_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - redis

  collector:
    build: .
    command: python collectors/simple_collector.py
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  bot:
    build: .
    command: python bot/app.py
    environment:
      - REDIS_URL=redis://redis:6379/0
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - PRED_API=http://web:8000
    depends_on:
      - redis
      - web

volumes:
  redis-data:
```

Run with:

```bash
docker-compose up -d
```

## Post-Deployment Setup

### 1. Configure Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/payments/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
4. Copy signing secret to `STRIPE_WEBHOOK_SECRET`

### 2. Test Stripe Webhook

```bash
stripe listen --forward-to localhost:8000/payments/webhook
stripe trigger checkout.session.completed
```

### 3. Verify Telegram Bot

```bash
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### 4. Setup Domain (Optional)

Configure custom domain in platform settings:
- Heroku: Add custom domain in settings
- Railway: Configure domain in service settings
- Render: Add custom domain in dashboard

### 5. SSL Certificate

All platforms provide automatic SSL. Verify:

```bash
curl -I https://your-domain.com
```

Should show `HTTP/2 200` or `HTTP/1.1 200`

## Monitoring & Maintenance

### Health Checks

Create health check endpoints:

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "redis": check_redis(),
        "database": check_database()
    }
```

### Logging

Configure structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitoring Services

Integrate with:
- **Sentry**: Error tracking
- **Datadog**: Performance monitoring
- **Logdna**: Log aggregation

### Backup Strategy

1. **Database**: Supabase provides automatic backups
2. **Redis**: Configure persistence if using standalone Redis
3. **Configuration**: Store in version control

### Scaling

#### Horizontal Scaling

```bash
heroku ps:scale web=2 worker=2 bot=1
```

#### Vertical Scaling

```bash
heroku ps:resize web=standard-2x
```

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "your-app-name"
          heroku_email: "your-email@example.com"
```

## Security Best Practices

1. **Environment Variables**: Never commit to repository
2. **API Keys**: Use separate test/production keys
3. **HTTPS**: Always use SSL in production
4. **Rate Limiting**: Implement on API endpoints
5. **Input Validation**: Sanitize all user inputs
6. **Dependencies**: Regular security updates

```bash
pip list --outdated
npm audit
```

## Performance Optimization

1. **Redis Caching**: Cache frequent queries
2. **Database Indexing**: Already configured in migrations
3. **CDN**: Use for static assets
4. **Compression**: Enable gzip
5. **Connection Pooling**: Configure for database

## Rollback Procedure

### Heroku

```bash
heroku releases
heroku rollback v123
```

### Railway

Use web dashboard to rollback to previous deployment.

### Docker

```bash
docker-compose down
git checkout previous-commit
docker-compose up -d
```

## Cost Estimation

### Heroku (Monthly)
- Standard 1X Dyno (web): $25
- Standard 1X Dyno (worker): $25
- Standard 1X Dyno (bot): $25
- Redis Mini: $15
- **Total**: ~$90/month

### Railway (Monthly)
- Starter Plan: $5
- Resource-based pricing: ~$20-50
- **Total**: ~$25-55/month

### Render (Monthly)
- Starter instances (3): $21
- Redis: $7
- **Total**: ~$28/month

## Support & Troubleshooting

### Common Issues

1. **Application Crashes**
   - Check logs: `heroku logs --tail`
   - Verify all environment variables are set
   - Check dependencies are installed

2. **Database Connection Issues**
   - Verify Supabase credentials
   - Check connection pooling settings
   - Review RLS policies

3. **Bot Not Responding**
   - Verify token is correct
   - Check bot process is running
   - Review Telegram API limits

### Getting Help

- GitHub Issues
- Platform documentation
- Community forums