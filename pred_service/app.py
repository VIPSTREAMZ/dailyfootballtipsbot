from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import time
import redis
import joblib
import numpy as np
from supabase import create_client, Client
from datetime import datetime, timedelta
from payments import router as payments_router

app = FastAPI(title="Football Prediction API")
app.include_router(payments_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
PRE_MATCH_ARTIFACT = os.path.join(MODEL_DIR, "pre_match_artifact.pkl")
INPLAY_ARTIFACT = os.path.join(MODEL_DIR, "inplay_models.pkl")

pre_match_artifact = None
inplay_models = None

try:
    if os.path.exists(PRE_MATCH_ARTIFACT):
        pre_match_artifact = joblib.load(PRE_MATCH_ARTIFACT)
except Exception:
    pre_match_artifact = None

try:
    if os.path.exists(INPLAY_ARTIFACT):
        inplay_models = joblib.load(INPLAY_ARTIFACT)
except Exception:
    inplay_models = None


def naive_probs(home: str, away: str):
    h = 1.0 + (abs(hash(home)) % 100) / 100.0
    a = 1.0 + (abs(hash(away)) % 100) / 100.0
    ph = h / (h + a)
    pa = a / (h + a)
    pd = max(0.04, 1.0 - (ph + pa))
    return ph, pd, pa


async def verify_subscription(user_id: str):
    """Check if user has active subscription"""
    try:
        result = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").gte("valid_until", datetime.utcnow().isoformat()).maybeSingle().execute()
        return result.data is not None
    except Exception:
        return False


@app.get("/")
def root():
    return {"status": "ok", "service": "football_predictions"}


@app.get("/pre-match")
async def pre_match(limit: int = 20):
    """Get pre-match predictions for upcoming matches"""
    raw = r.get("odds:latest")
    if not raw:
        raise HTTPException(status_code=404, detail="No odds available")

    blob = json.loads(raw)
    matches = blob.get("data", {}).get("matches", [])
    results = []

    for m in matches[:limit]:
        home = m.get("home")
        away = m.get("away")

        if pre_match_artifact:
            try:
                ph, pd, pa = pre_match_artifact["predict_fn"](home, away)
            except Exception:
                ph, pd, pa = naive_probs(home, away)
        else:
            ph, pd, pa = naive_probs(home, away)

        market = m.get("markets", {}).get("1x2", {})
        b_home = float(market.get("home_odds", 2.5))
        b_draw = float(market.get("draw_odds", 3.2))
        b_away = float(market.get("away_odds", 2.8))

        edges = [
            {"side": "Home", "model_prob": ph, "book_odds": b_home, "edge": ph - 1.0 / b_home},
            {"side": "Draw", "model_prob": pd, "book_odds": b_draw, "edge": pd - 1.0 / b_draw},
            {"side": "Away", "model_prob": pa, "book_odds": b_away, "edge": pa - 1.0 / b_away},
        ]
        best = max(edges, key=lambda x: x["edge"])

        match_data = {
            "match_id": m.get("match_id"),
            "match": f"{home} vs {away}",
            "home": home,
            "away": away,
            "start_time": m.get("start_ts"),
            "model_probs": {"home": ph, "draw": pd, "away": pa},
            "odds": {"home": b_home, "draw": b_draw, "away": b_away},
            "best_market": best
        }

        results.append(match_data)

        try:
            supabase.table("predictions").upsert({
                "match_id": m.get("match_id"),
                "home_team": home,
                "away_team": away,
                "prediction_type": "pre_match",
                "home_prob": ph,
                "draw_prob": pd,
                "away_prob": pa,
                "recommended_bet": best["side"],
                "edge": best["edge"],
                "odds_home": b_home,
                "odds_draw": b_draw,
                "odds_away": b_away,
                "match_time": m.get("start_ts"),
            }).execute()
        except Exception as e:
            print(f"Error saving prediction: {e}")

    return {"results": results, "ts": time.time()}


@app.get("/match/{match_id}")
async def match(match_id: str, sims: int = 1000):
    """Get in-play prediction for a specific match"""
    ekey = f"match:events:{match_id}"
    events = r.lrange(ekey, 0, -1)

    if not events:
        raise HTTPException(status_code=404, detail="No events for match")

    score = {"home": 0, "away": 0}
    minute = 1
    home_team = None
    away_team = None

    for raw in events:
        try:
            j = json.loads(raw)
        except Exception:
            continue

        ev = j.get("event", {})
        home_team = j.get("home") or home_team
        away_team = j.get("away") or away_team

        if ev.get("type") == "goal":
            if ev.get("team") == "home":
                score["home"] += 1
            elif ev.get("team") == "away":
                score["away"] += 1

        if ev.get("minute"):
            minute = max(minute, int(ev.get("minute")))

    if pre_match_artifact and home_team and away_team:
        try:
            ph0, pd0, pa0 = pre_match_artifact["predict_fn"](home_team, away_team)
        except Exception:
            ph0, pd0, pa0 = naive_probs(home_team or "home", away_team or "away")
    else:
        ph0, pd0, pa0 = naive_probs(home_team or "home", away_team or "away")

    if inplay_models:
        X_curr = [[minute, (abs(hash(home_team)) % 100) - (abs(hash(away_team)) % 100),
                   score["home"] - score["away"], 0, 0]]
        try:
            lam_h = float(inplay_models["home"].predict(X_curr)[0])
            lam_a = float(inplay_models["away"].predict(X_curr)[0])
        except Exception:
            lam_h = max(0.01, ph0 * 0.35)
            lam_a = max(0.01, pa0 * 0.35)
    else:
        lam_h = max(0.01, ph0 * 0.35)
        lam_a = max(0.01, pa0 * 0.35)

    def simulate_win_prob(lh, la, sh, sa, curr_min, sims_local):
        rem = max(90 - curr_min, 0)
        home_w = draw_w = away_w = 0
        for _ in range(sims_local):
            gh = np.random.poisson(lh * rem / 45.0)
            ga = np.random.poisson(la * rem / 45.0)
            fh = sh + int(gh)
            fa = sa + int(ga)
            if fh > fa:
                home_w += 1
            elif fa > fh:
                away_w += 1
            else:
                draw_w += 1
        return home_w / sims_local, draw_w / sims_local, away_w / sims_local

    ph, pd, pa = simulate_win_prob(lam_h, lam_a, score["home"], score["away"], minute, sims)

    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "score": score,
        "minute": minute,
        "home_prob": ph,
        "draw_prob": pd,
        "away_prob": pa,
        "lambda": {"home": lam_h, "away": lam_a},
        "recent_events": [json.loads(x) for x in events[-20:]]
    }


@app.get("/predictions/top")
async def top_predictions(limit: int = 10):
    """Get top value predictions"""
    try:
        result = supabase.table("predictions").select("*").eq("prediction_type", "pre_match").gte("match_time", datetime.utcnow().isoformat()).order("edge", desc=True).limit(limit).execute()
        return {"predictions": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/history")
async def prediction_history(days: int = 7):
    """Get prediction history and results"""
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = supabase.table("predictions").select("*").gte("created_at", cutoff).order("created_at", desc=True).execute()
        return {"predictions": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
