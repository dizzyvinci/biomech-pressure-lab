#!/usr/bin/env python3
"""
connectors.py — push insole events/results OUT to other services (webhooks).

api_server.py is inbound (apps call us); this is outbound (we call them). Forward a
**fall alert** to a caregiver, a **landing score** to a coaching platform, a **cue**
to a glasses controller, a **daily summary** to a dashboard / EHR. Dependency-free
(urllib). Targets live in a JSON config mapping event-type -> webhook URL(s); add a
service by adding a URL — no code change.

    python connectors.py --demo                       # dry-run: show the payloads
    python connectors.py --config connectors.json --emit fall_alert --data '{"...":...}'

This is how "connect to other things" scales: one event bus, many subscribers.
NOT a medical device.
"""
import argparse, json, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def push(url, payload, timeout=8, dry=False):
    body = json.dumps(payload).encode()
    if dry:
        print(f"  -> POST {url}\n     {json.dumps(payload)}")
        return {"url": url, "dry_run": True}
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"url": url, "status": r.status}
    except Exception as e:
        return {"url": url, "error": str(e)}


def emit(config, event_type, payload, dry=False):
    """Send `payload` to every webhook registered for `event_type`."""
    envelope = {"source": "biomech-pressure-lab", "event": event_type, "data": payload}
    urls = (config.get("events", {}) or {}).get(event_type, [])
    if not urls:
        print(f"  (no subscribers for '{event_type}')")
    return [push(u, envelope, dry=dry) for u in urls]


DEMO_CONFIG = {"events": {
    "fall_alert":    ["https://example.com/caregiver/webhook"],
    "landing_score": ["https://example.com/coach-app/hooks/landing"],
    "cue":           ["https://example.com/glasses-controller/cue"],
    "daily_summary": ["https://example.com/dashboard/ingest"],
}}
DEMO_EVENTS = [
    ("fall_alert",    {"severity": "high", "reason": "grab + foot-load drop", "t": 22.0}),
    ("landing_score", {"discipline": "figure_skating", "score": 9.7, "verdict": "clean edge check-out"}),
    ("cue",           {"channel": "visual_lines", "action": "on", "bpm": 110}),
    ("daily_summary", {"steadiness": "Low", "romberg": 2.3, "walker_support_pct": 16}),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--emit")
    ap.add_argument("--data", help="JSON payload for --emit")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--live", action="store_true", help="actually POST (default is dry-run)")
    args = ap.parse_args()

    if args.demo:
        print("connectors demo (dry-run) — payloads that would be sent:\n")
        for et, payload in DEMO_EVENTS:
            print(f"[{et}]")
            emit(DEMO_CONFIG, et, payload, dry=True)
            print()
        print("Wire real URLs into a connectors.json (see connectors.sample.json) to go live.")
        return

    cfg = json.load(open(args.config)) if args.config else DEMO_CONFIG
    if args.emit:
        payload = json.loads(args.data) if args.data else {}
        for res in emit(cfg, args.emit, payload, dry=not args.live):
            print(res)
    else:
        print("nothing to do — try --demo, or --emit <event> --data '{...}' --live")


if __name__ == "__main__":
    main()
