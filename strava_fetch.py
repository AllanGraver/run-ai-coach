import os
import json
import requests
from datetime import datetime

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "activities.json")

CID = os.getenv("STRAVA_CLIENT_ID")
CS = os.getenv("STRAVA_CLIENT_SECRET")
RT = os.getenv("STRAVA_REFRESH_TOKEN")


def get_access_token():
    r = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CID,
            "client_secret": CS,
            "refresh_token": RT,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def fetch_activities(token, per_page=30):
    r = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": per_page, "page": 1},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def load_existing():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    # map: id -> activity
    return {a["id"]: a for a in data}


def save_merged(activities_by_id):
    os.makedirs(DATA_DIR, exist_ok=True)
    merged = list(activities_by_id.values())
    merged.sort(key=lambda a: a["start_date"], reverse=True)
    with open(DATA_FILE, "w") as f:
        json.dump(merged, f, indent=2)


def main():
    print("✅ Fetching Strava activities...")
    token = get_access_token()
    new_activities = fetch_activities(token)

    existing = load_existing()
    before = len(existing)

    for a in new_activities:
        existing[a["id"]] = a

    after = len(existing)

    save_merged(existing)

    print(f"✅ Activities before: {before}")
    print(f"✅ Activities after:  {after}")
    print(f"✅ New added today:   {after - before}")
    print(f"✅ Saved to {DATA_FILE}")


if __name__ == "__main__":
    main()
