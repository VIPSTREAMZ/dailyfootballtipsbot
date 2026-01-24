# RapidAPI Football Data Integration Guide

## Current Status

The RapidAPI configuration has been added, but the specific endpoints for `free-api-live-football-data.p.rapidapi.com` need to be verified.

## API Configuration

Your API credentials are configured in `.env`:
```
RAPIDAPI_KEY=664531f8e5msh6679d51214ee411p1f3777jsn43467869b7f3
RAPIDAPI_HOST=free-api-live-football-data.p.rapidapi.com
```

## Finding the Correct Endpoints

To find the correct API endpoints:

1. Visit RapidAPI Hub: https://rapidapi.com/
2. Search for "free-api-live-football-data"
3. Check the API documentation for available endpoints
4. Look for endpoints like:
   - List fixtures/matches
   - Get live scores
   - Get odds data
   - Get match statistics

## Common Football API Endpoints

Most football APIs provide these types of endpoints:

### Fixtures/Matches
```
GET /fixtures?date=YYYY-MM-DD
GET /fixtures/live
GET /fixtures?league={league_id}
```

### Odds
```
GET /odds?fixture={fixture_id}
GET /odds/live
```

### Statistics
```
GET /fixtures/statistics?fixture={fixture_id}
GET /teams/{team_id}/statistics
```

## Integration Steps

Once you have the correct endpoints:

### 1. Update the Live Data Collector

Edit `collectors/live_data_collector.py` and update the URLs:

```python
async def fetch_fixtures(self, date: str = None) -> Dict[str, Any]:
    """Fetch live fixtures from RapidAPI"""
    try:
        async with aiohttp.ClientSession() as session:
            # REPLACE THIS URL with the correct endpoint
            url = f"{RAPIDAPI_URL}/correct-endpoint-here"
            params = {"date": date}

            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
```

### 2. Transform API Response

Update the `transform_to_predictions` method to match the actual API response structure:

```python
def transform_to_predictions(self, fixtures_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    predictions = []

    # Adapt this to match the actual API response structure
    for fixture in fixtures_data.get("response", []):  # or .get("data", [])
        match_id = str(fixture.get("id"))  # adjust based on actual API
        home_team = fixture.get("home", {}).get("name")  # adjust path
        away_team = fixture.get("away", {}).get("name")  # adjust path
        # ... etc
```

### 3. Run the Collector

```bash
python3 collectors/live_data_collector.py
```

## Alternative: Popular Football APIs

If the current API doesn't work, consider these alternatives:

### API-Football (Recommended)
- **URL**: https://rapidapi.com/api-sports/api/api-football
- **Free tier**: 100 requests/day
- **Features**: Comprehensive football data
- **Documentation**: Excellent

### Football-Data.org
- **URL**: https://www.football-data.org/
- **Free tier**: 10 requests/minute
- **Features**: European leagues
- **Documentation**: Good

### The Odds API
- **URL**: https://the-odds-api.com/
- **Free tier**: 500 requests/month
- **Features**: Betting odds from multiple bookmakers
- **Documentation**: Good

## Testing the Integration

1. Test API connection:
```bash
python3 test_api_simple.py
```

2. Run a single collection cycle:
```python
from collectors.live_data_collector import LiveDataCollector
import asyncio

async def test():
    collector = LiveDataCollector()
    await collector.run_collection_cycle()

asyncio.run(test())
```

3. Check database for new predictions:
```sql
SELECT COUNT(*) FROM predictions;
SELECT home_team, away_team, match_time
FROM predictions
ORDER BY created_at DESC
LIMIT 5;
```

## Current Demo Data

The application currently has 5 test predictions in the database:
- Manchester United vs Liverpool
- Barcelona vs Real Madrid
- Bayern Munich vs Dortmund
- PSG vs Lyon
- Juventus vs Inter Milan

These can be used for testing the frontend while setting up the real API integration.

## Next Steps

1. Verify the correct API endpoints on RapidAPI
2. Update `collectors/live_data_collector.py` with correct URLs
3. Test the API connection
4. Run the collector to populate real data
5. Set up automated collection (cron job or background service)
