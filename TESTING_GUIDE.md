# Football Tips Bot - Testing Guide

## Quick Start

The application is fully set up and ready to test with demo data.

### 1. Start the Web Server

```bash
npm start
```

The server will run on http://localhost:3000

### 2. View Available Data

#### Check Predictions in Database

```bash
python3 -c "
import os
os.environ['SUPABASE_URL'] = 'https://nhlhwsnhutkyrnnxqmgm.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5obGh3c25odXRreXJubnhxbWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkyMDkzMTYsImV4cCI6MjA4NDc4NTMxNn0.XD_O9qKSSiuOLf-kHM-8NWxUX5T4rMe3VouqC6CVRxs'

from shared.supabase_client import get_supabase_client

supabase = get_supabase_client()
result = supabase.table('predictions').select('*').execute()

print(f'Total predictions: {len(result.data)}')
for pred in result.data[:3]:
    print(f\"\\n{pred['home_team']} vs {pred['away_team']}\")
    print(f\"  Recommended: {pred['recommended_bet']}\")
    print(f\"  Edge: {pred['edge']:.2%}\")
"
```

### 3. Test Frontend Pages

Access these URLs in your browser:

- **Home**: http://localhost:3000/
- **Login**: http://localhost:3000/login
- **Dashboard**: http://localhost:3000/dashboard
- **Stats**: http://localhost:3000/stats
- **Subscribe**: http://localhost:3000/subscribe

### 4. Test Database Queries

#### Get all predictions:
```sql
SELECT home_team, away_team, recommended_bet, edge 
FROM predictions 
ORDER BY edge DESC;
```

#### Get active predictions:
```sql
SELECT * FROM predictions 
WHERE is_settled = false 
AND match_time > NOW();
```

## Current Test Data

The database contains 5 test predictions:

1. **Manchester United vs Liverpool**
   - Recommended: Home
   - Edge: 15%
   - Odds: 2.20 / 3.40 / 3.50

2. **Barcelona vs Real Madrid**
   - Recommended: Draw
   - Edge: 12%
   - Odds: 2.40 / 3.20 / 3.10

3. **Bayern Munich vs Dortmund**
   - Recommended: Home
   - Edge: 18%
   - Odds: 1.80 / 3.80 / 4.20

4. **PSG vs Lyon**
   - Recommended: Home
   - Edge: 22%
   - Odds: 1.65 / 4.00 / 5.50

5. **Juventus vs Inter Milan**
   - Recommended: Away
   - Edge: 10%
   - Odds: 2.80 / 3.30 / 2.70

## API Testing

### Test Supabase Connection

```bash
npm run build
```

This will verify:
- TypeScript compilation
- Vite build process
- Supabase configuration
- API integrations

### Check Environment Variables

```bash
cat web/.env
```

Should show:
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY
- VITE_API_URL

## Troubleshooting

### Build fails
```bash
cd web
npm install
npm run build
```

### Server won't start
```bash
npm install
PORT=3000 npm start
```

### Database connection issues
Check `.env` file has correct Supabase credentials

### No predictions showing
Run the prediction insert script to add test data

## Next Steps

1. Set up authentication (see AUTH_FLOW.md)
2. Configure RapidAPI integration (see RAPIDAPI_INTEGRATION.md)
3. Deploy to production (see DEPLOYMENT.md)
