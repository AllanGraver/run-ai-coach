import math
from datetime import datetime, timedelta, timezone

def parse_dt(s: str):
    # Strava bruger typisk ISO med 'Z'
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def pace_min_per_km(distance_m, moving_time_s):
    if not distance_m or distance_m <= 0 or not moving_time_s or moving_time_s <= 0:
        return None
    km = distance_m / 1000.0
    return (moving_time_s / 60.0) / km

def format_pace(p):
    if p is None:
        return "—"
    m = int(p)
    s = int(round((p - m) * 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d} /km"

def duration_h(moving_time_s):
    return (moving_time_s or 0) / 3600.0

# --- VO2max estimat (Daniels-lignende) ---
# VO2 (ml/kg/min) som funktion af løbehastighed v (m/min)
# VO2 = -4.60 + 0.182258*v + 0.000104*v^2
# %VO2max som funktion af tid t (min):
# pct = 0.8 + 0.1894393*e^(-0.012778*t) + 0.2989558*e^(-0.1932605*t)
def vo2max_estimate(distance_m, moving_time_s):
    if not distance_m or distance_m <= 0 or not moving_time_s or moving_time_s <= 0:
        return None
    t_min = moving_time_s / 60.0
    v_m_per_min = (distance_m / moving_time_s) * 60.0
    vo2 = -4.60 + 0.182258 * v_m_per_min + 0.000104 * (v_m_per_min ** 2)
    pct = 0.8 + 0.1894393 * math.exp(-0.012778 * t_min) + 0.2989558 * math.exp(-0.1932605 * t_min)
    if pct <= 0:
        return None
    return vo2 / pct

# --- TRIMP (hvis puls findes) ---
# HRr = (HRavg - HRrest) / (HRmax - HRrest)
# TRIMP = duration_min * HRr * exp(k*HRr)
# k = 1.92 (male), 1.67 (female)
def trimp(moving_time_s, hr_avg, hr_rest, hr_max, sex="male"):
    if not moving_time_s or moving_time_s <= 0 or not hr_avg:
        return None
    if not hr_rest or not hr_max or hr_max <= hr_rest:
        return None
    hrr = (hr_avg - hr_rest) / (hr_max - hr_rest)
    hrr = max(0.0, min(1.2, hrr))
    k = 1.92 if sex.lower() == "male" else 1.67
    dur_min = moving_time_s / 60.0
    return dur_min * hrr * math.exp(k * hrr)

# --- pTSS (fallback uden puls) ---
# IF = threshold_pace / actual_pace  (hurtigere => højere IF)
# pTSS = duration_h * 100 * IF^2
def ptss(distance_m, moving_time_s, threshold_pace_min_per_km):
    p = pace_min_per_km(distance_m, moving_time_s)
    if p is None or not threshold_pace_min_per_km:
        return None
    IF = threshold_pace_min_per_km / p
    IF = max(0.3, min(1.5, IF))
    return duration_h(moving_time_s) * 100.0 * (IF ** 2)

def week_key(dt: datetime):
    # ISO week
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"
