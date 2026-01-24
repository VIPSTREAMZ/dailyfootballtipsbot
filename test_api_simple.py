#!/usr/bin/env python3
"""
Simple test script for RapidAPI Football Data
Uses only standard library for initial testing
"""

import urllib.request
import json
import os
from datetime import datetime

RAPIDAPI_KEY = "664531f8e5msh6679d51214ee411p1f3777jsn43467869b7f3"
RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"

def test_api_connection():
    """Test basic API connection"""
    print("Testing RapidAPI connection...")
    print(f"Host: {RAPIDAPI_HOST}")
    print(f"API Key: {RAPIDAPI_KEY[:20]}...")

    url = f"https://{RAPIDAPI_HOST}/football-get-fixtures?date={datetime.utcnow().strftime('%Y-%m-%d')}"

    req = urllib.request.Request(url)
    req.add_header("x-rapidapi-host", RAPIDAPI_HOST)
    req.add_header("x-rapidapi-key", RAPIDAPI_KEY)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            print(f"\nStatus: {response.status}")
            print(f"Response type: {type(data)}")

            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")

                if "response" in data:
                    fixtures = data["response"]
                    print(f"\nFound {len(fixtures)} fixtures")

                    if fixtures:
                        print("\nFirst fixture:")
                        fixture = fixtures[0]
                        print(json.dumps(fixture, indent=2)[:500])
                    else:
                        print("No fixtures available for today")
                else:
                    print("Response structure:")
                    print(json.dumps(data, indent=2)[:500])

            return data

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Message: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

if __name__ == "__main__":
    test_api_connection()
