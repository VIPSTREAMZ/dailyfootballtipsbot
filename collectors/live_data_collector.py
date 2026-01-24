import os
import time
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "664531f8e5msh6679d51214ee411p1f3777jsn43467869b7f3")
RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"
RAPIDAPI_URL = f"https://{RAPIDAPI_HOST}"

try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shared.supabase_client import get_service_client
    USE_SUPABASE = True
except ImportError:
    USE_SUPABASE = False
    print("Warning: Supabase client not available, data won't be persisted")


class LiveDataCollector:
    def __init__(self):
        self.headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        self.supabase = get_service_client() if USE_SUPABASE else None

    async def fetch_fixtures(self, date: str = None) -> Dict[str, Any]:
        """Fetch live fixtures from RapidAPI"""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{RAPIDAPI_URL}/football-get-fixtures"
                params = {"date": date}

                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data
                    else:
                        print(f"API error: {resp.status}")
                        return {"response": []}
        except Exception as e:
            print(f"Error fetching fixtures: {e}")
            return {"response": []}

    async def fetch_odds(self, fixture_id: str) -> Dict[str, Any]:
        """Fetch odds for a specific fixture"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{RAPIDAPI_URL}/football-get-odds"
                params = {"fixture": fixture_id}

                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"response": []}
        except Exception as e:
            print(f"Error fetching odds for fixture {fixture_id}: {e}")
            return {"response": []}

    def transform_to_predictions(self, fixtures_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform API fixtures to prediction format"""
        predictions = []

        for fixture in fixtures_data.get("response", []):
            try:
                match_id = str(fixture.get("fixture", {}).get("id", ""))
                if not match_id:
                    continue

                home_team = fixture.get("teams", {}).get("home", {}).get("name", "Unknown")
                away_team = fixture.get("teams", {}).get("away", {}).get("name", "Unknown")
                match_time = fixture.get("fixture", {}).get("date")
                status = fixture.get("fixture", {}).get("status", {}).get("short", "NS")

                home_prob = 0.33 + (fixture.get("predictions", {}).get("home_win_prob", 0) / 100.0 * 0.67)
                draw_prob = 0.25
                away_prob = 1.0 - home_prob - draw_prob

                odds_data = fixture.get("odds", {})
                odds_home = odds_data.get("home", 2.0)
                odds_draw = odds_data.get("draw", 3.0)
                odds_away = odds_data.get("away", 3.5)

                if odds_home > 0 and home_prob > 0:
                    home_edge = (home_prob * odds_home) - 1
                    draw_edge = (draw_prob * odds_draw) - 1
                    away_edge = (away_prob * odds_away) - 1

                    max_edge = max(home_edge, draw_edge, away_edge)
                    if max_edge == home_edge:
                        recommended_bet = "home"
                        edge = home_edge
                    elif max_edge == draw_edge:
                        recommended_bet = "draw"
                        edge = draw_edge
                    else:
                        recommended_bet = "away"
                        edge = away_edge
                else:
                    recommended_bet = "home"
                    edge = 0.0

                prediction = {
                    "match_id": match_id,
                    "home_team": home_team,
                    "away_team": away_team,
                    "prediction_type": "inplay" if status in ["1H", "HT", "2H", "ET", "P"] else "pre_match",
                    "home_prob": round(home_prob, 4),
                    "draw_prob": round(draw_prob, 4),
                    "away_prob": round(away_prob, 4),
                    "recommended_bet": recommended_bet,
                    "edge": round(edge, 4),
                    "odds_home": odds_home,
                    "odds_draw": odds_draw,
                    "odds_away": odds_away,
                    "match_time": match_time,
                    "is_settled": status == "FT"
                }

                if status == "FT":
                    goals = fixture.get("goals", {})
                    home_goals = goals.get("home", 0)
                    away_goals = goals.get("away", 0)

                    if home_goals > away_goals:
                        prediction["actual_result"] = "home"
                    elif away_goals > home_goals:
                        prediction["actual_result"] = "away"
                    else:
                        prediction["actual_result"] = "draw"

                    prediction["final_score_home"] = home_goals
                    prediction["final_score_away"] = away_goals

                predictions.append(prediction)

            except Exception as e:
                print(f"Error transforming fixture: {e}")
                continue

        return predictions

    async def save_to_database(self, predictions: List[Dict[str, Any]]):
        """Save predictions to Supabase database"""
        if not self.supabase:
            print("Supabase not available, skipping database save")
            return

        for prediction in predictions:
            try:
                result = self.supabase.table("predictions").upsert(
                    prediction,
                    on_conflict="match_id"
                ).execute()

                if result.data:
                    print(f"Saved: {prediction['home_team']} vs {prediction['away_team']}")

            except Exception as e:
                print(f"Error saving prediction to database: {e}")

    async def run_collection_cycle(self):
        """Run a single collection cycle"""
        print(f"\n[{datetime.utcnow()}] Starting collection cycle...")

        today = datetime.utcnow().strftime("%Y-%m-%d")
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        fixtures_today = await self.fetch_fixtures(today)
        await asyncio.sleep(1)
        fixtures_tomorrow = await self.fetch_fixtures(tomorrow)

        all_fixtures = {
            "response": fixtures_today.get("response", []) + fixtures_tomorrow.get("response", [])
        }

        predictions = self.transform_to_predictions(all_fixtures)

        print(f"Collected {len(predictions)} predictions")

        await self.save_to_database(predictions)

        return predictions

    async def run_loop(self, interval: int = 300):
        """Run continuous collection loop"""
        print("Starting Live Data Collector...")
        print(f"API Host: {RAPIDAPI_HOST}")
        print(f"Update interval: {interval} seconds")

        while True:
            try:
                await self.run_collection_cycle()
                print(f"Next update in {interval} seconds...")
                await asyncio.sleep(interval)

            except Exception as e:
                print(f"Error in collection loop: {e}")
                await asyncio.sleep(60)


async def main():
    collector = LiveDataCollector()
    await collector.run_loop(interval=300)


if __name__ == "__main__":
    asyncio.run(main())
