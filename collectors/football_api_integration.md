# Football Data API Integration Guide

This guide explains how to replace mock data with real football data from various providers.

## Recommended APIs

### 1. API-Football (RapidAPI)
- **URL**: https://rapidapi.com/api-sports/api/api-football
- **Features**: Live scores, odds, predictions, team stats
- **Pricing**: Free tier available (100 requests/day)

### 2. Football-Data.org
- **URL**: https://www.football-data.org/
- **Features**: Match schedules, results, team data
- **Pricing**: Free tier (10 requests/minute)

### 3. The Odds API
- **URL**: https://the-odds-api.com/
- **Features**: Real-time betting odds from multiple bookmakers
- **Pricing**: Free tier (500 requests/month)

## Integration Steps

### Step 1: Choose Your Data Provider

Sign up for an API key from one of the providers above.

### Step 2: Update Environment Variables

Add your API credentials to `.env`:

```bash
FOOTBALL_API_KEY=your_api_key_here
FOOTBALL_API_URL=https://api.provider.com/v1
```

### Step 3: Replace Mock Data Collector

Update `collectors/simple_collector.py`:

```python
import os
import time
import json
import redis
import aiohttp
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
FOOTBALL_API_URL = os.getenv("FOOTBALL_API_URL")

r = redis.from_url(REDIS_URL)


async def fetch_matches():
    """Fetch matches from real API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "X-RapidAPI-Key": FOOTBALL_API_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        async with session.get(
            f"{FOOTBALL_API_URL}/fixtures",
            headers=headers,
            params={"date": datetime.utcnow().strftime("%Y-%m-%d")}
        ) as resp:
            return await resp.json()


async def fetch_odds(fixture_id):
    """Fetch odds for a specific match"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "X-RapidAPI-Key": FOOTBALL_API_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        async with session.get(
            f"{FOOTBALL_API_URL}/odds",
            headers=headers,
            params={"fixture": fixture_id}
        ) as resp:
            return await resp.json()


def transform_to_internal_format(api_data):
    """Transform API data to internal format"""
    matches = []

    for fixture in api_data.get("response", []):
        match = {
            "match_id": str(fixture["fixture"]["id"]),
            "home": fixture["teams"]["home"]["name"],
            "away": fixture["teams"]["away"]["name"],
            "start_ts": fixture["fixture"]["date"],
            "markets": {
                "1x2": {
                    "home_odds": 0.0,
                    "draw_odds": 0.0,
                    "away_odds": 0.0
                }
            }
        }
        matches.append(match)

    return {"matches": matches}


async def collect_live_events(match_id):
    """Collect live match events"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "X-RapidAPI-Key": FOOTBALL_API_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        async with session.get(
            f"{FOOTBALL_API_URL}/fixtures/events",
            headers=headers,
            params={"fixture": match_id}
        ) as resp:
            return await resp.json()


async def main_loop():
    """Main collector loop"""
    while True:
        try:
            matches_data = await fetch_matches()
            transformed = transform_to_internal_format(matches_data)

            r.set("odds:latest", json.dumps({
                "ts": time.time(),
                "data": transformed
            }))

            for match in transformed["matches"]:
                match_id = match["match_id"]

                events_data = await collect_live_events(match_id)

                events_key = f"match:events:{match_id}"

                for event in events_data.get("response", []):
                    event_obj = {
                        "ts": time.time(),
                        "home": match["home"],
                        "away": match["away"],
                        "event": {
                            "type": event["type"].lower(),
                            "team": "home" if event["team"]["id"] == event["teams"]["home"]["id"] else "away",
                            "minute": event["time"]["elapsed"]
                        }
                    }
                    r.rpush(events_key, json.dumps(event_obj))

                r.expire(events_key, 86400)

            print(f"Updated {len(transformed['matches'])} matches")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"Error in collector: {e}")
            await asyncio.sleep(30)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_loop())
```

### Step 4: Update Requirements

Add to `requirements.txt`:

```
aiohttp
asyncio
```

### Step 5: Rate Limiting

Implement proper rate limiting to stay within API limits:

```python
from asyncio import Semaphore

rate_limiter = Semaphore(10)

async def fetch_with_limit(url, **kwargs):
    async with rate_limiter:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as resp:
                return await resp.json()
```

## Data Mapping

Map API fields to your internal schema:

| Internal Field | API-Football | Football-Data.org |
|----------------|--------------|-------------------|
| match_id | fixture.id | id |
| home | teams.home.name | homeTeam.name |
| away | teams.away.name | awayTeam.name |
| home_odds | odds[0].values[0].odd | - |
| match_time | fixture.date | utcDate |

## Testing

Test your integration:

```bash
python collectors/simple_collector.py
```

Monitor Redis to verify data is being stored:

```bash
redis-cli
> GET odds:latest
> LRANGE match:events:123 0 -1
```

## Error Handling

Always implement robust error handling:

- API rate limit exceeded
- Network timeouts
- Invalid API responses
- Missing data fields

## Caching Strategy

Implement caching to reduce API calls:

- Cache match data for 5-10 minutes
- Cache odds data for 1-2 minutes
- Store historical data in database
