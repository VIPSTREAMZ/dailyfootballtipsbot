import os
import time
import json
import redis
import random
from datetime import datetime
from mock_feeds import mock_matches

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)
ODDS_KEY = "odds:latest"
EVENTS_KEY_PREFIX = "match:events:"


def simulate_match_events(match_id, home, away):
    """Simulate random match events"""
    events = []
    minute = random.randint(1, 90)

    if random.random() > 0.6:
        team = "home" if random.random() > 0.5 else "away"
        events.append({
            "ts": time.time(),
            "home": home,
            "away": away,
            "event": {
                "type": "goal",
                "team": team,
                "minute": minute
            }
        })

    return events


def loop():
    """Main collector loop"""
    print("Starting collector loop...")

    while True:
        try:
            m = mock_matches()
            r.set(ODDS_KEY, json.dumps({"ts": time.time(), "data": m}))

            for md in m["matches"]:
                key = EVENTS_KEY_PREFIX + md["match_id"]

                if not r.exists(key):
                    r.rpush(key, json.dumps({
                        "ts": time.time(),
                        "home": md["home"],
                        "away": md["away"],
                        "event": {"type": "game_start", "minute": 0}
                    }))

                events = simulate_match_events(md["match_id"], md["home"], md["away"])
                for event in events:
                    r.rpush(key, json.dumps(event))

                r.expire(key, 86400)

            print(f"Updated {len(m['matches'])} matches at {datetime.utcnow()}")
            time.sleep(30)

        except Exception as e:
            print(f"Error in collector loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    loop()
