import json
from datetime import datetime, timedelta
import random


def generate_match(mid):
    """Generate a mock match with realistic odds"""
    teams = [
        ("Manchester United", "Liverpool"),
        ("Barcelona", "Real Madrid"),
        ("Bayern Munich", "Borussia Dortmund"),
        ("PSG", "Marseille"),
        ("Juventus", "AC Milan"),
        ("Arsenal", "Chelsea"),
        ("Atletico Madrid", "Sevilla"),
        ("Inter Milan", "Roma"),
        ("Tottenham", "Man City"),
        ("Leicester", "West Ham"),
    ]

    team_pair = teams[mid % len(teams)]

    home_strength = random.uniform(1.5, 3.5)
    away_strength = random.uniform(1.5, 3.5)

    total_prob = home_strength + away_strength
    home_odds = round(total_prob / home_strength, 2)
    away_odds = round(total_prob / away_strength, 2)
    draw_odds = round(3.0 + random.uniform(0, 0.5), 2)

    start_time = datetime.utcnow() + timedelta(hours=random.randint(1, 48))

    return {
        "match_id": str(mid),
        "home": team_pair[0],
        "away": team_pair[1],
        "markets": {
            "1x2": {
                "home_odds": home_odds,
                "draw_odds": draw_odds,
                "away_odds": away_odds
            }
        },
        "start_ts": start_time.isoformat()
    }


def mock_matches():
    """Generate a set of mock matches"""
    return {"matches": [generate_match(i) for i in range(1, 11)]}


if __name__ == "__main__":
    print(json.dumps(mock_matches(), indent=2))
