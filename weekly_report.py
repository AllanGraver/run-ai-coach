import os
import json
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

import yaml  # kræver PyYAML
from analysis import (
    parse_dt, pace_min_per_km, format_pace,
    vo2max_estimate, trimp, ptss, week_key
)

DATA_FILE = "data/activities.json"
REPORT_DIR = "reports"

def load_config():
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

def load_activities():
    if not os.path.exists(DATA_FILE):
        raise SystemExit(f"❌ Missing {DATA_FILE}. Run daily fetch first.")
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def select_last_week(activities, end_dt=None):
    # sidste 7 dage (rullende) – alternativt kan vi lave “forrige ISO-uge”
    end_dt = end_dt or datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=7)
    selected = []
    for a in activities:
        dt = parse_dt(a.get("start_date", "1970-01-01T00:00:00Z"))
        if start_dt <= dt <= end_dt:
            selected.append(a)
    return selected, start_dt, end_dt

def compute_metrics(acts, cfg):
    total_dist_km = sum((a.get("distance", 0) or 0) for a in acts) / 1000.0
    total_time_s = sum((a.get("moving_time", 0) or 0) for a in acts)
    runs = [a for a in acts if (a.get("sport_type") or a.get("type") or "").lower() in ["run", "trailrun", "virtualrun", "run"]]
    n_runs = len(runs)

    # Pace stats
    paces = []
    longest = None
    fastest = None

    for a in runs:
        d = a.get("distance", 0) or 0
        t = a.get("moving_time", 0) or 0
        p = pace_min_per_km(d, t)
        if p:
            paces.append(p)
        if longest is None or d > (longest.get("distance", 0) or 0):
            longest = a
        if fastest is None:
            fastest = a if p else fastest
        else:
            pf = pace_min_per_km(fastest.get("distance", 0) or 0, fastest.get("moving_time", 0) or 0)
            if p and (pf is None or p < pf):
                fastest = a

    avg_pace = None
    if total_dist_km > 0:
        avg_pace = (total_time_s / 60.0) / total_dist_km

    # Load: TRIMP if HR present else pTSS
    hr_max = cfg["analysis"].get("hr_max")
    hr_rest = cfg["analysis"].get("hr_rest")
    sex = cfg["analysis"].get("sex", "male")
    thr = cfg["analysis"].get("threshold_pace_min_per_km")

    trimp_sum = 0.0
    trimp_count = 0
    ptss_sum = 0.0
    ptss_count = 0

    for a in runs:
        t = a.get("moving_time", 0) or 0
        hr = a.get("average_heartrate")
        if hr:
            val = trimp(t, hr, hr_rest, hr_max, sex)
            if val:
                trimp_sum += val
                trimp_count += 1
        else:
            val = ptss(a.get("distance", 0) or 0, t, thr)
            if val:
                ptss_sum += val
                ptss_count += 1

    # VO2max estimate: filter “useful” efforts
    vo2_cfg = cfg["analysis"].get("vo2", {})
    v_min = vo2_cfg.get("min_duration_min", 6)
    v_max = vo2_cfg.get("max_duration_min", 60)
    d_min = vo2_cfg.get("min_distance_km", 1.5)
    d_max = vo2_cfg.get("max_distance_km", 20)

    vo2_candidates = []
    for a in runs:
        d_km = (a.get("distance", 0) or 0) / 1000.0
        t_min = (a.get("moving_time", 0) or 0) / 60.0
        if d_km < d_min or d_km > d_max or t_min < v_min or t_min > v_max:
            continue
        est = vo2max_estimate(a.get("distance", 0) or 0, a.get("moving_time", 0) or 0)
        if est:
            vo2_candidates.append((est, a))

    vo2_best = max(vo2_candidates, key=lambda x: x[0], default=(None, None))

    return {
        "total_dist_km": total_dist_km,
        "total_time_s": total_time_s,
        "n_runs": n_runs,
        "avg_pace": avg_pace,
        "longest": longest,
        "fastest": fastest,
        "trimp_sum": trimp_sum if trimp_count > 0 else None,
        "ptss_sum": ptss_sum if ptss_count > 0 else None,
        "vo2_best": vo2_best[0],
        "vo2_best_activity": vo2_best[1],
        "runs": runs,
    }

def render_report(acts, start_dt, end_dt, metrics):
    start_str = start_dt.date().isoformat()
    end_str = end_dt.date().isoformat()

    total_time_h = metrics["total_time_s"] / 3600.0
    avg_pace_str = format_pace(metrics["avg_pace"])

    load_line = "—"
    if metrics["trimp_sum"] is not None:
        load_line = f"TRIMP: **{metrics['trimp_sum']:.0f}** (puls-baseret)"
    elif metrics["ptss_sum"] is not None:
        load_line = f"Belastning: **{metrics['ptss_sum']:.0f} pTSS** (pace-baseret fallback)"

    vo2_line = "—"
    if metrics["vo2_best"] is not None:
        vo2_line = f"VO₂max-estimat (bedste tur): **{metrics['vo2_best']:.1f} ml/kg/min**"
    else:
        vo2_line = "VO₂max-estimat: **ikke nok egnede ture** (prøv interval/tempo i 6–60 min vindue)"

    # Longest / Fastest
    longest = metrics["longest"]
    fastest = metrics["fastest"]

    def activity_line(a):
        if not a:
            return "—"
        dt = parse_dt(a.get("start_date", "1970-01-01T00:00:00Z")).date().isoformat()
        name = a.get("name", "Run")
        d_km = (a.get("distance", 0) or 0) / 1000.0
        t_s = a.get("moving_time", 0) or 0
        p = format_pace(pace_min_per_km(a.get("distance", 0) or 0, t_s))
        return f"{dt} · {d_km:.1f} km · {p} · {name}"

    lines = []
    for a in sorted(metrics["runs"], key=lambda x: x.get("start_date", ""), reverse=True)[:10]:
        dt = parse_dt(a.get("start_date", "1970-01-01T00:00:00Z")).date().isoformat()
        name = a.get("name", "Run")
        d_km = (a.get("distance", 0) or 0) / 1000.0
        p = format_pace(pace_min_per_km(a.get("distance", 0) or 0, a.get("moving_time", 0) or 0))
        hr = a.get("average_heartrate")
        hr_txt = f" · HR {hr:.0f}" if hr else ""
        lines.append(f"- {dt} · {d_km:.1f} km · {p}{hr_txt} · {name}")

    report_md = f"""# Ugentlig løberapport ({start_str} → {end_str})

## Overblik
- Antal løbeture: **{metrics['n_runs']}**
- Distance: **{metrics['total_dist_km']:.1f} km**
- Tid: **{total_time_h:.1f} timer**
- Gns. pace (alle aktiviteter): **{avg_pace_str}**
- {load_line}
- {vo2_line}

## Highlights
- Længste tur: {activity_line(longest)}
- Hurtigste gennemsnitspace: {activity_line(fastest)}

## Seneste ture (max 10)
{chr(10).join(lines)}

## Noter
- Hvis du vil have mere præcis belastning: sørg for at dine løbeture har **pulsdata** (average_heartrate).
- Hvis VO₂max-estimat virker “skørt”: det er mest stabilt på **tempo/interval-lignende ture** (6–60 min).
"""
    return report_md

def save_report(md_text, end_dt):
    os.makedirs(REPORT_DIR, exist_ok=True)
    y, w, _ = end_dt.isocalendar()
    path = os.path.join(REPORT_DIR, f"weekly_{y}-W{w:02d}.md")
    latest = os.path.join(REPORT_DIR, "weekly_latest.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(latest, "w", encoding="utf-8") as f:
        f.write(md_text)
    return path, latest

def send_email_smtp(to_addr, subject, body_md):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_PASS")
    from_addr = os.getenv("EMAIL_FROM", user)

    if not all([host, port, user, pw, from_addr, to_addr]):
        raise SystemExit("❌ Missing SMTP secrets/env (SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS/EMAIL_FROM).")

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body_md)  # plain text (markdown)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls(context=context)
        server.login(user, pw)
        server.send_message(msg)

def main():
    cfg = load_config()
    acts = load_activities()

    selected, start_dt, end_dt = select_last_week(acts)
    metrics = compute_metrics(selected, cfg)
    md = render_report(selected, start_dt, end_dt, metrics)

    path, latest = save_report(md, end_dt)
    print(f"✅ Saved report: {path}")
    print(f"✅ Updated: {latest}")

    if cfg["report"].get("email_enabled", False):
        to_addr = cfg["report"]["email_to"]
        subj = f"{cfg['report'].get('subject_prefix', 'Ugerapport')} · {week_key(end_dt)} · {metrics['total_dist_km']:.1f} km"
        send_email_smtp(to_addr, subj, md)
        print(f"✅ Email sent to {to_addr}")
    else:
        print("ℹ️ Email disabled in config.yml")

if __name__ == "__main__":
    main()
