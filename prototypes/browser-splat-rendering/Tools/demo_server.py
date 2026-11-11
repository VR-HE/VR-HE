#!/usr/bin/env python3
"""Local server and launcher for the VR-HE interactive browser demo (prototype).

Commands:
  run      Serve the demo and open it in one browser with a persistent demo profile.
  serve    Serve the demo only; open the printed address yourself in a browser you choose.
  collect  Pack the results folder into one ZIP file for transfer to the development laptop.

Why a fixed address and a kept profile: the demo saves records in the browser's local storage,
which belongs to one browser profile and one origin (scheme, host and port). The server always
uses http://127.0.0.1:8791, and "run" always uses the same demo profile folder, so records saved
in one session are there in the next. Profiles are never deleted or modified by this tool apart
from the browser's own use of its demo profile; your everyday browser profile is not touched.

Security and scope:
  * Binds to 127.0.0.1 only and never uses port 9002 (reserved for another local tool on the
    development laptop). On Windows the port is claimed exclusively.
  * Serves files only from the build and fixture folders. Accepts uploads only as JSON files
    with simple names under <results>/<session>/: console output, a session report with
    timings and counts, and copies of record exports (which contain the description text typed
    into the demo, so type made-up text only).
  * Never stops or kills a browser. Closing the demo window ends the session; the server stops
    by itself about a minute later, or at once with Ctrl+C.
  * Records browser/OS/GPU facts. It does not record host names, user names, account details or
    credentials; paths inside the user's folders are written with placeholders.

Platforms: Linux (development laptop, verified there) and Windows (bundle written by
Tools/package_demo_bundle.py; untested on real Windows until a recorded run says otherwise).

Examples:
  python3 -I Tools/demo_server.py run --browser chrome --build Builds/InteractiveDemo
      --fixtures Fixtures/Generated --results TestResults/raw/interactive-demo
  python -I tools/demo_server.py run --bundle <bundle folder> --browser edge
"""

import argparse
import datetime
import http.server
import importlib.util
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.dont_write_bytecode = True  # loading the harness by path must not leave __pycache__ behind

TOOLS = os.path.dirname(os.path.abspath(__file__))


def _load_harness():
    # Loaded by path: under "python -I" the script's own folder is not on sys.path.
    spec = importlib.util.spec_from_file_location("vrhe_harness", os.path.join(TOOLS, "browser_test_harness.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = _load_harness()

APP_ID = "vrhe-interactive-demo"
SERVER_VERSION = "1"
DEMO_PORT = 8791
SIGNATURE_PATH = "/__vrhe-demo"
OPEN_TIMEOUT = 90          # seconds to wait for the browser to ask for the page
HEARTBEAT_TIMEOUT = 45     # page heartbeats arrive every 5 s while a demo tab is open
EXITED_TIMEOUT = 15        # shorter wait once the browser process we started has exited
MAX_REPORT_BYTES = 4 * 2 ** 20
MAX_LOG_BYTES = 32 * 2 ** 20
QUIET_ERRORS = (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, TimeoutError)


def default_profile_dir(browser):
    """Persistent demo profile, outside synced document folders."""
    if H.IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(base, "VRHE-Interactive-Demo", "browser-profiles", browser)
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "vrhe-interactive-demo", "browser-profiles", browser)


# ------------------------------------------------------------------------------- server
class DemoHandler(http.server.BaseHTTPRequestHandler):
    server_version = "VRHEDemo/" + SERVER_VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        self.server.log("%s %s" % (self.address_string(), fmt % args))

    def _headers(self, status, length, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        # Cross-origin isolation gives the page finer performance.now() resolution.
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.end_headers()

    def _send(self, status, body, content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self._headers(status, len(body), content_type)
        if self.command != "HEAD":
            self.wfile.write(body)

    def _resolve(self, url_path):
        parts = [p for p in urllib.parse.unquote(url_path).split("/") if p]
        if not parts:
            parts = ["index.html"]
        if not all(H.safe_name(p) for p in parts):
            return None
        if parts[0] == "fixtures":
            if len(parts) != 2:
                return None
            candidate = os.path.realpath(os.path.join(self.server.fixtures_dir, parts[1]))
            root = self.server.fixtures_dir
        else:
            candidate = os.path.realpath(os.path.join(self.server.build_dir, *parts))
            root = self.server.build_dir
        if not candidate.startswith(root + os.sep) or not os.path.isfile(candidate):
            return None
        return candidate

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == SIGNATURE_PATH:
            self._send(200, json.dumps({"app": APP_ID, "version": SERVER_VERSION, "label": self.server.build_label,
                                        "port": self.server.server_port}), "application/json")
            return
        target = self._resolve(path)
        if target is None:
            self._send(404, "not found")
            return
        if os.path.basename(target) == "index.html":
            self.server.page_requested()
        content_type = H.MIME.get(os.path.splitext(target)[1].lower(), "application/octet-stream")
        size = os.path.getsize(target)
        self._headers(200, size, content_type)
        if self.command == "HEAD":
            return
        with open(target, "rb") as f:
            while True:
                block = f.read(1 << 20)
                if not block:
                    break
                self.wfile.write(block)

    def do_POST(self):
        parts = [p for p in urllib.parse.unquote(urllib.parse.urlsplit(self.path).path).split("/") if p]
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REPORT_BYTES:
            self._send(413, "too large")
            return
        body = self.rfile.read(length) if length else b""
        if parts == ["heartbeat"]:
            self.server.heartbeat(body)
            self._send(204, b"")
            return
        if len(parts) == 2 and parts[0] == "log" and self._session_ok(parts[1]):
            self._append_log(parts[1], body)
            return
        if len(parts) == 3 and parts[0] == "report" and self._session_ok(parts[1]) and \
                H.safe_name(parts[2]) and parts[2].lower().endswith(".json"):
            try:
                json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                self._send(400, "report must be JSON")
                return
            self.server.write_report(parts[1], parts[2], body)
            self._send(204, b"")
            return
        self._send(404, "not found")

    @staticmethod
    def _session_ok(session):
        return H.safe_name(session) and len(session) <= 80 and session.startswith("demo-")

    def _append_log(self, session, body):
        try:
            entries = json.loads(body.decode("utf-8"))
            if not isinstance(entries, list):
                raise ValueError("expected a list")
        except (UnicodeDecodeError, ValueError):
            self._send(400, "log must be a JSON list")
            return
        self.server.append_log(session, entries)
        self._send(204, b"")


class DemoServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR would let this server bind a port another program is listening
    # on, so it is off there and the port is claimed exclusively instead.
    allow_reuse_address = not H.IS_WINDOWS

    def __init__(self, port, build_dir, fixtures_dir, results_dir, build_label, access_log=None):
        if port in H.RESERVED_PORTS:
            raise OSError(f"port {port} is reserved")
        super().__init__(("127.0.0.1", port), DemoHandler)
        self.build_dir = os.path.realpath(build_dir)
        self.fixtures_dir = os.path.realpath(fixtures_dir)
        self.results_dir = os.path.realpath(results_dir)
        self.build_label = build_label
        self.access_log = access_log
        self.lock = threading.Lock()
        self.first_page_request = None
        self.page_requests = 0
        self.last_heartbeat = None
        self.sessions = {}

    def server_bind(self):
        if H.IS_WINDOWS and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        socketserver.TCPServer.server_bind(self)
        # HTTPServer.server_bind would look up a host name (slow, and on Windows the computer's
        # name). The loopback address is all that is needed.
        self.server_name = "127.0.0.1"
        self.server_port = self.server_address[1]

    def handle_error(self, request, client_address):
        # A browser closing a connection mid-response (WinError 10054 and similar) is normal
        # when a window or tab closes; note it in the access log instead of printing a traceback.
        error = sys.exc_info()[1]
        if isinstance(error, QUIET_ERRORS):
            self.log(f"connection closed by the browser ({type(error).__name__})")
            return
        super().handle_error(request, client_address)

    def log(self, line):
        if self.access_log:
            with self.lock:
                self.access_log.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="milliseconds"), line))
                self.access_log.flush()

    def page_requested(self):
        with self.lock:
            self.page_requests += 1
            if self.first_page_request is None:
                self.first_page_request = time.time()

    def heartbeat(self, body):
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, ValueError):
            data = {}
        session = str(data.get("session", ""))[:80]
        with self.lock:
            self.last_heartbeat = time.time()
            if DemoHandler._session_ok(session):
                info = self.sessions.setdefault(session, {"first": H.now_iso(), "ready": False})
                info["last"] = H.now_iso()
                info["ready"] = info["ready"] or bool(data.get("ready"))

    def _session_dir(self, session):
        folder = os.path.join(self.results_dir, session)
        os.makedirs(folder, exist_ok=True)
        return folder

    def append_log(self, session, entries):
        with self.lock:
            path = os.path.join(self._session_dir(session), "console.jsonl")
            if os.path.exists(path) and os.path.getsize(path) > MAX_LOG_BYTES:
                return
            with open(path, "a", encoding="utf-8") as f:
                for entry in entries[:5000]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def write_report(self, session, name, body):
        with self.lock:
            path = os.path.join(self._session_dir(session), name)
            temporary = path + ".tmp"
            with open(temporary, "wb") as f:
                f.write(body)
            for attempt in range(10):
                try:
                    os.replace(temporary, path)
                    break
                except PermissionError:  # Windows: a scanner or sync client has the file open
                    time.sleep(0.2 * (attempt + 1))


def existing_demo_server(port):
    """The signature of a VR-HE demo server already on this port, or None."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{SIGNATURE_PATH}", timeout=2) as reply:
            data = json.loads(reply.read().decode("utf-8"))
            return data if data.get("app") == APP_ID else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def open_demo_server(port, **kwargs):
    """(server, None) or (None, signature of a demo server already running there or None)."""
    if port in H.RESERVED_PORTS:
        raise SystemExit(f"Port {port} is reserved for another tool; choose a different --port.")
    try:
        return DemoServer(port, **kwargs), None
    except OSError:
        return None, existing_demo_server(port)


def port_busy_message(port, signature, build_label):
    if signature and signature.get("label") == build_label:
        return None
    if signature:
        return ("Another VR-HE demo window (a different build) is already serving the demo on this computer.\n"
                "Close that black demo window (or press Ctrl+C in it), then start this one again.")
    return (f"Port {port} on this computer is used by another program, so the demo cannot start.\n"
            "Close the other program, or restart the computer, and try again. A different port would\n"
            "also work (--port), but records saved at the usual address would not appear there.")


# ------------------------------------------------------------------------------- helpers
def resolve_paths(args):
    bundle_root, manifest = None, None
    if args.bundle:
        bundle_root = os.path.abspath(args.bundle)
        manifest = H.load_json(os.path.join(bundle_root, "bundle.json"))
        args.build = args.build or os.path.join(bundle_root, "app")
        args.fixtures = args.fixtures or os.path.join(bundle_root, "fixtures")
        args.results = args.results or os.path.join(bundle_root, "results")
    missing = [n for n in ("build", "fixtures", "results") if not getattr(args, n, None)]
    if missing:
        raise SystemExit("Give --bundle, or all of --build, --fixtures and --results (missing: " + ", ".join(missing) + ")")
    os.makedirs(args.results, exist_ok=True)
    return bundle_root, manifest


def build_label(build_dir):
    info = H.load_json(os.path.join(build_dir, "data", "build-info.json")) or {}  # DemoPaths.BuildInfoUrl
    return info.get("label") or "unlabelled build"


def browser_command(name, binary, profile, url, devtools_port=None):
    family = H.BROWSERS[name]["family"]
    if family == "chromium":
        command = [binary, f"--user-data-dir={profile}"] + H.chromium_flags()
        if devtools_port:
            command.append(f"--remote-debugging-port={devtools_port}")
        return command + [url]
    if family == "firefox":
        with open(os.path.join(profile, "user.js"), "w", encoding="utf-8") as f:
            for key, value in H.FIREFOX_PREFS.items():
                f.write(f"user_pref({json.dumps(key)}, {json.dumps(value)});\n")
        command = [binary, "--no-remote", "--profile", profile, "-width", "1400", "-height", "960"]
        if devtools_port:
            command += ["--remote-debugging-port", str(devtools_port)]
        return command + [url]
    raise ValueError(name)


def write_server_record(args, record):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(args.results, f"server-{stamp}-{record.get('mode', 'run')}.json")
    H.write_json(path, record)
    return path


def wait_for_sessions(server, proc, started, label):
    """Serve until the demo page has been closed (heartbeats stop) or Ctrl+C."""
    announced_page = announced_ready = hinted = False
    outcome = "stopped"
    try:
        while True:
            time.sleep(1)
            now = time.time()
            if server.first_page_request and not announced_page:
                announced_page = True
                print("The demo page is loading in the browser.")
            if not announced_ready and any(s.get("ready") for s in server.sessions.values()):
                announced_ready = True
                print("The demo is ready. Keep this window open while you use it.")
                print("When you are finished, close the demo browser window; this window closes its server")
                print("by itself about a minute later (or press Ctrl+C now).")
            if server.first_page_request is None and not hinted and now - started > OPEN_TIMEOUT:
                hinted = True
                print(f"The browser has not opened the demo page after {OPEN_TIMEOUT} s. It may be showing a")
                print(f"welcome, sign-in or policy screen. In that window, open http://127.0.0.1:{server.server_port}/")
                print("yourself. This server keeps waiting (Ctrl+C stops it).")
            if server.last_heartbeat is not None:
                quiet = now - server.last_heartbeat
                exited = proc is not None and proc.poll() is not None
                if quiet > HEARTBEAT_TIMEOUT or (exited and quiet > EXITED_TIMEOUT):
                    outcome = "demo window closed"
                    print(f"No open demo page for {int(quiet)} s: the {label} demo window was closed.")
                    break
    except KeyboardInterrupt:
        outcome = "stopped with Ctrl+C"
        print("Stopping the demo server (Ctrl+C).")
    return outcome


# ------------------------------------------------------------------------------- commands
def start_server(args):
    bundle_root, manifest = resolve_paths(args)
    build = os.path.realpath(args.build)
    if not os.path.isfile(os.path.join(build, "index.html")):
        print(f"The demo page is missing: {os.path.join(build, 'index.html')}")
        return None
    if bundle_root:
        if not H.verify_bundle(bundle_root, manifest):
            return None
        H.folder_notes(bundle_root)
    if not H.free_space_ok(args.results, "results"):
        return None
    label = build_label(build)
    log_path = os.path.join(args.results, "server-access.log")
    access_log = open(log_path, "a", encoding="utf-8")
    server, signature = open_demo_server(args.port, build_dir=build, fixtures_dir=args.fixtures,
                                         results_dir=args.results, build_label=label, access_log=access_log)
    if server is None:
        access_log.close()
        message = port_busy_message(args.port, signature, label)
        return ("busy", message)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # The server record keeps the bundle's identity, not its full checksum list.
    identity = {k: manifest.get(k) for k in ("bundle_name", "bundle_version", "created", "source_commit",
                                             "source_dirty")} if manifest else None
    return {"server": server, "access_log": access_log, "label": label, "bundle": identity, "build": build}


def run(args):
    label = H.BROWSERS[args.browser]["label"]
    print(f"VR-HE interactive demo (prototype, local demo data) - {label}")
    py = H.python_description()
    print(f"Python {py['version']} ({py['source']}).")
    binary, where = H.find_browser(args.browser, args.binary)
    if not binary:
        print(f"{label} was not found on this computer, so the demo cannot open in it.")
        print("Looked in: " + "; ".join(where))
        print("Try the other browser's launcher, or DEMO-SERVER-ONLY.cmd with a browser you have.")
        return 3
    version = H.browser_version(args.browser, binary)
    print(f"Found {version or label} ({where}).")

    started = start_server(args)
    if started is None:
        return 2
    url = f"http://127.0.0.1:{args.port}/"
    if isinstance(started, tuple):
        _, message = started
        if message:
            print(message)
            return 2
        print("A demo server for this build is already running in another window; using it.")
        started = None

    profile = os.path.abspath(args.profile_dir or default_profile_dir(args.browser))
    os.makedirs(profile, exist_ok=True)
    print(f"Demo browser profile (kept between runs so saved records stay): {H.display_path(profile)}")
    print(f"Your everyday {label} profile and windows are not touched.")
    command = browser_command(args.browser, binary, profile, url, args.devtools_port)
    popen_options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if H.IS_WINDOWS:
        popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # Ctrl+C here never reaches it
    else:
        popen_options["start_new_session"] = True
    launch_time = time.time()
    proc = subprocess.Popen(command, **popen_options)
    print(f"Opening the demo at {url} (this computer only).")
    if started is None:
        return 0

    server = started["server"]
    record = {
        "app": APP_ID, "mode": "run", "started": H.now_iso(), "build_label": started["label"],
        "browser": args.browser, "browser_label": label, "browser_version": version,
        "browser_install": where, "browser_binary": H.display_path(binary),
        "launch_flags": [c for c in command[1:] if c.startswith("-") and "user-data-dir" not in c],
        "profile": H.display_path(profile), "profile_kept": True, "port": args.port, "python": py,
        "system": H.system_facts(), "bundle": started["bundle"],
    }
    outcome = wait_for_sessions(server, proc, launch_time, label)
    server.shutdown()
    server.server_close()
    started["access_log"].close()
    record.update({"finished": H.now_iso(), "outcome": outcome, "page_requests": server.page_requests,
                   "sessions": server.sessions,
                   "browser_process_exited": proc.poll() is not None})
    path = write_server_record(args, record)
    finish_message(args, server, path)
    return 0


def serve(args):
    print("VR-HE interactive demo (prototype, local demo data) - server only")
    started = start_server(args)
    if started is None:
        return 2
    if isinstance(started, tuple):
        print(started[1] or "A demo server for this build is already running in another window. Use that one.")
        return 2
    server = started["server"]
    url = f"http://127.0.0.1:{args.port}/"
    print(f"The demo is served at {url} (this computer only).")
    print("Open that exact address in Edge or Chrome. Saved records belong to that browser profile and")
    print("this address, so use the same browser profile and address each time to see them again.")
    print("Press Ctrl+C or close this window to stop the server.")
    record = {"app": APP_ID, "mode": "serve", "started": H.now_iso(), "build_label": started["label"],
              "port": args.port, "python": H.python_description(), "system": H.system_facts(),
              "bundle": started["bundle"]}
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping the demo server (Ctrl+C).")
    server.shutdown()
    server.server_close()
    started["access_log"].close()
    record.update({"finished": H.now_iso(), "outcome": "stopped with Ctrl+C", "page_requests": server.page_requests,
                   "sessions": server.sessions})
    finish_message(args, server, write_server_record(args, record))
    return 0


def finish_message(args, server, record_path):
    print("The demo server has stopped.")
    sessions = sorted(server.sessions)
    if sessions:
        print(f"Session results: {len(sessions)} folder(s) in {H.display_path(args.results)}")
    print(f"Server record: {H.display_path(record_path)}")
    if args.bundle:
        print("To bring results back, run COLLECT-DEMO-RESULTS.cmd (see START-HERE-DEMO.txt).")


def collect(args):
    if not args.bundle and not args.results:
        raise SystemExit("Give --bundle or --results")
    root = os.path.abspath(args.bundle) if args.bundle else os.path.dirname(os.path.abspath(args.results))
    results = os.path.abspath(args.results or os.path.join(root, "results"))
    names = sorted(os.listdir(results)) if os.path.isdir(results) else []
    if not names:
        print("There are no demo results yet. Run RUN-DEMO-EDGE.cmd or RUN-DEMO-CHROME.cmd first.")
        return 1
    if not H.free_space_ok(root, "results ZIP"):
        return 2
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(root, f"VRHE-demo-results-{stamp}.zip")
    rules = H.scrubbers()
    scrubbed = {}
    now = time.localtime()[:6]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        def add(arcname, data):
            info = zipfile.ZipInfo(arcname, date_time=now)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)

        manifest = os.path.join(root, "bundle.json")
        if os.path.isfile(manifest):
            with open(manifest, "rb") as f:
                add("bundle.json", f.read())
        for folder, dirs, files in os.walk(results):
            dirs.sort()
            for name in sorted(files):
                if name.endswith(".tmp"):
                    continue
                full = os.path.join(folder, name)
                arcname = os.path.relpath(full, os.path.dirname(results)).replace(os.sep, "/")
                with open(full, "rb") as f:
                    data = f.read()
                if name.lower().endswith(H.TEXT_SUFFIXES):
                    data, count = H.scrub_text(data, rules)
                    if count:
                        scrubbed[arcname] = count
                add(arcname, data)
        add("collect.json", json.dumps({
            "created": H.now_iso(), "app": APP_ID, "server_version": SERVER_VERSION,
            "note": "Demo results only. Browser profiles are not included. Record exports contain the "
                    "description text typed into the demo. Text files had user-folder, user, domain and "
                    "computer names replaced by placeholders; replacements per file are listed.",
            "replacements": scrubbed}, indent=2))
    print(f"Packed the demo results into one file ({os.path.getsize(out) / 2 ** 20:.2f} MB):")
    print("  " + out)
    if scrubbed:
        print(f"({sum(scrubbed.values())} user or computer name(s) were replaced by placeholders.)")
    print("Copy this one file to the USB drive or OneDrive and bring it back to the development laptop.")
    if H.IS_WINDOWS and not args.no_open:
        try:
            subprocess.Popen(f'explorer.exe /select,"{out}"')
        except OSError:
            pass
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "serve", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--bundle", help="demo-bundle folder containing app/, fixtures/ and results/")
        p.add_argument("--build")
        p.add_argument("--fixtures")
        p.add_argument("--results")
        p.add_argument("--port", type=int, default=DEMO_PORT,
                       help=f"local port (default {DEMO_PORT}; saved records belong to one address)")
    r = sub.choices["run"]
    r.add_argument("--browser", required=True, choices=sorted(H.BROWSERS))
    r.add_argument("--binary", help="browser executable to use instead of the installed one")
    r.add_argument("--profile-dir", help="persistent demo profile folder (default: per-user app data)")
    r.add_argument("--devtools-port", type=int,
                   help="development checks only: enable the browser's local debugging port")
    sub.choices["collect"].add_argument("--no-open", action="store_true", help="do not open Explorer afterwards")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    if getattr(args, "devtools_port", None) in H.RESERVED_PORTS:
        raise SystemExit("that debugging port is reserved for another tool")
    if args.command == "run":
        return run(args)
    if args.command == "serve":
        return serve(args)
    return collect(args)


if __name__ == "__main__":
    sys.exit(main())
