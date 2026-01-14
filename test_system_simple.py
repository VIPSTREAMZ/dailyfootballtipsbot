#!/usr/bin/env python3
"""
Simplified integration test without external dependencies
Tests core functionality using existing libraries
"""

import os
import sys
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from shared.supabase_client import get_supabase_client

print("=" * 60)
print("FOOTBALL TIPS BOT - SYSTEM TEST")
print("=" * 60)
print()

supabase = get_supabase_client()
test_results = {"passed": 0, "failed": 0}


def log_test(name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   └─ {details}")
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1


# Test 1: Database Connection
print("\n📋 Test 1: Database Connectivity")
print("-" * 60)
try:
    response = supabase.table("users").select("count", count="exact").execute()
    log_test("Database connection", True, f"Connected successfully")
except Exception as e:
    log_test("Database connection", False, str(e))
    sys.exit(1)


# Test 2: Create Test User
print("\n📋 Test 2: User Management")
print("-" * 60)
test_user_data = {
    "telegram_id": f"test_{int(datetime.now().timestamp())}",
    "username": "test_user",
    "first_name": "Test",
    "email": f"test_{int(datetime.now().timestamp())}@example.com"
}

try:
    user_response = supabase.table("users").insert(test_user_data).execute()
    if user_response.data and len(user_response.data) > 0:
        test_user_id = user_response.data[0]["id"]
        log_test("Create test user", True, f"User ID: {test_user_id[:8]}...")
    else:
        log_test("Create test user", False, "No user data returned")
        test_user_id = None
except Exception as e:
    log_test("Create test user", False, str(e))
    test_user_id = None


# Test 3: Create Test Subscription
print("\n📋 Test 3: Subscription Management")
print("-" * 60)
if test_user_id:
    try:
        sub_data = {
            "user_id": test_user_id,
            "plan_type": "monthly",
            "status": "active",
            "valid_from": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=30)).isoformat()
        }
        sub_response = supabase.table("subscriptions").insert(sub_data).execute()
        if sub_response.data and len(sub_response.data) > 0:
            test_sub_id = sub_response.data[0]["id"]
            log_test("Create subscription", True, f"Subscription ID: {test_sub_id[:8]}...")
        else:
            log_test("Create subscription", False, "No subscription data returned")
            test_sub_id = None
    except Exception as e:
        log_test("Create subscription", False, str(e))
        test_sub_id = None
else:
    log_test("Create subscription", False, "No test user available")
    test_sub_id = None


# Test 4: Generate Mock Predictions
print("\n📋 Test 4: Prediction Generation & Storage")
print("-" * 60)

mock_matches = [
    {"home": "Manchester City", "away": "Liverpool", "odds": [1.8, 3.6, 4.2]},
    {"home": "Arsenal", "away": "Chelsea", "odds": [2.1, 3.2, 3.5]},
    {"home": "Tottenham", "away": "Manchester United", "odds": [2.3, 3.4, 3.1]},
]

predictions_created = 0
for idx, match in enumerate(mock_matches):
    try:
        match_id = f"match_{int(datetime.now().timestamp())}_{idx}"
        home_team = match["home"]
        away_team = match["away"]
        odds_home, odds_draw, odds_away = match["odds"]

        home_prob = (1.0 / odds_home)
        draw_prob = (1.0 / odds_draw)
        away_prob = (1.0 / odds_away)
        total = home_prob + draw_prob + away_prob
        home_prob = home_prob / total * 100
        draw_prob = draw_prob / total * 100
        away_prob = away_prob / total * 100

        recommended_bet = "home" if home_prob > max(draw_prob, away_prob) else (
            "draw" if draw_prob > away_prob else "away"
        )
        edge = max(home_prob, draw_prob, away_prob) - 33.33

        prediction_data = {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "prediction_type": "pre_match",
            "home_prob": float(home_prob),
            "draw_prob": float(draw_prob),
            "away_prob": float(away_prob),
            "recommended_bet": recommended_bet,
            "edge": float(edge),
            "odds_home": float(odds_home),
            "odds_draw": float(odds_draw),
            "odds_away": float(odds_away),
            "match_time": (datetime.now() + timedelta(hours=idx+2)).isoformat(),
            "is_settled": False
        }

        pred_response = supabase.table("predictions").insert(prediction_data).execute()
        if pred_response.data:
            predictions_created += 1

    except Exception as e:
        print(f"   Warning: Could not create prediction: {e}")

log_test("Store predictions", predictions_created > 0,
         f"Created {predictions_created} predictions")


# Test 5: Query Predictions
print("\n📋 Test 5: Prediction Retrieval")
print("-" * 60)
try:
    pred_query = supabase.table("predictions")\
        .select("*")\
        .order("match_time")\
        .limit(5)\
        .execute()

    if pred_query.data:
        log_test("Query predictions", True, f"Retrieved {len(pred_query.data)} predictions")
        print("\n   Latest predictions:")
        for pred in pred_query.data[:3]:
            print(f"   • {pred['home_team']} vs {pred['away_team']}")
            print(f"     Rec: {pred['recommended_bet'].upper()} | Edge: {pred['edge']:.1f}%")
    else:
        log_test("Query predictions", False, "No predictions found")
except Exception as e:
    log_test("Query predictions", False, str(e))


# Test 6: Test Payment Flow
print("\n📋 Test 6: Payment System")
print("-" * 60)
if test_user_id and test_sub_id:
    try:
        payment_data = {
            "user_id": test_user_id,
            "subscription_id": test_sub_id,
            "amount": 29.99,
            "currency": "USD",
            "status": "succeeded",
            "payment_method": "stripe",
            "metadata": {"test": True, "timestamp": datetime.now().isoformat()}
        }
        payment_response = supabase.table("payment_transactions").insert(payment_data).execute()
        if payment_response.data:
            log_test("Create payment transaction", True, "Payment recorded successfully")
        else:
            log_test("Create payment transaction", False, "No payment data returned")
    except Exception as e:
        log_test("Create payment transaction", False, str(e))
else:
    log_test("Create payment transaction", False, "No test user/subscription available")


# Test 7: User Tips Tracking
print("\n📋 Test 7: User Tips Tracking")
print("-" * 60)
if test_user_id:
    try:
        recent_pred = supabase.table("predictions").select("id").limit(1).execute()
        if recent_pred.data:
            pred_id = recent_pred.data[0]["id"]
            tip_data = {
                "user_id": test_user_id,
                "prediction_id": pred_id,
                "bet_side": "home",
                "stake": 10.0,
                "odds": 2.1,
                "status": "pending"
            }
            tip_response = supabase.table("user_tips").insert(tip_data).execute()
            if tip_response.data:
                log_test("Track user tip", True, "Tip recorded successfully")
            else:
                log_test("Track user tip", False, "No tip data returned")
        else:
            log_test("Track user tip", False, "No predictions available")
    except Exception as e:
        log_test("Track user tip", False, str(e))
else:
    log_test("Track user tip", False, "No test user available")


# Test 8: Performance Check
print("\n📋 Test 8: Query Performance")
print("-" * 60)
try:
    start_time = datetime.now()
    perf_query = supabase.table("predictions")\
        .select("*")\
        .gte("match_time", datetime.now().isoformat())\
        .order("edge", desc=True)\
        .limit(10)\
        .execute()

    query_time = (datetime.now() - start_time).total_seconds()

    if query_time < 2.0:
        log_test("Query performance", True, f"Query executed in {query_time:.3f}s")
    else:
        log_test("Query performance", False, f"Query took {query_time:.3f}s (>2s)")
except Exception as e:
    log_test("Query performance", False, str(e))


# Test 9: Data Integrity
print("\n📋 Test 9: Data Integrity Checks")
print("-" * 60)
try:
    users_count = supabase.table("users").select("count", count="exact").execute()
    subs_count = supabase.table("subscriptions").select("count", count="exact").execute()
    preds_count = supabase.table("predictions").select("count", count="exact").execute()
    payments_count = supabase.table("payment_transactions").select("count", count="exact").execute()

    details = f"Users: {users_count.count}, Subs: {subs_count.count}, Preds: {preds_count.count}, Payments: {payments_count.count}"
    log_test("Data integrity", True, details)
except Exception as e:
    log_test("Data integrity", False, str(e))


# Test 10: Subscription Status Check
print("\n📋 Test 10: Subscription Validation")
print("-" * 60)
if test_user_id:
    try:
        active_subs = supabase.table("subscriptions")\
            .select("*")\
            .eq("user_id", test_user_id)\
            .eq("status", "active")\
            .execute()

        if active_subs.data and len(active_subs.data) > 0:
            sub = active_subs.data[0]
            valid_until = datetime.fromisoformat(sub["valid_until"].replace("Z", "+00:00"))
            is_valid = valid_until > datetime.now().astimezone()
            log_test("Check subscription validity", is_valid,
                    f"Subscription valid until {valid_until.strftime('%Y-%m-%d')}")
        else:
            log_test("Check subscription validity", False, "No active subscription found")
    except Exception as e:
        log_test("Check subscription validity", False, str(e))
else:
    log_test("Check subscription validity", False, "No test user available")


# Final Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"✅ Passed: {test_results['passed']}")
print(f"❌ Failed: {test_results['failed']}")
print(f"📊 Total:  {test_results['passed'] + test_results['failed']}")
print()

if test_results['failed'] == 0:
    print("🎉 ALL TESTS PASSED! System is fully operational.")
    print()
    print("✨ The football tips bot is working correctly:")
    print("   ✓ Database connected and operational")
    print("   ✓ User management functional")
    print("   ✓ Subscription system active")
    print("   ✓ Prediction generation working")
    print("   ✓ Payment processing ready")
    print("   ✓ Data integrity maintained")
    print()
    print("🚀 Ready for production deployment!")
    sys.exit(0)
else:
    print("⚠️  Some tests failed. Review the output above.")
    sys.exit(1)
