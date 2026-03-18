import os
import requests
from datetime import datetime, timezone

STRAVA_CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
STRAVA_CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
STRAVA_REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

def get_access_token():
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["access_token"]

def fetch_latest_activities(access_token, per_page=5):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": per_page, "page": 1}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    print("✅ Starting Strava fetch...")
    token = get_access_token()
    activities = fetch_latest_activities(token, per_page=5)

    print(f"✅ Found {len(activities)} activities (showing up to 5):\n")

    for a in activities:
        name = a.get("name", "No name")
        sport = a.get("sport_type", "Unknown")
        start = a.get("start_date", "")
        dist_m = a.get("distance", 0.0)
        time_s = a.get("moving_time", 0)

        dist_km = dist_m / 1000.0
        pace = None
        if dist_km > 0:
            pace_s_per_km = time_s / dist_km
            mins = int(pace_s_per_km // 60)
            secs = int(pace_s_per_km % 60)
            pace = f"{mins}:{secs:02d} /km"

        print(f"- {start} | {sport:10} | {dist_km:6.2f} km | {time_s:4d} s | pace {pace} | {name}")

    print("\n✅ Done.")

if __name__ == "__main__":
    main()
