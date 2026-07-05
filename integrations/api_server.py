#!/usr/bin/env python3
"""
api_server.py — a small REST/event API so other apps connect to the insole engine.

Dependency-free (Python stdlib). It turns the analysis + integration tools into HTTP
endpoints any external service can call: a coaching app, a clinician dashboard, a
phone app that drives the Parkinson's cue glasses, a caregiver fall-alert, a smart
walker. This is the reference **API connection surface** — production would add auth
and a real WSGI/ASGI server; the shapes stay the same.

    python api_server.py --port 8787
    curl -s http://localhost:8787/health
    curl -s "http://localhost:8787/events/fog?demo=1"
    curl -s -X POST --data-binary @session.csv \
         "http://localhost:8787/analyze/landing?discipline=dance"

Endpoints
    GET  /health
    GET  /openapi.json                         machine-readable spec (connect any client)
    POST /analyze/{tool}   body = CSV log    -> analysis JSON
    GET  /events/{tool}?demo=1               -> event stream (cue/feedback) as JSON
where tool in: pressure balance balance_positions beam landing fog walker
NOT a medical device.
"""
import argparse, http.server, json, os, subprocess, sys, tempfile, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# tool -> (script, output-json filename, allows --calibration, event-style)
TOOLS = {
    "pressure":          ("analysis/interpret.py",           "insole_spec.json",      True,  False),
    "balance":           ("analysis/balance.py",             "balance_metrics.json",  True,  False),
    "balance_positions": ("analysis/balance_positions.py",   "balance_positions.json",True,  False),
    "beam":              ("analysis/beam_balance.py",        "beam_balance.json",     True,  False),
    "landing":           ("analysis/landing_lab.py",         "landing_lab.json",      True,  False),
    "fog":               ("integrations/gait_cue.py",        "cue_events.json",       False, True),
    "walker":            ("integrations/walker.py",          "walker_feedback.json",  False, True),
}


def run_tool(tool, csv_bytes, query):
    script, out_name, allows_cal, _ = TOOLS[tool]
    with tempfile.TemporaryDirectory() as td:
        cmd = [PY, os.path.join(ROOT, script)]
        if query.get("demo"):
            cmd.append("--demo")
        elif csv_bytes:
            src = os.path.join(td, "in.csv")
            open(src, "wb").write(csv_bytes)
            cmd.append(src)
        else:
            return {"error": "POST a CSV body, or pass ?demo=1"}, 400
        cmd += ["--out", td]
        if allows_cal and query.get("calibration"):
            cmd += ["--calibration", query["calibration"]]
        if tool == "landing" and query.get("discipline"):
            cmd += ["--discipline", query["discipline"]]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        path = os.path.join(td, out_name)
        if not os.path.exists(path):
            return {"error": "analysis failed", "detail": (r.stderr or r.stdout)[-800:]}, 500
        return json.load(open(path)), 200


OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "biomech-pressure-lab API", "version": "0.1.0",
             "description": "Connect any app to the insole pressure/balance/landing engine."},
    "paths": {
        "/health": {"get": {"summary": "liveness + available tools"}},
        "/analyze/{tool}": {"post": {
            "summary": "run an analysis on an uploaded CSV log",
            "parameters": [
                {"name": "tool", "in": "path", "required": True,
                 "schema": {"enum": list(TOOLS)}},
                {"name": "calibration", "in": "query", "schema": {"type": "string"},
                 "description": "server path to calibration.json for real kPa"},
                {"name": "discipline", "in": "query",
                 "schema": {"enum": ["gymnastics", "figure_skating", "dance"]}}],
            "requestBody": {"content": {"text/csv": {}}},
            "responses": {"200": {"description": "analysis JSON"}}}},
        "/events/{tool}": {"get": {
            "summary": "cue / feedback event stream (fog, walker)",
            "parameters": [{"name": "tool", "in": "path", "schema": {"enum": ["fog", "walker"]}},
                           {"name": "demo", "in": "query", "schema": {"type": "boolean"}}]}},
    },
}


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):    # quiet
        pass

    def _route(self):
        u = urllib.parse.urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        query = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        return parts, query

    def do_GET(self):
        parts, query = self._route()
        if parts == ["health"]:
            return self._send({"status": "ok", "tools": list(TOOLS)})
        if parts == ["openapi.json"]:
            return self._send(OPENAPI)
        if len(parts) == 2 and parts[0] == "events" and parts[1] in TOOLS:
            obj, code = run_tool(parts[1], None, {**query, "demo": query.get("demo", "1")})
            return self._send(obj, code)
        return self._send({"error": "not found", "try": ["/health", "/openapi.json",
                                                          "/analyze/{tool}", "/events/{tool}?demo=1"]}, 404)

    def do_POST(self):
        parts, query = self._route()
        if len(parts) == 2 and parts[0] == "analyze" and parts[1] in TOOLS:
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n) if n else b""
            obj, code = run_tool(parts[1], body, query)
            return self._send(obj, code)
        return self._send({"error": "not found"}, 404)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"biomech-pressure-lab API on http://{args.host}:{args.port}  tools={list(TOOLS)}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
