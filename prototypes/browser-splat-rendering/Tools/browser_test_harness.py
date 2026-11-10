#!/usr/bin/env python3
"""Local test server and browser launcher for the VR-HE browser splat benchmark.

The Unity Web build reports its own results: the benchmark page POSTs JSON, screenshots and
console output back to this server, so no browser-automation driver is needed.

Commands:
  serve  Serve the build and fixtures until interrupted (for manual testing).
  run    Serve, launch one browser with a fresh temporary profile, wait for the page to
         report completion, then close that browser and print a summary.

Security and scope:
  * Binds to 127.0.0.1 only. Serves files only from the build and fixture folders.
  * Accepts uploads only under <results>/<run>/ with simple file names.
  * Launches the browser in its own process session with a temporary profile, and stops
    only that session; existing browser windows and profiles are not touched.
  * Records browser/OS/GPU facts for the test record; it does not record host names,
    accounts or credentials.

Example:
  python3 -I Tools/browser_test_harness.py run --browser chrome --run 20261110-chrome-1 \
      --build Builds/WebGL --fixtures Fixtures/Generated --results TestResults/raw \
      --profile-root /path/to/scratch/profiles
"""

import argparse
import datetime
import http.server
import json
import os
import platform
import re
import shutil
import signal
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse

SAFE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,159}$")
MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript",
    ".wasm": "application/wasm",
    ".data": "application/octet-stream",
    ".json": "application/json",
    ".ply": "application/octet-stream",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".css": "text/css",
}

BROWSERS = {
    "chrome": {
        "binary": "/opt/google/chrome/google-chrome",
        "family": "chromium",
    },
    "brave": {
        "binary": "/opt/brave.com/brave/brave-browser",
        "family": "chromium",
    },
    "chromium": {
        "binary": shutil.which("chromium") or shutil.which("chromium-browser") or "chromium",
        "family": "chromium",
    },
    "firefox": {
        "binary": "/usr/lib/firefox/firefox" if os.path.exists("/usr/lib/firefox/firefox") else (shutil.which("firefox") or "firefox"),
        "family": "firefox",
    },
}

# Harness-only flags: fresh profile, no first-run UI, no extensions/sync/background traffic,
# and no throttling of a window that loses focus. None change WebGL or GPU selection.
CHROMIUM_FLAGS = [
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-component-update",
    "--disable-background-networking",
    "--disable-sync",
    "--disable-default-apps",
    "--password-store=basic",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--new-window",
    "--window-position=0,0",
    "--window-size=1400,960",
]

FIREFOX_PREFS = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.startup.page": 0,
    "startup.homepage_welcome_url": "",
    "startup.homepage_welcome_url.additional": "",
    "browser.aboutwelcome.enabled": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "datareporting.healthreport.uploadEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "app.normandy.enabled": False,
    "browser.sessionstore.resume_from_crash": False,
    "browser.tabs.warnOnClose": False,
    "extensions.pocket.enabled": False,
    "browser.newtabpage.enabled": False,
}

FATAL_PATTERNS = ("Aborted(", "RuntimeError", "out of memory", "Out of memory", "OOM", "createUnityInstance failed")


# ------------------------------------------------------------------------------- server
class BenchmarkHandler(http.server.BaseHTTPRequestHandler):
    server_version = "VRHEBench/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        log = getattr(self.server, "access_log", None)
        if log:
            with self.server.log_lock:
                log.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="milliseconds"), fmt % args))
                log.flush()

    def _common_headers(self, length, content_type):
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        # Cross-origin isolation gives the page finer performance.now() resolution.
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")

    def _send_text(self, status, text, content_type="text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self._common_headers(len(body), content_type)
        self.end_headers()
        self.wfile.write(body)

    def _resolve_get(self, url_path):
        parts = [p for p in urllib.parse.unquote(url_path).split("/") if p]
        if parts and parts[0] == "fixtures":
            if len(parts) != 2 or not SAFE_NAME.match(parts[1]):
                return None
            return os.path.join(self.server.fixtures_dir, parts[1])
        if not parts:
            parts = ["index.html"]
        if any(p in (".", "..") or "\\" in p for p in parts):
            return None
        candidate = os.path.realpath(os.path.join(self.server.build_dir, *parts))
        if not candidate.startswith(self.server.build_dir + os.sep):
            return None
        return candidate

    def do_GET(self):
        path = self._resolve_get(urllib.parse.urlsplit(self.path).path)
        if not path or not os.path.isfile(path):
            self._send_text(404, "not found")
            return
        size = os.path.getsize(path)
        self.send_response(200)
        self._common_headers(size, MIME.get(os.path.splitext(path)[1].lower(), "application/octet-stream"))
        self.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 1 << 20)

    def do_POST(self):
        parts = [p for p in urllib.parse.unquote(urllib.parse.urlsplit(self.path).path).split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)
        if length > 64 * 1024 * 1024:
            self._send_text(413, "too large")
            return
        body = self.rfile.read(length) if length else b""
        if len(parts) == 3 and parts[0] == "report" and SAFE_NAME.match(parts[1]) and SAFE_NAME.match(parts[2]):
            folder = os.path.join(self.server.results_dir, parts[1])
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, parts[2]), "wb") as f:
                f.write(body)
            self.server.touch(parts[1], parts[2])
            self._send_text(200, "ok")
            return
        if len(parts) == 2 and parts[0] == "log" and SAFE_NAME.match(parts[1]):
            folder = os.path.join(self.server.results_dir, parts[1])
            os.makedirs(folder, exist_ok=True)
            try:
                entries = json.loads(body.decode("utf-8") or "[]")
            except ValueError:
                entries = [{"level": "harness", "text": "unparseable log batch"}]
            with self.server.log_lock:
                with open(os.path.join(folder, "console.jsonl"), "a", encoding="utf-8") as f:
                    for entry in entries:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.server.touch(parts[1], "console.jsonl", entries)
            self._send_text(200, "ok")
            return
        self._send_text(404, "not found")


class BenchmarkServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, build_dir, fixtures_dir, results_dir, port, access_log=None):
        super().__init__(("127.0.0.1", port), BenchmarkHandler)
        self.build_dir = os.path.realpath(build_dir)
        self.fixtures_dir = os.path.realpath(fixtures_dir)
        self.results_dir = os.path.realpath(results_dir)
        self.access_log = access_log
        self.log_lock = threading.Lock()
        self.last_activity = time.time()
        self.fatal_lines = []

    def touch(self, run, name, entries=None):
        self.last_activity = time.time()
        for entry in entries or []:
            text = str(entry.get("text", ""))
            if entry.get("level") in ("error", "pageerror", "unhandledrejection") and any(p in text for p in FATAL_PATTERNS):
                self.fatal_lines.append(text[:500])


# ------------------------------------------------------------------------------- facts
def command_output(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def system_facts():
    os_name = None
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    facts = {
        "os": os_name,
        "kernel": platform.release(),
        "machine": platform.machine(),
        "session_type": os.environ.get("XDG_SESSION_TYPE"),
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP"),
        "cpu": None,
        "nvidia": command_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"]),
        "prime_select": command_output(["prime-select", "query"]),
        "display_mode": None,
    }
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    facts["cpu"] = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    xr = command_output(["xrandr", "--current"])
    if xr:
        facts["display_mode"] = [l.strip() for l in xr.splitlines() if "*" in l][:2]
    return facts


# ------------------------------------------------------------------------------- browser
def build_command(name, binary, profile, url):
    family = BROWSERS[name]["family"]
    if family == "chromium":
        return [binary, f"--user-data-dir={profile}"] + CHROMIUM_FLAGS + [url]
    if family == "firefox":
        with open(os.path.join(profile, "user.js"), "w") as f:
            for key, value in FIREFOX_PREFS.items():
                f.write(f"user_pref({json.dumps(key)}, {json.dumps(value)});\n")
        return [binary, "--no-remote", "--new-instance", "--profile", profile, "-width", "1400", "-height", "960", url]
    raise ValueError(name)


def stop_session(proc, profile):
    """Stop only the browser session started by this harness."""
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    # Helper processes that left the group but still use the temporary profile.
    time.sleep(1)
    leftovers = command_output(["pgrep", "-f", profile])
    for pid in (leftovers or "").split():
        try:
            os.kill(int(pid), signal.SIGTERM)
        except (ProcessLookupError, ValueError, PermissionError):
            pass


def summarize(run_dir):
    path = os.path.join(run_dir, "summary.json")
    if not os.path.exists(path):
        print("no summary.json; partial results:", sorted(os.listdir(run_dir)) if os.path.isdir(run_dir) else [])
        return
    with open(path) as f:
        summary = json.load(f)
    print(f"run {summary.get('run')} ({summary.get('browserLabel')}): {summary.get('status')}, "
          f"{summary.get('totalSeconds', 0):.0f} s")
    for r in summary.get("results", []):
        regions = ", ".join(f"{g['name']}={g['nearest']}" for g in r.get("regions") or [])
        fps = r.get("fpsFromMeanInterval", 0)
        sort = (r.get("sortMs") or {}).get("mean", 0)
        cpu = (r.get("cpuMs") or {}).get("mean", 0)
        print(f"  {r['caseName']:<52} {r['status']:<7} splats={r.get('uploadedSplats', 0):>8} "
              f"fps={fps:6.1f} sort={sort:7.2f}ms cpu={cpu:7.2f}ms "
              f"load={r.get('downloadMs', 0) + r.get('decodeMs', 0) + r.get('uploadMs', 0):8.0f}ms {regions}"
              + (f" ERROR={r.get('error')}" if r.get("error") else ""))


def run(args):
    build = os.path.realpath(args.build)
    if not os.path.isfile(os.path.join(build, "index.html")):
        sys.exit(f"build not found: {build}/index.html")
    if not SAFE_NAME.match(args.run):
        sys.exit("run id must match " + SAFE_NAME.pattern)
    info = BROWSERS[args.browser]
    binary = args.binary or info["binary"]
    if not (os.path.isfile(binary) and os.access(binary, os.X_OK)):
        print(f"{args.browser}: not installed ({binary}); UNTESTED")
        return 3

    run_dir = os.path.join(os.path.realpath(args.results), args.run)
    if os.path.exists(run_dir):
        sys.exit(f"run folder already exists: {run_dir}")
    os.makedirs(run_dir)
    os.makedirs(args.profile_root, exist_ok=True)
    profile = tempfile.mkdtemp(prefix=f"{args.run}-", dir=args.profile_root)

    access_log = open(os.path.join(run_dir, "server.log"), "w")
    server = BenchmarkServer(build, args.fixtures, args.results, args.port, access_log)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    query = {"run": args.run, "browser": args.label or args.browser}
    for item in args.query or []:
        key, _, value = item.partition("=")
        query[key] = value
    url = f"http://127.0.0.1:{port}/index.html?" + urllib.parse.urlencode(query)
    command = build_command(args.browser, binary, profile, url)
    version = command_output([binary, "--version"])

    record = {
        "run": args.run,
        "browser": args.browser,
        "label": args.label or args.browser,
        "browser_version": version,
        "browser_family": info["family"],
        "harness_flags": [c for c in command[1:] if c.startswith("-") and not c.startswith("--user-data-dir")],
        "profile": "fresh temporary profile (deleted after the run)",
        "url_query": query,
        "server": "127.0.0.1 (COOP same-origin, COEP require-corp, no-store, no compression)",
        "system": system_facts(),
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    browser_log = open(os.path.join(run_dir, "browser-stdout.log"), "w")
    print(f"launching {args.browser} ({version}) -> {url}")
    proc = subprocess.Popen(command, stdout=browser_log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            start_new_session=True)
    outcome = "timeout"
    deadline = time.time() + args.timeout
    fatal_seen_at = None
    try:
        while time.time() < deadline:
            if os.path.exists(os.path.join(run_dir, "done.json")):
                outcome = "done"
                time.sleep(2)  # let any trailing uploads land
                break
            if proc.poll() is not None and args.browser != "firefox":
                outcome = f"browser exited ({proc.returncode})"
                break
            if server.fatal_lines and fatal_seen_at is None:
                fatal_seen_at = time.time()
                print("fatal page error:", server.fatal_lines[0][:200])
            if fatal_seen_at and time.time() - fatal_seen_at > 15:
                outcome = "page error"
                break
            if time.time() - server.last_activity > args.stall:
                outcome = f"stalled ({args.stall} s without reports)"
                break
            time.sleep(1)
    finally:
        stop_session(proc, profile)
        server.shutdown()
        server.server_close()
        access_log.close()
        browser_log.close()
        if not args.keep_profile:
            shutil.rmtree(profile, ignore_errors=True)

    record["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    record["outcome"] = outcome
    record["fatal_lines"] = server.fatal_lines[:20]
    with open(os.path.join(run_dir, "harness.json"), "w") as f:
        json.dump(record, f, indent=2)
    print("outcome:", outcome)
    summarize(run_dir)
    return 0 if outcome == "done" else 2


def serve(args):
    server = BenchmarkServer(args.build, args.fixtures, args.results, args.port)
    print(f"serving http://127.0.0.1:{server.server_address[1]}/index.html (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "run"):
        p = sub.add_parser(name)
        p.add_argument("--build", required=True)
        p.add_argument("--fixtures", required=True)
        p.add_argument("--results", required=True)
        p.add_argument("--port", type=int, default=0)
    r = sub.choices["run"]
    r.add_argument("--browser", required=True, choices=sorted(BROWSERS))
    r.add_argument("--binary")
    r.add_argument("--run", required=True)
    r.add_argument("--label")
    r.add_argument("--query", action="append", help="extra page parameter key=value (repeatable)")
    r.add_argument("--timeout", type=int, default=900)
    r.add_argument("--stall", type=int, default=240)
    r.add_argument("--profile-root", default=os.path.join(tempfile.gettempdir(), "vrhe-browser-profiles"))
    r.add_argument("--keep-profile", action="store_true")
    args = parser.parse_args()
    return run(args) if args.command == "run" else serve(args)


if __name__ == "__main__":
    sys.exit(main())
