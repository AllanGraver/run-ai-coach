import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "activities.json")

CID = os.getenv("STRAVA_CLIENT_ID")
CS = os.getenv("STRAVA_CLIENT_SECRET")
RT = os.getenv("STRAVA_REFRESH_TOKEN")

API_BASE = "https://www.strava.com/api/v3"


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


def load_existing_by_id():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {a["id"]: a for a in data if "id" in a}


def save_by_id(activities_by_id):
    os.makedirs(DATA_DIR, exist_ok=True)
    merged = list(activities_by_id.values())
    merged.sort(key=lambda a: a.get("start_date", ""), reverse=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


def fetch_activities(token, after_epoch, per_page=200):
    """
    Henter alle aktiviteter efter 'after_epoch' via pagination.
    """
    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    all_acts = []

    while True:
        params = {
            "after": int(after_epoch),
            "per_page": per_page,
            "page": page,
        }
        r = requests.get(f"{API_BASE}/athlete/activities", headers=headers, params=params, timeout=30)

        # Rate limit / transient errors
        if r.status_code in (429, 500, 502, 503, 504):
            wait = 10
            print(f"⚠️ HTTP {r.status_code} – waiting {wait}s and retrying...")
            time.sleep(wait)
            continue

        r.raise_for_status()
        batch = r.json()

        if not batch:
            break

        all_acts.extend(batch)
        print(f"✅ Page {page}: fetched {len(batch)} (total {len(all_acts)})")

        # Hvis der kommer færre end per_page, er vi typisk ved enden
        if len(batch) < per_page:
            break

        page += 1

    return all_acts


def main():
    if not all([CID, CS, RT]):
        raise SystemExit("❌ Missing STRAVA env vars (STRAVA_CLIENT_ID/SECRET/REFRESH_TOKEN)")

    now = datetime.now(timezone.utc)
    after_dt = now - timedelta(days=365)
    after_epoch = after_dt.timestamp()

    print(f"🏁 Backfill start: fetching activities after {after_dt.isoformat()} (epoch {int(after_epoch)})")

    token = get_access_token()
    acts = fetch_activities(token, after_epoch=after_epoch, per_page=200)

    existing = load_existing_by_id()
    before = len(existing)

    for a in acts:
        existing[a["id"]] = a

    after = len(existing)
    save_by_id(existing)

    print(f"✅ Existing before: {before}")
    print(f"✅ After merge:     {after}")
    print(f"✅ Added/updated:   {after - before}")
    print(f"✅ Saved to:        {DATA_FILE}")


if __name__ == "__main__":
    main()
