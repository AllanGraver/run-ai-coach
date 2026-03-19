import os
import requests

CID = os.getenv("STRAVA_CLIENT_ID")
CS  = os.getenv("STRAVA_CLIENT_SECRET")
RT  = os.getenv("STRAVA_REFRESH_TOKEN")

def main():
    if not all([CID, CS, RT]):
        raise SystemExit("❌ Missing STRAVA env vars (CID/CS/RT).")

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

    print(f"Token endpoint status: {r.status_code}")

    # Hvis Strava svarer med fejl, print en kort (ikke-følsom) besked
    if r.status_code != 200:
        try:
            j = r.json()
            print("❌ Token refresh failed:", j.get("error") or j)
        except Exception:
            print("❌ Token refresh failed (non-JSON response).")
        raise SystemExit(1)

    data = r.json()
    token = data.get("access_token")
    if not token:
        print("❌ No access_token in response.")
        raise SystemExit(1)

    print("✅ OK: access_token received (not printed).")

if __name__ == "__main__":
    main()``
