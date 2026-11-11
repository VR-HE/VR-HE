#!/usr/bin/env python3
"""Development check of the VR-HE interactive browser demo in real Chromium-family browsers.

Starts the demo through Tools/demo_server.py exactly as a tester would (persistent profile,
fixed address), then drives the page through the Chrome DevTools Protocol with trusted keyboard
and mouse input events, so Unity sees the same events as from a person. It checks controls,
pointer and panel transitions, typing without movement, selection of two racks, stable IDs,
save, reload, relaunch with the same profile, export, view orbit and the X reset, the optional
mouse Y inversion, equipment records with RU ranges, descriptions and the description-name list
(including D041's replacement rules, a refused browser write and store-level refusals), and records
frame pacing during idle, movement, looking, orbiting and panel typing.

  --part all         everything above (default; two browser sessions)
  --part authoring   only the equipment/description/name checks, with reload, restart and reset
  --part migration   needs --old-bundle <extracted first-demo bundle>: that build saves version 1
                     rack notes in a fresh profile, this build reads and carries them, then the
                     first build runs again on the same profile. Use a new --profile-dir.

Linux development laptop only. Uses a throwaway profile folder you name (never your normal
profile) and the browser's local debugging port, which this tool alone opens. Writes results to
TestResults/raw/interactive-demo/ (ignored by Git).

  python3 -I Tools/verify_interactive_demo.py --browser chrome --profile-dir <scratch>/chrome-profile

To check a packaged Windows bundle instead, extract its ZIP and add --bundle <extracted folder>:
the bundle's own tools/demo_server.py then serves its own app/ and fixtures/ after verifying their
checksums. That exercises the packaged files on Linux; it does not test Windows.
"""

import argparse
import base64
import datetime
import json
import math
import os
import random
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(PROJECT, "Assets", "InteractiveDemo", "Data", "demo-site.json")
DEMO_PORT = 8791
DEMO_URL = f"http://127.0.0.1:{DEMO_PORT}/"


# ------------------------------------------------------------------------------- websocket
class WebSocket:
    """Minimal RFC 6455 client for a local DevTools endpoint (text frames only)."""

    def __init__(self, url, timeout=60):
        parts = urllib.parse.urlsplit(url)
        if parts.hostname not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("DevTools endpoint must be local")
        self.sock = socket.create_connection((parts.hostname, parts.port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        path = parts.path + ("?" + parts.query if parts.query else "")
        request = (f"GET {path} HTTP/1.1\r\nHost: {parts.netloc}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(request.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("websocket handshake failed")
            response += chunk
        head, self.buffer = response.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise ConnectionError(head.decode(errors="replace"))

    def _read(self, n):
        while len(self.buffer) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise ConnectionError("websocket closed")
            self.buffer += chunk
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def send(self, text):
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 1 << 16:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def recv(self):
        message = b""
        while True:
            b1, b2 = self._read(2)
            opcode = b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            if b2 & 0x80:
                mask = self._read(4)
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(self._read(n)))
            else:
                data = self._read(n)
            if opcode == 0x8:
                raise ConnectionError("websocket closed by peer")
            if opcode == 0x9:  # ping
                continue
            if opcode in (0x0, 0x1, 0x2):
                message += data
                if b1 & 0x80:
                    return message.decode("utf-8")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class CDP:
    def __init__(self, ws_url):
        self.ws = WebSocket(ws_url)
        self.next_id = 0
        self.events = []

    def call(self, method, params=None, timeout=60):
        self.next_id += 1
        my_id = self.next_id
        self.ws.send(json.dumps({"id": my_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = json.loads(self.ws.recv())
            if message.get("id") == my_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            if "method" in message:
                self.events.append(message)
        raise TimeoutError(method)

    def eval(self, expression, timeout=60):
        result = self.call("Runtime.evaluate", {"expression": expression, "returnByValue": True,
                                                "awaitPromise": True}, timeout)
        if "exceptionDetails" in result:
            raise RuntimeError(f"page error in {expression[:80]}: {json.dumps(result['exceptionDetails'])[:400]}")
        return result.get("result", {}).get("value")


# ------------------------------------------------------------------------------- input
KEYS = {
    "w": ("KeyW", 87), "a": ("KeyA", 65), "s": ("KeyS", 83), "d": ("KeyD", 68), "q": ("KeyQ", 81),
    "e": ("KeyE", 69), "x": ("KeyX", 88), "v": ("KeyV", 86), "h": ("KeyH", 72), "l": ("KeyL", 76),
    "m": ("KeyM", 77), "Enter": ("Enter", 13), "Escape": ("Escape", 27), "Shift": ("ShiftLeft", 16),
    "ArrowUp": ("ArrowUp", 38), "ArrowDown": ("ArrowDown", 40), "ArrowLeft": ("ArrowLeft", 37),
    "ArrowRight": ("ArrowRight", 39), "Control": ("ControlLeft", 17), "Backspace": ("Backspace", 8),
}


class Driver:
    def __init__(self, cdp):
        self.cdp = cdp

    def key_down(self, key, modifiers=0):
        code, vk = KEYS[key]
        text = key if len(key) == 1 else ("\r" if key == "Enter" else "")
        params = {"type": "keyDown" if text else "rawKeyDown", "key": key, "code": code,
                  "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": modifiers}
        if text:
            params["text"] = text
            params["unmodifiedText"] = text
        self.cdp.call("Input.dispatchKeyEvent", params)

    def key_up(self, key, modifiers=0):
        code, vk = KEYS[key]
        self.cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": key, "code": code,
                                                 "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk,
                                                 "modifiers": modifiers})

    def press(self, key, modifiers=0):
        self.key_down(key, modifiers)
        time.sleep(0.05)
        self.key_up(key, modifiers)
        time.sleep(0.15)

    def hold(self, keys, seconds):
        for key in keys:
            self.key_down(key)
        time.sleep(seconds)
        for key in reversed(keys):
            self.key_up(key)
        time.sleep(0.2)

    def type_text(self, text, delay=0.03):
        for ch in text:
            code = ("Key" + ch.upper()) if ch.isalpha() else ("Digit" + ch if ch.isdigit() else "Space" if ch == " " else "")
            vk = ord(ch.upper()) if ch.isalnum() else (32 if ch == " " else 0)
            base = {"key": ch, "code": code, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
            self.cdp.call("Input.dispatchKeyEvent", dict(base, type="keyDown", text=ch, unmodifiedText=ch))
            self.cdp.call("Input.dispatchKeyEvent", dict(base, type="keyUp"))
            time.sleep(delay)

    def mouse(self, kind, x, y, button="none", buttons=0, clicks=0, **extra):
        params = {"type": kind, "x": x, "y": y, "button": button, "buttons": buttons, "clickCount": clicks}
        params.update(extra)
        self.cdp.call("Input.dispatchMouseEvent", params)

    def click(self, x, y, button="left"):
        mask = 1 if button == "left" else 2
        self.mouse("mouseMoved", x, y)
        time.sleep(0.08)
        self.mouse("mousePressed", x, y, button, mask, 1)
        time.sleep(0.06)
        self.mouse("mouseReleased", x, y, button, 0, 1)
        time.sleep(0.25)

    def drag(self, x0, y0, dx, dy, steps=20, seconds=0.6):
        self.mouse("mouseMoved", x0, y0)
        self.mouse("mousePressed", x0, y0, "left", 1, 1)
        for i in range(1, steps + 1):
            self.mouse("mouseMoved", x0 + dx * i / steps, y0 + dy * i / steps, "left", 1)
            time.sleep(seconds / steps)
        self.mouse("mouseReleased", x0 + dx, y0 + dy, "left", 0, 1)
        time.sleep(0.25)

    def wheel(self, x, y, delta_y):
        self.mouse("mouseWheel", x, y, deltaX=0, deltaY=delta_y)
        time.sleep(0.2)

    def click_element(self, element_id):
        self.click_selector("#" + element_id)

    def click_selector(self, selector):
        # Panels scroll; bring the control into view first, as a person would, then click its centre.
        # A control that something else covers (a sticky footer, say) is an error, not a silent misclick.
        rect = self.cdp.eval(f"(() => {{ const e = document.querySelector({json.dumps(selector)}); if (!e) return null;"
                             " e.scrollIntoView({block: 'nearest'});"
                             " const r = e.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + r.height / 2;"
                             " const hit = document.elementFromPoint(x, y);"
                             " const covered = hit && hit !== e && !e.contains(hit) ? (hit.id || hit.className || hit.tagName) : '';"
                             " return [x, y, r.width, covered]; })()")
        if not rect or rect[2] == 0:
            raise RuntimeError(f"element {selector} is not visible")
        if rect[3]:
            raise RuntimeError(f"element {selector} is covered by '{rect[3]}' at its centre")
        self.click(rect[0], rect[1])


# ------------------------------------------------------------------------------- checks
class Checks:
    def __init__(self):
        self.items = []

    def check(self, name, ok, detail=""):
        self.items.append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
        return ok

    @property
    def failed(self):
        return [i for i in self.items if not i["ok"]]


def http_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as reply:
        return json.loads(reply.read().decode("utf-8"))


def wait(predicate, timeout, interval=0.25, what="condition"):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = predicate()
            if last:
                return last
        except Exception as error:  # page may be reloading
            last = error
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for {what} (last: {str(last)[:200]})")


def start_demo(args, results, devtools_port):
    if getattr(args, "bundle", None):
        command = [sys.executable, "-I", os.path.join(args.bundle, "tools", "demo_server.py"), "run",
                   "--browser", args.browser, "--bundle", args.bundle, "--results", results]
    else:
        command = [sys.executable, "-I", os.path.join(PROJECT, "Tools", "demo_server.py"), "run",
                   "--browser", args.browser, "--build", os.path.join(PROJECT, "Builds", "InteractiveDemo"),
                   "--fixtures", os.path.join(PROJECT, "Fixtures", "Generated"), "--results", results]
    command += ["--profile-dir", args.profile_dir, "--devtools-port", str(devtools_port)]
    if args.binary:
        command += ["--binary", args.binary]
    log = open(os.path.join(results, f"launcher-{int(time.time())}.log"), "w", encoding="utf-8")
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            start_new_session=True)
    return proc, log


def connect(devtools_port, timeout=60):
    def page_target():
        for target in http_json(f"http://127.0.0.1:{devtools_port}/json/list"):
            if target.get("type") == "page" and target.get("url", "").startswith(DEMO_URL):
                return target
        return None
    target = wait(page_target, timeout, 0.5, "the demo page target")
    page = CDP(target["webSocketDebuggerUrl"])
    browser = CDP(http_json(f"http://127.0.0.1:{devtools_port}/json/version")["webSocketDebuggerUrl"])
    return page, browser


def prepare(page, browser, downloads):
    page.call("Runtime.enable")
    page.call("Page.enable")
    page.call("Emulation.setFocusEmulationEnabled", {"enabled": True})
    browser.call("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": downloads, "eventsEnabled": True})
    wait(lambda: page.eval("!!(window.VRHEDemoPage && VRHEDemoPage.test.snapshot().ready)"), 120, 0.5, "demo ready")


def snap(page):
    return page.eval("VRHEDemoPage.test.snapshot()")


def state(page):
    return page.eval("VRHEDemoPage.test.state()")


def canvas_center(page):
    return page.eval("(() => { const r = document.getElementById('unity-canvas').getBoundingClientRect();"
                     " return [r.left + r.width / 2, r.top + r.height / 2]; })()")


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def angle_delta(a, b):
    return (b - a + 540.0) % 360.0 - 180.0


def pacing(page, label, action):
    page.eval(f"VRHEDemoPage.test.pacingBegin({json.dumps(label)})")
    action()
    stats = page.eval("VRHEDemoPage.test.pacingEnd()")
    if stats:
        print(f"  pacing {label}: {stats['frames']} frames, {stats['fps']:.1f} fps, p50 {stats['p50Ms']:.1f} ms, "
              f"p95 {stats['p95Ms']:.1f} ms, p99 {stats['p99Ms']:.1f} ms, max {stats['maxMs']:.1f} ms, "
              f">50 ms {stats['over50Ms']}, cpu mean {stats['cpuMeanMs']:.2f} ms", flush=True)
    return stats


def focus_view(driver, page):
    """Click an empty strip of the canvas (top edge) to give it focus without selecting."""
    rect = page.eval("(() => { const r = document.getElementById('unity-canvas').getBoundingClientRect();"
                     " return [r.left + r.width / 2, r.top + 12]; })()")
    if not page.eval("VRHEDemoPage.test.snapshot().gate"):
        driver.click(rect[0], rect[1])
    return page.eval("VRHEDemoPage.test.snapshot().gate")


def select_via_list(driver, page, name):
    driver.press("l")
    wait(lambda: snap(page)["panel"] == "list", 5, what="list panel")
    record_id = page.eval(f"VRHEDemoPage.test.snapshot().records.find(r => r.name === {json.dumps(name)}).recordId")
    driver.click_selector(f'#list-items > li[data-record="{record_id}"] button[data-act=show]')
    wait(lambda: snap(page)["panel"] == "" and snap(page)["selectedName"] == name, 5, what=f"{name} shown")
    time.sleep(0.4)


LOOK_DEG_PER_PX = 0.15  # DemoPlayer's mouse look at the page's default 1.00x look speed


def turn_by_drag(driver, page, degrees):
    """Turn the first-person view with real horizontal drags on the canvas. The arrow keys step sideways
    (D022), so turning is by mouse. Every segment moves at least 60 px, far past the page's 5 px
    click-versus-drag slop, so a small correction can never count as a click and select a rack."""
    cx, cy = canvas_center(page)
    px = max(-400.0, min(400.0, degrees / LOOK_DEG_PER_PX))
    segments = [px] if abs(px) >= 60 else [math.copysign(100, px), px - math.copysign(100, px)]
    for seg in segments:
        driver.drag(cx - seg / 2, cy, seg, 0, max(4, int(abs(seg) / 20)), max(0.12, abs(seg) / 1500))


def walk_to(driver, page, waypoints, tolerance=0.12):
    """Closed-loop walking with real input in first person: turn with mouse drags, step with W."""
    for tx, tz in waypoints:
        for _ in range(80):
            st = state(page)
            dx, dz = tx - st["feet"][0], tz - st["feet"][2]
            d = math.hypot(dx, dz)
            if d < tolerance:
                break
            turn = angle_delta(st["viewYaw"], math.degrees(math.atan2(dx, dz)))
            if abs(turn) > 4:
                turn_by_drag(driver, page, turn)
            else:
                driver.hold(["w"], min(0.6, max(0.05, d / 1.3 - 0.02)))
        else:
            raise RuntimeError(f"could not reach waypoint {(tx, tz)}; at {state(page)['feet']}")


def face(driver, page, yaw, tolerance=1.5):
    for _ in range(20):
        turn = angle_delta(state(page)["viewYaw"], yaw)
        if abs(turn) < tolerance:
            return
        turn_by_drag(driver, page, turn)
    raise RuntimeError(f"could not face yaw {yaw}")


# ------------------------------------------------------------------------------- mouse Y inversion (D036)
PREFS_KEY = "vrhe.demo.ui-preferences.v1"


def stored_prefs(page):
    raw = page.eval(f"localStorage.getItem({json.dumps(PREFS_KEY)})")
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return {"unreadable": raw}


def set_invert(driver, page, on):
    """Tick or untick Help > Settings > Invert mouse Y-axis with a real click, then close Help with Esc."""
    focus_view(driver, page)
    if snap(page)["panel"] != "help":
        driver.press("h")
        wait(lambda: snap(page)["panel"] == "help", 5, what="help panel")
    if bool(page.eval("document.getElementById('invert-mouse-y').checked")) != on:
        driver.click_element("invert-mouse-y")
    driver.press("Escape")
    wait(lambda: snap(page)["panel"] == "", 5, what="help closed")
    return snap(page)["invertMouseY"] == on


def drag_look(driver, page, dx, dy):
    """One real left-button drag through the canvas centre; returns (yaw change, pitch change)."""
    cx, cy = canvas_center(page)
    st0 = state(page)
    driver.drag(cx - dx / 2, cy - dy / 2, dx, dy, 30, 1.0)
    st1 = state(page)
    return angle_delta(st0["viewYaw"], st1["viewYaw"]), st1["pitch"] - st0["pitch"]


def captured_vertical(driver, page, pixels=80):
    """Under pointer lock, move the mouse straight down in steps; returns (yaw change, pitch change) or None."""
    cx, cy = canvas_center(page)
    focus_view(driver, page)
    driver.press("x")
    for _ in range(2):
        driver.press("m")
        time.sleep(0.6)
        if snap(page)["locked"]:
            break
        time.sleep(1.5)  # Chrome briefly refuses a new lock right after Esc released the previous one
    else:
        return None
    driver.mouse("mouseMoved", cx, cy)   # settle: the first locked move may carry an old offset
    time.sleep(0.3)
    st0 = state(page)
    for i in range(8):
        driver.mouse("mouseMoved", cx, cy + pixels * (i + 1) / 8)
        time.sleep(0.03)
    time.sleep(0.3)
    st1 = state(page)
    driver.press("Escape")
    time.sleep(0.4)
    return angle_delta(st0["viewYaw"], st1["viewYaw"]), st1["pitch"] - st0["pitch"]


def nearest_rack_yaw(page, site, name):
    anchor = next(a for a in site["anchors"] if a["recordId"] == {r["name"]: r for r in site["records"]}[name]["recordId"])
    feet = state(page)["feet"]
    return math.degrees(math.atan2(anchor["center"][0] - feet[0], anchor["center"][2] - feet[2]))


def run_inversion_checks(page, driver, checks, site):
    """D036 with the preference ON: vertical look reverses in first person, captured mouse and third-person
    orbit; horizontal look, wheel zoom, picking and Q/E/X keep their meanings; panels still block input."""
    checks.check("Invert mouse Y-axis is off by default in a new profile",
                 not snap(page)["invertMouseY"] and not page.eval("document.getElementById('invert-mouse-y').checked"))
    focus_view(driver, page)
    driver.press("x")
    yaw_n, pitch_n = drag_look(driver, page, 120, 60)
    driver.press("x")
    checks.check("Help > Settings checkbox turns inversion on (real click)", set_invert(driver, page, True))
    prefs = stored_prefs(page) or {}
    checks.check("inversion choice is saved in this browser profile", prefs.get("invertMouseY") is True, f"{prefs}")
    focus_view(driver, page)
    driver.press("x")
    yaw_i, pitch_i = drag_look(driver, page, 120, 60)
    checks.check("inverted drag: same turn, vertical reversed (first person)",
                 abs(yaw_i - yaw_n) < 1.5 and 15 < yaw_i < 21 and -12 < pitch_i < -6 and 6 < pitch_n < 12,
                 f"normal yaw {yaw_n:.1f} pitch {pitch_n:.1f}; inverted yaw {yaw_i:.1f} pitch {pitch_i:.1f}")
    moved = captured_vertical(driver, page)
    checks.check("inverted captured mouse: moving down looks up (synthetic events; manual check still needed)",
                 moved is not None and moved[1] < -3 and abs(moved[0]) < 2,
                 f"yaw {moved[0]:.1f}, pitch {moved[1]:.1f}" if moved else "pointer lock refused")

    # Picking uses absolute coordinates: unchanged by the preference.
    focus_view(driver, page)
    face(driver, page, nearest_rack_yaw(page, site, "Rack A5"))
    driver.press("x")
    a5 = {r["name"]: r for r in site["records"]}["Rack A5"]["recordId"]
    p = page.eval(f"VRHEDemoPage.test.project({json.dumps(a5)})")
    driver.mouse("mouseMoved", p["clientX"], p["clientY"])
    time.sleep(0.4)
    hovered = state(page)["hoveredRecordId"]
    driver.click(p["clientX"], p["clientY"])
    checks.check("with inversion on, pointing and clicking still pick the rack under the pointer",
                 hovered == a5 and snap(page)["selected"] == a5, f"hovered {hovered[:12]}, selected {snap(page)['selected'][:12]}")

    # Q/E/X unchanged.
    st0 = state(page)
    driver.hold(["q"], 0.6)
    st1 = state(page)
    driver.hold(["e"], 1.2)
    st2 = state(page)
    drag_look(driver, page, 0, 60)
    before_x = state(page)
    driver.press("x")
    st3 = state(page)
    checks.check("with inversion on, Q raises, E lowers and X restores height and a level view",
                 st1["heightOffset"] - st0["heightOffset"] > 0.25 and st2["heightOffset"] < st1["heightOffset"] - 0.4 and
                 abs(before_x["pitch"]) > 3 and abs(st3["heightOffset"]) < 1e-3 and abs(st3["pitch"]) < 1e-3,
                 f"Q +{st1['heightOffset'] - st0['heightOffset']:.2f} m, E to {st2['heightOffset']:.2f} m, "
                 f"X from pitch {before_x['pitch']:.1f} to {st3['pitch']:.3f}")

    # Third person: orbit pitch reverses, orbit yaw and wheel zoom do not.
    driver.press("v")
    time.sleep(1.2)
    driver.press("x")
    yaw_t, pitch_t = drag_look(driver, page, 100, 60)
    st0 = state(page)
    driver.wheel(*canvas_center(page), 300)
    st1 = state(page)
    checks.check("inverted third-person orbit: same horizontal orbit, vertical reversed",
                 st0["view"] == "third" and 12 < yaw_t < 18 and -12 < pitch_t < -6, f"yaw {yaw_t:.1f}, pitch {pitch_t:.1f}")
    checks.check("with inversion on, the mouse wheel still zooms out", st1["orbitDistance"] > st0["orbitDistance"] + 0.5,
                 f"{st0['orbitDistance']:.2f} -> {st1['orbitDistance']:.2f} m")
    driver.wheel(*canvas_center(page), -300)
    driver.press("x")
    driver.press("v")
    time.sleep(0.5)

    # A panel still blocks movement.
    driver.press("h")
    st0 = state(page)
    driver.hold(["w"], 0.5)
    st1 = state(page)
    driver.press("Escape")
    checks.check("with inversion on, W does nothing while Help is open", dist(st0["feet"], st1["feet"]) < 1e-4)


def check_inversion_persists(page, driver, checks, when):
    s = snap(page)
    prefs = stored_prefs(page) or {}
    checks.check(f"inversion still on after {when} (checkbox, page state, stored preference)",
                 s["invertMouseY"] and page.eval("document.getElementById('invert-mouse-y').checked") and
                 prefs.get("invertMouseY") is True, f"{prefs}")
    focus_view(driver, page)
    driver.press("x")
    yaw, pitch = drag_look(driver, page, 120, 60)
    driver.press("x")
    checks.check(f"after {when}, a drag down still looks up (inverted)", 15 < yaw < 21 and -12 < pitch < -6,
                 f"yaw {yaw:.1f}, pitch {pitch:.1f}")


def reload_page(page):
    page.call("Page.reload", {"ignoreCache": True})
    time.sleep(1.0)
    wait(lambda: page.eval("!!(window.VRHEDemoPage && VRHEDemoPage.test.snapshot().ready)"), 120, 0.5, "ready after reload")
    page.call("Emulation.setFocusEmulationEnabled", {"enabled": True})


def run_session_one(args, page, browser, driver, checks, site, results, downloads):
    rec = {r["name"]: r for r in site["records"]}
    a1, b1 = rec["Rack A1"], rec["Rack B1"]
    s = snap(page)
    checks.check("page ready with LOCAL DEMO DATA badge",
                 s["ready"] and page.eval("document.querySelector('.badge').textContent") == "LOCAL DEMO DATA")
    checks.check("canvas renders at 1280x720", s["canvas"]["width"] == 1280 and s["canvas"]["height"] == 720,
                 f"{s['canvas']}")
    wait(lambda: snap(page)["hud"], 5, what="HUD")
    hud = page.eval("document.getElementById('hud').textContent")
    checks.check("HUD shows canvas pixels and fps", "1280x720 px" in hud and "fps" in hud, hud)
    checks.check("served data/site.json is the committed site definition",
                 http_json(DEMO_URL + "data/site.json") == site)
    checks.check("site.json IDs unchanged in the running build",
                 page.eval("VRHEDemoPage.test.snapshot().storageKey") == "vrhe.demo.records.v2." + site["siteId"])
    checks.check("build-info.json is served and labelled", bool(http_json(DEMO_URL + "data/build-info.json").get("label")))
    covered = snap(page)["viewCovered"]
    checks.check("nothing covers the 3D view once ready (clicks reach the canvas)", covered == "", covered or "clear")
    checks.check("loading and error overlays are gone once ready",
                 not page.eval("['loading', 'error'].some(id => document.getElementById(id).getClientRects().length > 0)"))

    # Focus: the first click on the view only gives it focus.
    st0 = state(page)
    cx, cy = canvas_center(page)
    page.eval("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
    time.sleep(0.2)
    checks.check("input gate closed while the view lacks focus", not snap(page)["gate"])
    driver.press("w")
    st_blur = state(page)
    checks.check("keys ignored while the view lacks focus", dist(st0["feet"], st_blur["feet"]) < 0.01)
    driver.click(cx, cy)
    s = snap(page)
    checks.check("first click focuses the view without selecting", s["gate"] and s["selected"] == "",
                 f"gate={s['gate']} selected={s['selected']!r}")

    # Movement near the spawn point, where the next 1.8 m ahead are clear.
    st0 = state(page)
    yaw = st0["viewYaw"]
    fwd = (math.sin(math.radians(yaw)), math.cos(math.radians(yaw)))
    right = (math.cos(math.radians(yaw)), -math.sin(math.radians(yaw)))

    def along(a, b, axis):
        return (b["feet"][0] - a["feet"][0]) * axis[0] + (b["feet"][2] - a["feet"][2]) * axis[1]

    driver.hold(["w"], 0.6)
    st1 = state(page)
    walk = along(st0, st1, fwd)
    checks.check("W moves forward (about 1.3 m/s)", 0.6 < walk < 1.0, f"{walk:.2f} m in 0.6 s")
    driver.hold(["s"], 0.6)
    st2 = state(page)
    checks.check("S moves back", along(st1, st2, fwd) < -0.6, f"{along(st1, st2, fwd):.2f} m")
    driver.hold(["Shift", "w"], 0.6)
    st3 = state(page)
    fast = along(st2, st3, fwd)
    checks.check("Shift doubles the speed (about 2.6 m/s)", 1.7 < fast / max(walk, 1e-3) < 2.3,
                 f"{fast:.2f} m vs {walk:.2f} m")
    driver.hold(["Shift", "s"], 0.6)
    st4 = state(page)
    driver.hold(["d"], 0.6)
    st5 = state(page)
    checks.check("D steps right", along(st4, st5, right) > 0.6, f"{along(st4, st5, right):.2f} m")
    driver.hold(["a"], 0.6)
    st6 = state(page)
    checks.check("A steps left", along(st5, st6, right) < -0.6, f"{along(st5, st6, right):.2f} m")
    driver.hold(["ArrowUp"], 0.6)
    st7 = state(page)
    checks.check("Up arrow moves forward", along(st6, st7, fwd) > 0.6, f"{along(st6, st7, fwd):.2f} m")
    driver.hold(["ArrowDown"], 0.6)
    st8 = state(page)
    checks.check("Down arrow moves back", along(st7, st8, fwd) < -0.6, f"{along(st7, st8, fwd):.2f} m")
    # D022: Left/Right arrows match A/D (step sideways, no turning). Same 0.6 s excursions as D/A above.
    driver.hold(["ArrowRight"], 0.6)
    st9 = state(page)
    side, turned = along(st8, st9, right), angle_delta(st8["viewYaw"], st9["viewYaw"])
    checks.check("Right arrow steps right like D, without turning", side > 0.6 and abs(turned) < 1.0,
                 f"{side:.2f} m, yaw change {turned:.1f} deg")
    driver.hold(["ArrowLeft"], 0.6)
    st10 = state(page)
    side, turned = along(st9, st10, right), angle_delta(st9["viewYaw"], st10["viewYaw"])
    checks.check("Left arrow steps left like A, without turning", side < -0.6 and abs(turned) < 1.0,
                 f"{side:.2f} m, yaw change {turned:.1f} deg")
    pace_move = pacing(page, "first.moving (W held 2.5 s, sliding along a rack)", lambda: driver.hold(["w"], 2.5))
    st11 = state(page)
    # Hollow if nothing moved: require a real walk that ends outside rack A4's footprint.
    moved = dist(st10["feet"], st11["feet"])
    checks.check("racks stop the walker (proxy collision)",
                 moved > 1.0 and not (-1.9 - 0.2 < st11["feet"][0] < 1.18 + 0.2 and -1.7 - 0.2 < st11["feet"][2] < -0.7 + 0.2),
                 f"walked {moved:.2f} m, feet {[round(v, 2) for v in st11['feet']]}")

    # Height and reset.
    st0 = state(page)
    pace_height = pacing(page, "first.height (Q held 1 s)", lambda: driver.hold(["q"], 1.0))
    st1 = state(page)
    checks.check("Q raises the camera", 0.45 < st1["heightOffset"] - st0["heightOffset"] < 0.75,
                 f"+{st1['heightOffset'] - st0['heightOffset']:.2f} m, eye {st1['eyeHeight']:.2f} m")
    driver.hold(["e"], 2.0)
    st2 = state(page)
    checks.check("E lowers the camera", st2["heightOffset"] < -0.4, f"{st2['heightOffset']:.2f} m")

    # Drag look.
    st0 = state(page)
    pace_look = pacing(page, "first.looking (drag)", lambda: driver.drag(cx, cy, 160, 60, 30, 1.2))
    st1 = state(page)
    dyaw = angle_delta(st0["viewYaw"], st1["viewYaw"])
    dpitch = st1["pitch"] - st0["pitch"]
    checks.check("drag right/down turns right and looks down (0.15 deg/px)", 18 < dyaw < 30 and 6 < dpitch < 12,
                 f"yaw {dyaw:.1f}, pitch {dpitch:.1f}")
    checks.check("a drag does not select", snap(page)["selected"] == "")
    before_x = state(page)
    driver.press("x")
    st2 = state(page)
    # Only meaningful if height and pitch were away from normal before X.
    checks.check("X restores normal height and a level view (first person)",
                 abs(before_x["heightOffset"]) > 0.1 and abs(before_x["pitch"]) > 1 and
                 abs(st2["heightOffset"]) < 1e-3 and abs(st2["pitch"]) < 1e-3 and abs(st2["eyeHeight"] - 1.6) < 0.02,
                 f"before offset {before_x['heightOffset']:.2f}, pitch {before_x['pitch']:.1f}; "
                 f"after offset {st2['heightOffset']:.3f}, pitch {st2['pitch']:.3f}, eye {st2['eyeHeight']:.3f}")

    # Select A1 with the mouse: walk to the front aisle facing A1, hover, click, right-click.
    walk_to(driver, page, [(2.3, -2.45), (-1.6, -2.45)])
    face(driver, page, 0.0)
    driver.press("x")
    p = page.eval(f"VRHEDemoPage.test.project({json.dumps(a1['recordId'])})")
    checks.check("Rack A1 is straight ahead from the front aisle", p and p["visible"], f"{p}")
    driver.mouse("mouseMoved", p["clientX"], p["clientY"])
    time.sleep(0.4)
    st = state(page)
    checks.check("hovering A1 highlights it (white outline)", st["hoveredRecordId"] == a1["recordId"], st["hoveredRecordId"])
    driver.click(p["clientX"], p["clientY"])
    s = snap(page)
    checks.check("click selects A1 (cyan outline, label)", s["selected"] == a1["recordId"] and s["tagVisible"],
                 f"selected={s['selected']} tag={s['tagVisible']}")
    driver.click(p["clientX"], p["clientY"], "right")
    s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="record panel")
    rec_a = s["record"]
    checks.check("right-click opens A1's record with name and stable ID",
                 rec_a["recordId"] == a1["recordId"] and rec_a["name"] == "Rack A1" and
                 rec_a["anchorIds"] == [site["anchors"][0]["anchorId"]],
                 f"{rec_a['recordId']} / {rec_a['anchorIds']}")
    checks.check("record shows original demo text before any edit", rec_a["revision"] == 0 and rec_a["source"] == "seed")
    checks.check("panel open closes the input gate", not s["gate"] and s["typing"], f"gate={s['gate']} typing={s['typing']}")

    # Typing must not move the view.
    st0 = state(page)
    note_a = "Edited A1 note from the automated check: www aaa sss ddd qqq eee xxx vvv " + str(random.randint(1000, 9999))
    page.eval("document.getElementById('rec-description').select()")
    pace_typing = pacing(page, "panel.typing", lambda: driver.type_text(note_a, 0.02))
    driver.hold(["w"], 0.8)  # a held key inside the text box
    page.eval("(() => { const t = document.getElementById('rec-description'); t.value = t.value.replace(/w+$/, ''); t.dispatchEvent(new Event('input')); })()")
    st1 = state(page)
    checks.check("typing W A S D Q E X V in the description moves nothing",
                 dist(st0["feet"], st1["feet"]) < 1e-4 and st0["viewYaw"] == st1["viewYaw"] and
                 st0["pitch"] == st1["pitch"] and st0["heightOffset"] == st1["heightOffset"] and st0["view"] == st1["view"],
                 f"moved {dist(st0['feet'], st1['feet']):.5f} m, view {st0['view']}->{st1['view']}")
    checks.check("typed text arrived in the editor", snap(page)["editorText"] == note_a)

    driver.press("Enter", modifiers=2)  # Ctrl+Enter
    s = snap(page)
    checks.check("Ctrl+Enter saves A1 (version 1)", s["lastSave"] and s["lastSave"]["status"] == "Saved" and
                 s["record"]["revision"] == 1, f"{s['lastSave']}")
    raw = json.loads(page.eval("VRHEDemoPage.test.storedRaw()"))
    entries = {e["recordId"]: e for e in raw["rackNotes"]}
    checks.check("storage holds A1's text under its recordId only",
                 entries.get(a1["recordId"], {}).get("description") == note_a and b1["recordId"] not in entries,
                 f"keys {sorted(entries)}")
    driver.press("Escape")
    s = snap(page)
    checks.check("Esc closes the panel and returns focus to the view",
                 s["panel"] == "" and s["activeElement"] == "unity-canvas" and s["gate"], f"{s['activeElement']} gate={s['gate']}")
    # Step sideways along the open front aisle (backwards would meet the room boundary at z = -3).
    st0 = state(page)
    driver.hold(["d"], 0.6)
    st1 = state(page)
    checks.check("movement works again after closing the panel", dist(st0["feet"], st1["feet"]) > 0.6,
                 f"{dist(st0['feet'], st1['feet']):.2f} m in 0.6 s")
    driver.hold(["a"], 0.6)

    # B1: walk round to the back aisle, click it, then open it with the Enter key.
    walk_to(driver, page, [(-1.6, -2.45), (2.4, -2.45), (2.4, 2.3), (-1.6, 2.3)])
    face(driver, page, 180.0)
    driver.press("x")
    p = page.eval(f"VRHEDemoPage.test.project({json.dumps(b1['recordId'])})")
    checks.check("Rack B1 is straight ahead from the back aisle", p and p["visible"], f"{p}")
    driver.mouse("mouseMoved", p["clientX"], p["clientY"])
    time.sleep(0.4)
    checks.check("hovering B1 highlights it", state(page)["hoveredRecordId"] == b1["recordId"])
    driver.click(p["clientX"], p["clientY"])
    checks.check("click selects B1 (a second, different item)", snap(page)["selected"] == b1["recordId"])
    driver.press("Enter")
    s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="B1 record")
    checks.check("Enter opens the selected record (B1)", s["record"]["recordId"] == b1["recordId"])
    checks.check("B1 still has its own original text", s["record"]["description"] == b1["description"] and
                 s["record"]["revision"] == 0)
    note_b = "B1 note " + str(random.randint(1000, 9999))
    page.eval("document.getElementById('rec-description').select()")
    driver.type_text(note_b, 0.02)
    driver.click_element("rec-save")
    s = snap(page)
    checks.check("Save button saves B1", s["lastSave"]["status"] == "Saved" and s["record"]["revision"] == 1)
    driver.press("Escape")
    driver.press("l")
    wait(lambda: snap(page)["panel"] == "list", 5, what="list")
    driver.click_selector(f'#list-items > li[data-record="{a1["recordId"]}"] button[data-act=open]')
    s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="A1 record")
    checks.check("reopening A1 shows A1's saved text, not B1's", s["record"]["description"] == note_a and
                 s["record"]["recordId"] == a1["recordId"])

    # Discard question for unsaved text.
    driver.type_text(" unsaved", 0.02)
    driver.press("Escape")
    s = snap(page)
    checks.check("Esc with unsaved text asks before discarding", s["discardVisible"] and s["panel"] == "record")
    driver.press("Escape")  # = keep editing
    s = snap(page)
    checks.check("Esc on the question keeps editing", not s["discardVisible"] and s["panel"] == "record" and s["dirty"])
    driver.press("Escape")
    driver.click_element("rec-discard-yes")
    s = snap(page)
    stored = json.loads(page.eval("VRHEDemoPage.test.storedRaw()"))
    a_text = {e["recordId"]: e for e in stored["rackNotes"]}[a1["recordId"]]["description"]
    checks.check("discarding closes without saving", s["panel"] == "" and a_text == note_a)

    # Equipment list route for non-gamers: "Show" selects an item and turns the view to it.
    select_via_list(driver, page, "Rack B3")
    p = page.eval(f"VRHEDemoPage.test.project({json.dumps(rec['Rack B3']['recordId'])})")
    checks.check("Equipment list 'Show' selects B3 and turns the view toward it",
                 snap(page)["selected"] == rec["Rack B3"]["recordId"] and p["visible"] and abs(p["unityX"] - 640) < 60,
                 f"projected x {p['unityX']:.0f} of 1280")

    # Stage 2: equipment records, descriptions and description names (D037-D039, D041).
    authoring = run_authoring_checks(page, driver, checks, site)

    # Reload keeps both edits.
    page.call("Page.reload", {"ignoreCache": True})
    time.sleep(1.0)
    wait(lambda: page.eval("!!(window.VRHEDemoPage && VRHEDemoPage.test.snapshot().ready)"), 120, 0.5, "ready after reload")
    page.call("Emulation.setFocusEmulationEnabled", {"enabled": True})
    for name, note in (("Rack A1", note_a), ("Rack B1", note_b)):
        r = rec[name]
        page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsOpenRecord', JSON.stringify({{recordId: {json.dumps(r['recordId'])}, how: 'check'}}))")
        s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what=f"{name} after reload")
        checks.check(f"page reload keeps {name}'s saved text", s["record"]["description"] == note and s["record"]["revision"] == 1)
        driver.press("Escape")
    check_authoring_persisted(page, driver, checks, authoring, "a page reload")

    # Export.
    driver.click_selector("button[data-action=data]")
    driver.click_element("data-export")
    exported = wait(lambda: page.eval("VRHEDemoPage.test.lastExportJson()"), 5, what="export")
    export = json.loads(exported)
    by_id = {r["recordId"]: r for r in export["records"]}
    checks.check("export is labelled local demo data with schema", export["schema"] == "vrhe.demo.records-export" and
                 export["notice"].startswith("LOCAL DEMO DATA") and export["origin"] == DEMO_URL.rstrip("/"))
    checks.check("export carries both edits and untouched seeds",
                 by_id[a1["recordId"]]["description"] == note_a and by_id[b1["recordId"]]["description"] == note_b and
                 by_id[rec["Rack A2"]["recordId"]]["source"] == "seed")
    name = snap(page)["lastExport"]
    downloaded = wait(lambda: os.path.isfile(os.path.join(downloads, name)) and os.path.join(downloads, name), 10,
                      what="downloaded file")
    with open(downloaded, encoding="utf-8") as f:
        checks.check("browser download contains the same JSON", json.load(f) == export, downloaded)
    session_dir = os.path.join(results, snap(page)["session"])
    checks.check("export copy reached the local results folder", os.path.isfile(os.path.join(session_dir, name)))
    check_authoring_export(export, authoring, checks)
    driver.press("Escape")

    # Third person, orbit, zoom and X, on the open floor right of the racks facing the front.
    walk_to(driver, page, [(2.4, 2.3), (3.3, 1.0), (3.3, -0.3)])
    face(driver, page, 180.0)
    focus_view(driver, page)
    driver.press("v")
    time.sleep(1.5)
    st0 = state(page)
    checks.check("V switches to third person behind the avatar",
                 st0["view"] == "third" and abs(st0["cameraDistance"] - st0["orbitDistance"]) < 0.05,
                 f"view {st0['view']}, camera {st0['cameraDistance']:.2f} m / {st0['orbitDistance']:.2f} m")
    pace_orbit = pacing(page, "third.orbiting (drag)", lambda: driver.drag(cx, cy, 300, -40, 40, 1.5))
    st1 = state(page)
    orbit = angle_delta(st0["viewYaw"], st1["viewYaw"])
    checks.check("drag orbits the camera around the avatar without turning it",
                 abs(orbit) > 30 and abs(angle_delta(st0["bodyYaw"], st1["bodyYaw"])) < 0.01,
                 f"orbit {orbit:.1f} deg, body {st0['bodyYaw']:.1f}->{st1['bodyYaw']:.1f}")
    driver.hold(["q"], 0.6)
    driver.wheel(cx, cy, 300)
    time.sleep(1.5)
    st2 = state(page)
    checks.check("mouse wheel zooms out", st2["orbitDistance"] > st1["orbitDistance"] + 0.5,
                 f"{st1['orbitDistance']:.2f} -> {st2['orbitDistance']:.2f} m")
    driver.press("x")
    st3 = state(page)
    checks.check("X in third person: normal height, level view, back behind the avatar",
                 abs(st2["heightOffset"]) > 0.1 and abs(angle_delta(st2["viewYaw"], st2["bodyYaw"])) > 10 and
                 abs(st3["heightOffset"]) < 1e-3 and abs(st3["pitch"]) < 1e-3 and
                 abs(angle_delta(st3["viewYaw"], st3["bodyYaw"])) < 0.01 and
                 abs(angle_delta(st1["bodyYaw"], st3["bodyYaw"])) < 0.01,
                 f"offset {st3['heightOffset']:.3f}, pitch {st3['pitch']:.3f}, yaw {st3['viewYaw']:.1f}/{st3['bodyYaw']:.1f}")
    pace_third_move = pacing(page, "third.moving (W held 2 s)", lambda: driver.hold(["w"], 2.0))
    st4 = state(page)
    checks.check("third-person movement walks the avatar", dist(st3["feet"], st4["feet"]) > 1.0)
    driver.hold(["s"], 2.0)
    driver.press("v")
    st5 = state(page)
    checks.check("V returns to first person", st5["view"] == "first" and st5["cameraDistance"] == 0)

    # Idle and panel pacing.
    focus_view(driver, page)
    pace_idle = pacing(page, "first.idle (3 s)", lambda: time.sleep(3.0))
    driver.press("h")
    pace_panel = pacing(page, "panel.help open (2 s)", lambda: time.sleep(2.0))
    driver.press("Escape")

    # Pointer lock (game-style look). CDP mouse events under lock are a best-effort check.
    focus_view(driver, page)
    driver.press("m")
    time.sleep(0.6)
    s = snap(page)
    locked = s["locked"]
    checks.check("M captures the mouse (pointer lock) and shows the crosshair", locked and s["crosshairVisible"],
                 f"locked={locked}")
    if locked:
        st0 = state(page)
        for i in range(10):
            driver.mouse("mouseMoved", cx + 10 * (i + 1), cy)
            time.sleep(0.03)
        time.sleep(0.3)
        st1 = state(page)
        checks.check("captured mouse motion turns the view (synthetic events; manual check still needed)",
                     abs(angle_delta(st0["viewYaw"], st1["viewYaw"])) > 1, f"{angle_delta(st0['viewYaw'], st1['viewYaw']):.1f} deg")
        driver.press("Escape")
        time.sleep(0.4)
        checks.check("Esc releases the mouse", not snap(page)["locked"])
        moved = captured_vertical(driver, page)
        checks.check("captured mouse moving down looks down with inversion off (synthetic events)",
                     moved is not None and moved[1] > 3 and abs(moved[0]) < 2,
                     f"yaw {moved[0]:.1f}, pitch {moved[1]:.1f}" if moved else "pointer lock refused")

    # Optional mouse Y inversion (D036), then a reload with it on.
    run_inversion_checks(page, driver, checks, site)
    reload_page(page)
    check_inversion_persists(page, driver, checks, "a page reload")
    return {"notes": {"A1": note_a, "B1": note_b}, "authoring": authoring,
            "pacing": [x for x in (pace_idle, pace_move, pace_height, pace_look, pace_orbit, pace_third_move,
                                   pace_typing, pace_panel) if x] + authoring["pacing"]}


def run_inversion_session_two(page, driver, checks):
    """After a browser restart: the preference persists; turning it off restores normal look; older and
    unreadable stored preferences fall back to defaults without breaking the page."""
    check_inversion_persists(page, driver, checks, "closing and restarting the browser")
    checks.check("unticking the checkbox turns inversion off", set_invert(driver, page, False))
    focus_view(driver, page)
    driver.press("x")
    yaw, pitch = drag_look(driver, page, 120, 60)
    driver.press("x")
    prefs = stored_prefs(page) or {}
    checks.check("inversion off again: a drag down looks down, and off is saved",
                 15 < yaw < 21 and 6 < pitch < 12 and prefs.get("invertMouseY") is False,
                 f"yaw {yaw:.1f}, pitch {pitch:.1f}, stored {prefs}")
    page.eval(f"localStorage.setItem({json.dumps(PREFS_KEY)}, JSON.stringify({{lookSpeed: 1.5}}))")
    reload_page(page)
    s = snap(page)
    checks.check("an older stored preference without the inversion field loads as normal look, keeping look speed",
                 not s["invertMouseY"] and abs(s["lookSpeed"] - 1.5) < 1e-6, f"invert {s['invertMouseY']}, speed {s['lookSpeed']}")
    page.eval(f"localStorage.setItem({json.dumps(PREFS_KEY)}, '{{not json')")
    reload_page(page)
    s = snap(page)
    checks.check("an unreadable stored preference loads the defaults and the demo still starts",
                 s["ready"] and not s["invertMouseY"] and abs(s["lookSpeed"] - 1.0) < 1e-6 and not s["error"],
                 f"invert {s['invertMouseY']}, speed {s['lookSpeed']}, error {s['error']!r}")


def run_session_two(page, driver, checks, site, notes, authoring):
    run_inversion_session_two(page, driver, checks)
    check_authoring_persisted(page, driver, checks, authoring, "closing and restarting the browser")
    rec = {r["name"]: r for r in site["records"]}
    for name, key in (("Rack A1", "A1"), ("Rack B1", "B1")):
        r = rec[name]
        page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsOpenRecord', JSON.stringify({{recordId: {json.dumps(r['recordId'])}, how: 'check'}}))")
        s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what=f"{name} after relaunch")
        checks.check(f"browser relaunch with the same profile keeps {name}'s text",
                     s["record"]["description"] == notes[key] and s["record"]["revision"] == 1)
        driver.press("Escape")
    other = rec["Rack A2"]
    page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsOpenRecord', JSON.stringify({{recordId: {json.dumps(other['recordId'])}, how: 'check'}}))")
    s = wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="A2")
    checks.check("an unedited rack still shows its original text", s["record"]["description"] == other["description"])
    driver.press("Escape")
    # Reset demo data through the page.
    driver.click_selector("button[data-action=data]")
    driver.click_element("data-reset")
    driver.click_element("data-reset-yes")
    time.sleep(0.3)
    check_reset_v2(page, checks, site)
    driver.press("Escape")


# ------------------------------------------------------------------------------- stage 2: equipment and names
# Racks hold equipment records with RU ranges (D037); each item starts with one empty, unnamed
# description and gains more through Add description (D038); description names come from one shared,
# editable list (D039); a name leaves the list only through a replacement that keeps every
# description's identity and text (D041). Everything below goes through the page with real clicks
# and keys, except: choosing an entry in a native drop-down (CDP cannot drive the browser's own
# pop-up list, so the value is set and a change event sent), placing the caret, and the checks that
# deliberately bypass the page to prove the store enforces a rule by itself.
V2_PREFIX = "vrhe.demo.records.v2."
V1_PREFIX = "vrhe.demo.records.v1."
FILLER_PREFIX = "vrhe.check.filler."
UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def is_id(value, prefix):
    return bool(re.fullmatch(prefix + "-" + UUID, value or ""))


def visible(page, element_id):
    return page.eval(f"(() => {{ const n = document.getElementById({json.dumps(element_id)});"
                     " return !!n && n.getClientRects().length > 0; })()")


def wait_panel(page, name, what=None):
    return wait(lambda: (lambda s: s if s["panel"] == name else None)(snap(page)), 5, what=what or f"{name} panel")


def stored_doc(page):
    raw = page.eval("VRHEDemoPage.test.storedRaw()")
    return json.loads(raw) if raw else None


def stored_item(doc, equipment_id):
    return next((e for e in (doc or {}).get("equipment", []) if e["equipmentId"] == equipment_id), None)


def stored_label(doc, label_id):
    return next((l for l in (doc or {}).get("labels", []) if l["labelId"] == label_id), None)


def triples(descriptions):
    return [(d["descriptionId"], d["labelId"], d["text"]) for d in descriptions]


def catalog_label(page, label_id):
    return next((l for l in (snap(page)["catalog"] or {}).get("labels", []) if l["labelId"] == label_id), None)


def same_pose(a, b):
    return (dist(a["feet"], b["feet"]) < 1e-4 and a["viewYaw"] == b["viewYaw"] and a["pitch"] == b["pitch"] and
            a["heightOffset"] == b["heightOffset"] and a["view"] == b["view"])


def set_field(driver, page, element_id, text):
    """Real click into a text or number field, select its content, then type (Backspace for empty)."""
    driver.click_element(element_id)
    page.eval(f"document.getElementById({json.dumps(element_id)}).select()")
    if text:
        driver.type_text(text, 0.02)
    else:
        driver.press("Backspace")


def open_list(driver, page):
    if snap(page)["panel"] != "list":
        driver.click_selector("button[data-action=list]")
    wait_panel(page, "list")


def open_rack(driver, page, rack):
    """Equipment list > Open rack (real clicks); returns the snapshot with the rack panel open."""
    open_list(driver, page)
    driver.click_selector(f'#list-items > li[data-record="{rack["recordId"]}"] button[data-act=open]')
    return wait(lambda: (lambda s: s if s["panel"] == "record" and s["record"] and
                         s["record"]["recordId"] == rack["recordId"] else None)(snap(page)), 5, what=rack["name"])


def open_item_from_list(driver, page, equipment_id):
    open_list(driver, page)
    driver.click_selector(f'#list-items li[data-equipment="{equipment_id}"] button[data-act=open-eq]')
    return wait(lambda: (lambda s: s if s["panel"] == "equipment" and s["equipment"] and
                         s["equipment"]["equipmentId"] == equipment_id else None)(snap(page)), 5, what="equipment item")


def open_names(driver, page):
    if snap(page)["panel"] != "names":
        driver.click_selector("button[data-action=names]")
    return wait_panel(page, "names")


def add_equipment(driver, page, name, start, end=""):
    set_field(driver, page, "eq-new-name", name)
    set_field(driver, page, "eq-new-start", start)
    set_field(driver, page, "eq-new-end", end)
    driver.click_element("eq-add-btn")
    return snap(page)


def card(i, what=""):
    return f"#eq-descriptions > li:nth-child({i + 1}) {what}".strip()


def choose_name(page, i, value):
    """Pick an entry in description i's name list (set programmatically; see the section comment)."""
    page.eval(f"(() => {{ const s = document.querySelector({json.dumps(card(i, 'select'))});"
              f" s.value = {json.dumps(value)}; s.dispatchEvent(new Event('change', {{bubbles: true}})); }})()")


def in_clear_view(page, selector):
    """Whether the element lies inside its panel's visible area, above any sticky footer, and is
    what a click at its centre would reach; also whether it has focus."""
    return page.eval(f"""(() => {{
      const e = document.querySelector({json.dumps(selector)}); if (!e) return {{ok: false, focused: false, why: 'missing'}};
      const panel = e.closest('.panel'), r = e.getBoundingClientRect(), p = panel.getBoundingClientRect();
      const foot = panel.querySelector('.panel-foot'), limit = foot ? foot.getBoundingClientRect().top : p.bottom;
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return {{ok: r.top >= p.top && r.bottom <= limit + 0.5 && !!hit && (hit === e || e.contains(hit)),
               focused: document.activeElement === e, why: `top ${{Math.round(r.top)}} bottom ${{Math.round(r.bottom)}}`
               + ` footer ${{Math.round(limit)}} hit ${{hit ? (hit.id || hit.className || hit.tagName) : 'none'}}`}};
    }})()""")


def focus_spot(page):
    """[description index, element, caret start, caret end] for focus inside a description card, else None."""
    return page.eval("(() => { const a = document.activeElement; const li = a && a.closest && a.closest('#eq-descriptions > li');"
                     " return li ? [Array.prototype.indexOf.call(li.parentNode.children, li), a.tagName,"
                     " a.tagName === 'TEXTAREA' ? a.selectionStart : null, a.tagName === 'TEXTAREA' ? a.selectionEnd : null] : null; })()")


def type_description(driver, page, i, text):
    """Real click into description i's text box, caret to the end, then real typing."""
    driver.click_selector(card(i, "textarea"))
    page.eval(f"(() => {{ const t = document.querySelector({json.dumps(card(i, 'textarea'))});"
              " t.setSelectionRange(t.value.length, t.value.length); })()")
    driver.type_text(text, 0.02)


def add_description(driver, page):
    driver.click_element("eq-add-desc")
    return len(snap(page)["draft"]["descriptions"])


def save_item(driver, page):
    driver.press("Enter", modifiers=2)  # Ctrl+Enter
    return snap(page)


def authoring_raw(page, payload):
    """Send one JsAuthoring command straight to Unity, bypassing the page's own checks."""
    request_id = "check-" + str(random.randint(100000, 999999))
    payload = dict(payload, requestId=request_id)
    page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsAuthoring', {json.dumps(json.dumps(payload))})")
    return page.eval(f"VRHEDemoPage.test.takeReply({json.dumps(request_id)})")


def fill_storage(page):
    """Fill this origin's localStorage until the browser refuses even one more character."""
    return page.eval("(() => { let n = 0, size = 1 << 20, chars = 0;"
                     f" while (size >= 1) {{ try {{ localStorage.setItem({json.dumps(FILLER_PREFIX)} + n, 'x'.repeat(size));"
                     " n++; chars += size; } catch (e) { size = Math.floor(size / 2); } }"
                     " return {keys: n, chars: chars}; })()")


def free_storage(page):
    return page.eval("(() => { const keys = []; for (let i = 0; i < localStorage.length; i++) {"
                     f" const k = localStorage.key(i); if (k.startsWith({json.dumps(FILLER_PREFIX)})) keys.push(k); }}"
                     " keys.forEach(k => localStorage.removeItem(k)); return keys.length; })()")


def run_authoring_checks(page, driver, checks, site):
    """Stage 2 in one session. Returns what the reload, restart and export checks compare against."""
    rec = {r["name"]: r for r in site["records"]}
    a4, b2 = rec["Rack A4"], rec["Rack B2"]
    starter = {l["name"]: l["labelId"] for l in site["labels"]}
    serial, model, asset_tag = starter["Serial number"], starter["Model"], starter["Asset tag"]
    ctx = {"pacing": []}

    # --- Rack A4: bounds advice, a store refusal, then a 1U switch with one empty unnamed description.
    s = open_rack(driver, page, a4)
    checks.check("a rack panel shows its equipment list (empty) and the Add equipment form",
                 s["record"]["equipment"] == [] and visible(page, "eq-add") and s["record"]["rackUnits"] == 42,
                 f"{len(s['record']['equipment'])} items, {s['record']['rackUnits']} RU")
    raw0 = page.eval("VRHEDemoPage.test.storedRaw()")
    s = add_equipment(driver, page, "Synthetic switch SW-01", "43")
    checks.check("RU 43 in a 42 RU rack: flagged while typing, refused by the store, nothing written",
                 "use 1 to 42" in s["addCheck"] and s["lastAuthoring"]["status"] == "Invalid" and
                 s["panel"] == "record" and page.eval("VRHEDemoPage.test.storedRaw()") == raw0,
                 f"{s['lastAuthoring']['status']}: {s['addStatus']}")
    set_field(driver, page, "eq-new-start", "40")
    driver.press("Enter")  # Enter in the form adds; "to RU" left blank means the same unit
    s = wait_panel(page, "equipment", "new item editor")
    sw = s["equipment"]
    first = sw["descriptions"]
    checks.check("Add equipment opens the new item with exactly one empty, unnamed description",
                 sw["name"] == "Synthetic switch SW-01" and (sw["ruStart"], sw["ruEnd"]) == (40, 40) and
                 len(first) == 1 and first[0]["labelId"] == "" and first[0]["text"] == "" and sw["revision"] == 1,
                 f"{sw['name']} RU {sw['ruStart']}-{sw['ruEnd']}, {len(first)} description(s)")
    checks.check("equipment and description identities are their own prefixed UUIDs, linked to the rack",
                 is_id(sw["equipmentId"], "eq") and is_id(first[0]["descriptionId"], "dsc") and
                 sw["rackRecordId"] == a4["recordId"], f"{sw['equipmentId']} / {first[0]['descriptionId']}")
    ctx["SW"] = sw["equipmentId"]

    # One named, one unnamed and another named description; typing never moves the view.
    choose_name(page, 0, serial)
    type_description(driver, page, 0, "SYN-SW-0001")
    add_description(driver, page)
    uplinks = "Uplinks to the core www aaa sss ddd qqq eee xxx"
    st0 = state(page)
    ctx["pacing"].append(pacing(page, "panel.equipment typing", lambda: type_description(driver, page, 1, uplinks)))
    driver.hold(["w"], 0.6)  # a held key inside the text box types one "w"
    uplinks += "w"
    st1 = state(page)
    checks.check("typing W A S D Q E X in an equipment description moves nothing",
                 same_pose(st0, st1) and snap(page)["draft"]["descriptions"][1]["text"] == uplinks,
                 f"moved {dist(st0['feet'], st1['feet']):.5f} m")
    add_description(driver, page)
    choose_name(page, 2, model)
    type_description(driver, page, 2, "Synthetic 48-port switch")
    page.eval(f"document.querySelector({json.dumps(card(2, 'select'))}).focus()")
    st0 = state(page)
    driver.type_text("hlqx", 0.05)
    s = snap(page)
    st1 = state(page)
    checks.check("letters typed while a name list has focus open no panel and move nothing",
                 s["panel"] == "equipment" and s["draft"]["descriptions"][2]["labelId"] == model and same_pose(st0, st1),
                 f"panel {s['panel']}")
    n = add_description(driver, page)
    view = in_clear_view(page, card(n - 1, "textarea"))
    checks.check("Add description focuses the new text box and scrolls it into view above the Save row",
                 view["ok"] and view["focused"], view.get("why", ""))
    text_locked = page.eval(f"document.querySelector({json.dumps(card(0, 'button[data-act=remove]'))}).disabled")
    driver.click_selector(card(n - 1, "button[data-act=remove]"))
    s = snap(page)
    checks.check("Remove works on an empty description and is unavailable for one with text",
                 text_locked and len(s["draft"]["descriptions"]) == n - 1, f"{n} -> {len(s['draft']['descriptions'])}")
    before = focus_spot(page)
    s = save_item(driver, page)
    after = focus_spot(page)
    checks.check("after Ctrl+Enter the caret stays where it was, so typing carries on in the same description",
                 before is not None and before == after, f"{before} -> {after}")
    sw = s["equipment"]
    checks.check("Ctrl+Enter saves the item: one unnamed and two named descriptions, first ID kept",
                 s["lastAuthoring"]["status"] == "Saved" and sw["revision"] == 2 and
                 [(d["labelId"], d["text"]) for d in sw["descriptions"]] ==
                 [(serial, "SYN-SW-0001"), ("", uplinks), (model, "Synthetic 48-port switch")] and
                 sw["descriptions"][0]["descriptionId"] == first[0]["descriptionId"],
                 f"{s['lastAuthoring']['status']}: {s['eqStatus']}")

    # A 2U server at RU 20-21, after an overlap warning while typing.
    driver.click_element("eq-back")
    s = wait(lambda: (lambda x: x if x["panel"] == "record" and x["record"]["recordId"] == a4["recordId"] else None)(snap(page)),
             5, what="back to A4")
    checks.check("the item's back link returns to its rack, which lists it",
                 [e["equipmentId"] for e in s["record"]["equipment"]] == [ctx["SW"]])
    set_field(driver, page, "eq-new-name", "Synthetic server SRV-01")
    set_field(driver, page, "eq-new-start", "40")
    overlap_text = snap(page)["addCheck"]
    checks.check("a rack unit already in use is flagged while typing (front/rear is not recorded)",
                 "Shares rack units with Synthetic switch SW-01" in overlap_text and "front" in overlap_text, overlap_text)
    set_field(driver, page, "eq-new-start", "20")
    set_field(driver, page, "eq-new-end", "21")
    driver.click_element("eq-add-btn")
    s = wait(lambda: (lambda x: x if x["panel"] == "equipment" and x["equipment"]["equipmentId"] != ctx["SW"] else None)(snap(page)),
             5, what="server editor")
    srv = s["equipment"]
    checks.check("a 2U device is one record covering RU 20-21",
                 (srv["ruStart"], srv["ruEnd"]) == (20, 21) and len(srv["descriptions"]) == 1, f"RU {srv['ruStart']}-{srv['ruEnd']}")
    ctx["SRV"] = srv["equipmentId"]
    choose_name(page, 0, serial)
    type_description(driver, page, 0, "SYN-SRV-0002")
    driver.click_element("eq-save")
    doc = stored_doc(page)
    sw_doc, srv_doc = stored_item(doc, ctx["SW"]), stored_item(doc, ctx["SRV"])
    checks.check("the same name holds different text on each item (choosing a name copies nothing)",
                 (sw_doc["descriptions"][0]["labelId"], sw_doc["descriptions"][0]["text"]) == (serial, "SYN-SW-0001") and
                 (srv_doc["descriptions"][0]["labelId"], srv_doc["descriptions"][0]["text"]) == (serial, "SYN-SRV-0002"))
    checks.check("saving the server left the switch unchanged (record-local)",
                 sw_doc["revision"] == 2 and triples(sw_doc["descriptions"]) == triples(sw["descriptions"]))
    driver.click_element("eq-back")
    s = wait(lambda: (lambda x: x if x["panel"] == "record" and len(x["record"]["equipment"]) == 2 else None)(snap(page)),
             5, what="A4 with two items")
    checks.check("rack A4 lists both devices, top of the rack first",
                 [(e["name"], e["ruStart"], e["ruEnd"]) for e in s["record"]["equipment"]] ==
                 [("Synthetic switch SW-01", 40, 40), ("Synthetic server SRV-01", 20, 21)])
    driver.press("Escape")

    # --- The shared list: add a misspelt name, then use it on two items in two racks.
    open_names(driver, page)
    doc0 = stored_doc(page)
    ctx["pacing"].append(pacing(page, "panel.names typing", lambda: set_field(driver, page, "names-new", "Serail no")))
    driver.click_element("names-add")
    s = snap(page)
    typo = s["lastAuthoring"]["labelId"]
    doc1 = stored_doc(page)
    checks.check("Add name puts the name in the shared list and changes no equipment record",
                 s["lastAuthoring"]["status"] == "Saved" and is_id(typo, "lbl") and
                 [e["revision"] for e in doc0["equipment"]] == [e["revision"] for e in doc1["equipment"]] and
                 any(l["labelId"] == typo and not l["retired"] for l in s["catalog"]["labels"]), s["namesStatus"])
    driver.press("Escape")

    s = open_rack(driver, page, b2)
    add_equipment(driver, page, "Synthetic router RT-01", "10", "11")
    s = wait_panel(page, "equipment", "router editor")
    ctx["RT"] = s["equipment"]["equipmentId"]
    choose_name(page, 0, typo)
    type_description(driver, page, 0, "SYN-RT-0003")
    add_description(driver, page)
    choose_name(page, 1, serial)
    type_description(driver, page, 1, "RT-SERIAL-B")
    add_description(driver, page)
    choose_name(page, 2, "__new")
    form_shown = page.eval(f"document.querySelector({json.dumps(card(2, '.desc-new'))}).getClientRects().length > 0")
    driver.click_selector(card(2, ".desc-new input"))
    driver.type_text("Firmware version", 0.02)
    driver.click_selector(card(2, "button[data-act=new-add]"))
    s = snap(page)
    firmware = s["lastAuthoring"]["labelId"]
    doc = stored_doc(page)
    checks.check("'New name...' in a description adds the name and chooses it for that description only",
                 form_shown and s["lastAuthoring"]["status"] == "Saved" and s["draft"]["descriptions"][2]["labelId"] == firmware and
                 s["draft"]["descriptions"][0]["labelId"] == typo and stored_item(doc, ctx["SRV"])["revision"] == 2,
                 s["eqStatus"])
    type_description(driver, page, 2, "1.0.0-synthetic")
    # Clicking a blank part of the panel leaves the text box; a shortcut then asks before dropping the
    # unsaved changes, and Keep editing (Esc) goes back to the description that was being typed in.
    driver.click_selector("#equipment-title")
    driver.press("l")
    asked = snap(page)
    driver.press("Escape")
    back = in_clear_view(page, card(2, "textarea"))
    s = snap(page)
    checks.check("a shortcut with unsaved changes asks first; Keep editing returns to the description in use",
                 asked["confirmVisible"] and asked["panel"] == "equipment" and back["focused"] and back["ok"] and
                 not s["confirmVisible"] and s["draft"]["descriptions"][2]["text"] == "1.0.0-synthetic",
                 f"asked {asked['confirmVisible']}; {back.get('why', '')}")
    s = save_item(driver, page)
    checks.check("router saved with a misspelt name, Serial number and the new name",
                 s["lastAuthoring"]["status"] == "Saved" and
                 [(d["labelId"], d["text"]) for d in s["equipment"]["descriptions"]] ==
                 [(typo, "SYN-RT-0003"), (serial, "RT-SERIAL-B"), (firmware, "1.0.0-synthetic")], s["eqStatus"])
    driver.press("Escape")

    # Hierarchy in the Equipment list; opening an item selects its rack in the view.
    open_list(driver, page)
    listed = page.eval(f"Array.from(document.querySelectorAll('#list-items > li[data-record=\"{a4['recordId']}\"] .eq-sub li'))"
                       ".map(n => n.dataset.equipment)")
    s = open_item_from_list(driver, page, ctx["SW"])
    checks.check("the Equipment list shows each rack's items; Open opens the item and selects its rack",
                 listed == [ctx["SW"], ctx["SRV"]] and snap(page)["selected"] == a4["recordId"], f"listed {len(listed or [])}")
    add_description(driver, page)
    choose_name(page, 3, typo)
    type_description(driver, page, 3, "SW-OLD-77")
    s = save_item(driver, page)
    checks.check("switch saved with a fourth description under the misspelt name",
                 s["lastAuthoring"]["status"] == "Saved" and s["equipment"]["revision"] == 3)

    # --- Rename: a spelling fix reaches every description; no text or equipment record changes.
    before = stored_doc(page)
    open_names(driver, page)
    driver.click_selector(f'#names-list li[data-label="{typo}"] button[data-act=rename]')
    set_field(driver, page, "names-rename-input", "Serial no.")
    driver.click_selector("#names-list .name-form button[data-act=rename-go]")
    s = snap(page)
    after = stored_doc(page)
    label = stored_label(after, typo)
    unchanged = all(triples(stored_item(after, i)["descriptions"]) == triples(stored_item(before, i)["descriptions"]) and
                    stored_item(after, i)["revision"] == stored_item(before, i)["revision"] for i in (ctx["SW"], ctx["RT"]))
    checks.check("Rename fixes the spelling everywhere: same descriptions, same text, same item versions",
                 s["lastAuthoring"]["status"] == "Saved" and s["lastAuthoring"]["affected"] == 2 and label["name"] == "Serial no." and
                 label["previousNames"] == ["Serail no"] and unchanged, s["namesStatus"])

    # --- Remove: impossible without a replacement, in the page and in the store.
    driver.click_selector(f'#names-list li[data-label="{typo}"] button[data-act=remove]')
    go_disabled = page.eval("document.querySelector('#names-list .name-form button[data-act=replace-go]').disabled")
    raw0 = page.eval("VRHEDemoPage.test.storedRaw()")
    revision = catalog_label(page, typo)["revision"]
    replies = [authoring_raw(page, {"op": "replaceLabel", "labelId": typo, "baseRevision": revision,
                                    "replacementLabelId": rid, "replacementName": rname})
               for rid, rname in (("", ""), ("", "   "), (typo, ""), ("", "serial NO."))]
    checks.check("Remove can't be confirmed until a replacement is chosen (button disabled)", go_disabled)
    checks.check("the store itself refuses removal without a valid replacement and writes nothing",
                 all(r and r["status"] == "Invalid" for r in replies) and page.eval("VRHEDemoPage.test.storedRaw()") == raw0,
                 "; ".join(f"{r['status']}" if r else "no reply" for r in replies))

    # --- Replace with an existing name across two items, with a name clash on both.
    page.eval(f"(() => {{ const s = document.getElementById('names-rep-existing'); s.value = {json.dumps(serial)};"
              " s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    before = stored_doc(page)
    driver.click_selector("#names-list .name-form button[data-act=replace-go]")
    s = snap(page)
    after = stored_doc(page)
    moved = {i: [(d["descriptionId"], serial if d["labelId"] == typo else d["labelId"], d["text"])
                 for d in stored_item(before, i)["descriptions"]] for i in (ctx["SW"], ctx["RT"])}
    checks.check("Replace moves every description from 'Serial no.' to 'Serial number', keeping IDs, order and text",
                 s["lastAuthoring"]["status"] == "Saved" and s["lastAuthoring"]["affected"] == 2 and
                 all(triples(stored_item(after, i)["descriptions"]) == moved[i] for i in moved) and
                 triples(stored_item(after, ctx["SRV"])["descriptions"]) == triples(stored_item(before, ctx["SRV"])["descriptions"]),
                 s["namesStatus"])
    checks.check("where an item already had 'Serial number', both descriptions are kept and the page says so",
                 any("Both descriptions are kept" in w for w in s["namesWarnings"]) and
                 [d["text"] for d in stored_item(after, ctx["SW"])["descriptions"] if d["labelId"] == serial] == ["SYN-SW-0001", "SW-OLD-77"],
                 "; ".join(s["namesWarnings"]))
    retired = stored_label(after, typo)
    options = page.eval(f"(() => {{ const l = VRHEDemoPage.test.snapshot().catalog.labels;"
                        f" return l.filter(x => !x.retired).map(x => x.labelId).includes({json.dumps(typo)}); }})()")
    checks.check("the replaced name leaves the list and stays recorded as replaced, with what moved",
                 retired["retired"] and retired["replacedByLabelId"] == serial and len(retired["reassignedDescriptionIds"]) == 2 and
                 not options and page.eval(f"!!document.querySelector('#names-retired li[data-label=\"{typo}\"]')"))

    # --- A refused browser write (storage full) changes nothing; the same replacement works afterwards.
    set_field(driver, page, "names-new", "Asset no.")
    driver.click_element("names-add")
    asset_no = snap(page)["lastAuthoring"]["labelId"]
    driver.press("Escape")
    open_item_from_list(driver, page, ctx["SRV"])
    add_description(driver, page)
    choose_name(page, 1, asset_no)
    type_description(driver, page, 1, "AN-555")
    save_item(driver, page)
    open_names(driver, page)
    driver.click_selector(f'#names-list li[data-label="{asset_no}"] button[data-act=remove]')
    page.eval(f"(() => {{ const s = document.getElementById('names-rep-existing'); s.value = {json.dumps(asset_tag)};"
              " s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    raw0 = page.eval("VRHEDemoPage.test.storedRaw()")
    filled = fill_storage(page)
    driver.click_selector("#names-list .name-form button[data-act=replace-go]")
    s = snap(page)
    checks.check("with browser storage full, the replacement is refused and nothing changes",
                 s["lastAuthoring"]["status"] == "StorageError" and "Nothing was changed" in s["namesStatus"] and
                 page.eval("VRHEDemoPage.test.storedRaw()") == raw0 and not catalog_label(page, asset_no)["retired"],
                 f"filled {filled['keys']} keys / {filled['chars']} chars; {s['namesStatus'][:120]}")
    freed = free_storage(page)
    page.eval(f"(() => {{ const s = document.getElementById('names-rep-existing'); s.value = {json.dumps(asset_tag)};"
              " s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    driver.click_selector("#names-list .name-form button[data-act=replace-go]")
    s = snap(page)
    srv_doc = stored_item(stored_doc(page), ctx["SRV"])
    checks.check("after space is freed the same replacement succeeds and keeps the text",
                 freed == filled["keys"] and s["lastAuthoring"]["status"] == "Saved" and
                 (srv_doc["descriptions"][1]["labelId"], srv_doc["descriptions"][1]["text"]) == (asset_tag, "AN-555"),
                 s["namesStatus"][:120])
    ctx["pacing"].append(pacing(page, "panel.names open (2 s)", lambda: time.sleep(2.0)))
    driver.press("Escape")

    # The final state that reload, restart and export must reproduce.
    doc = stored_doc(page)
    ctx["expect"] = {i: {"name": stored_item(doc, i)["name"], "ru": (stored_item(doc, i)["ruStart"], stored_item(doc, i)["ruEnd"]),
                         "descriptions": triples(stored_item(doc, i)["descriptions"])} for i in (ctx["SW"], ctx["SRV"], ctx["RT"])}
    ctx["labels"] = {"typo": typo, "asset_no": asset_no, "firmware": firmware, "serial": serial, "asset_tag": asset_tag}
    ctx["pacing"] = [p for p in ctx["pacing"] if p]
    return ctx


def check_authoring_persisted(page, driver, checks, ctx, when):
    """Open every item through the Equipment list and compare it with the state saved earlier."""
    ok = True
    for equipment_id, expect in ctx["expect"].items():
        s = open_item_from_list(driver, page, equipment_id)
        e = s["equipment"]
        ok = ok and e["name"] == expect["name"] and (e["ruStart"], e["ruEnd"]) == tuple(expect["ru"]) and \
            [tuple(x) for x in triples(e["descriptions"])] == [tuple(x) for x in expect["descriptions"]]
        driver.press("Escape")
    labels = {l["labelId"]: l for l in snap(page)["catalog"]["labels"]}
    names = ctx["labels"]
    checks.check(f"{when} keeps every equipment item, its RU range and each description's ID, name and text", ok)
    checks.check(f"{when} keeps the name list: replaced names retired, the new name active",
                 labels[names["typo"]]["retired"] and labels[names["asset_no"]]["retired"] and
                 not labels[names["firmware"]]["retired"] and labels[names["typo"]]["replacedByName"] == "Serial number")


def check_authoring_export(export, ctx, checks):
    items = {e["equipmentId"]: e for e in export.get("equipment", [])}
    ok = all(i in items and [tuple(x) for x in triples(items[i]["descriptions"])] == [tuple(x) for x in ctx["expect"][i]["descriptions"]]
             for i in ctx["expect"])
    labels = {l["labelId"]: l for l in export.get("labels", [])}
    checks.check("export (format 2) carries every equipment item with its descriptions and name labels", ok and
                 export.get("schemaVersion") == 2 and
                 items[ctx["SRV"]]["descriptions"][0]["labelName"] == "Serial number" if ok else False)
    checks.check("export keeps replaced names inspectable and says no spreadsheet column is touched",
                 labels[ctx["labels"]["typo"]]["retired"] and labels[ctx["labels"]["typo"]]["replacedByLabelId"] == ctx["labels"]["serial"] and
                 "never renames, clears or deletes a spreadsheet column" in export.get("mappingNotice", ""))


def check_reset_v2(page, checks, site):
    doc = stored_doc(page)
    active = [l for l in (doc or {}).get("labels", []) if not l["retired"]]
    checks.check("Reset demo data starts over: no rack notes, no equipment, only the starter names",
                 doc is not None and doc["rackNotes"] == [] and doc["equipment"] == [] and
                 doc["migration"]["state"] == "reset" and
                 sorted(l["labelId"] for l in active) == sorted(l["labelId"] for l in site["labels"]) and
                 len(doc["labels"]) == len(site["labels"]),
                 f"{len((doc or {}).get('equipment', []))} items, {len(active)} names")


# ------------------------------------------------------------------------------- migration from the first demo
MIGRATION_UNKNOWN = "rec-11111111-2222-3333-4444-555555555555"


def save_note_old_build(page, driver, record_id, text):
    """Open a rack in whichever build is running and save a rack note (real typing, Ctrl+Enter)."""
    page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsOpenRecord', JSON.stringify({{recordId: {json.dumps(record_id)}, how: 'check'}}))")
    wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="record panel")
    page.eval("document.getElementById('rec-description').select()")
    driver.type_text(text, 0.02)
    driver.press("Enter", modifiers=2)
    s = snap(page)
    driver.press("Escape")
    return s["lastSave"]


def open_note(page, record_id):
    page.eval(f"unityInstance.SendMessage('VRHEDemo', 'JsOpenRecord', JSON.stringify({{recordId: {json.dumps(record_id)}, how: 'check'}}))")
    return wait(lambda: (lambda x: x if x["panel"] == "record" else None)(snap(page)), 5, what="record panel")["record"]


def run_migration(args, results, downloads, checks, site):
    """The delivered first-demo build writes version 1 data in a real browser profile; this build then
    reads the same profile; finally the first build runs again on it."""
    rec = {r["name"]: r for r in site["records"]}
    a3, b4 = rec["Rack A3"], rec["Rack B4"]
    v1_key, v2_key = V1_PREFIX + site["siteId"], V2_PREFIX + site["siteId"]
    old = argparse.Namespace(**vars(args))
    old.bundle = args.old_bundle
    notes = {"A3": "A3 note saved by the first demo build " + str(random.randint(1000, 9999)),
             "B4": "B4 note, second save " + str(random.randint(1000, 9999))}
    out = {}

    def old_session(page, browser):
        prepare(page, browser, downloads)
        out["old_label"] = http_json(DEMO_URL + "data/build-info.json").get("label")
        driver = Driver(page)
        checks.check("first demo build uses the version 1 key", snap(page)["storageKey"] == v1_key)
        a = save_note_old_build(page, driver, a3["recordId"], notes["A3"])
        save_note_old_build(page, driver, b4["recordId"], "B4 first save")
        b = save_note_old_build(page, driver, b4["recordId"], notes["B4"])
        raw = json.loads(page.eval(f"localStorage.getItem({json.dumps(v1_key)})"))
        raw["entries"].append({"recordId": MIGRATION_UNKNOWN, "description": "note for a rack this site version lacks",
                               "revision": 4, "updatedAt": "2026-11-10T08:00:00Z"})
        page.eval(f"localStorage.setItem({json.dumps(v1_key)}, {json.dumps(json.dumps(raw))})")
        out["v1_raw"] = page.eval(f"localStorage.getItem({json.dumps(v1_key)})")
        checks.check("first demo build saved version 1 rack notes (A3 once, B4 twice) plus an unknown record",
                     a["status"] == "Saved" and b["status"] == "Saved" and b["revision"] == 2 and
                     page.eval(f"localStorage.getItem({json.dumps(v2_key)})") is None)

    def new_session(page, browser):
        prepare(page, browser, downloads)
        driver = Driver(page)
        checks.check("this build opens the profile without writing anything",
                     page.eval(f"localStorage.getItem({json.dumps(v2_key)})") is None and
                     page.eval(f"localStorage.getItem({json.dumps(v1_key)})") == out["v1_raw"])
        a, b = open_note(page, a3["recordId"]), None
        driver.press("Escape")
        b = open_note(page, b4["recordId"])
        driver.press("Escape")
        checks.check("first-demo rack notes are carried over as rack notes with their versions",
                     a["description"] == notes["A3"] and a["revision"] == 1 and a["source"] == "local edit" and
                     b["description"] == notes["B4"] and b["revision"] == 2 and a["equipment"] == [],
                     f"A3 v{a['revision']}, B4 v{b['revision']}")
        driver.click_selector("button[data-action=data]")
        wait_panel(page, "data")
        migration_text = page.eval("document.getElementById('data-migration').textContent")
        checks.check("Saved data panel explains the carry-over and the kept copy",
                     "Carried over 3 rack notes" in migration_text and "kept unchanged" in migration_text, migration_text)
        driver.click_element("data-export")
        export = json.loads(wait(lambda: page.eval("VRHEDemoPage.test.lastExportJson()"), 5, what="export"))
        copies = {c["key"]: c for c in export["storedCopies"]}
        checks.check("export before any save holds the carried notes, the unknown record and the raw version 1 copy",
                     {r["recordId"]: r["description"] for r in export["records"]}[a3["recordId"]] == notes["A3"] and
                     export["unmatchedStoredEntries"][0]["recordId"] == MIGRATION_UNKNOWN and
                     copies.get(v1_key, {}).get("raw") == out["v1_raw"] and export["migration"]["state"] == "carried over" and
                     page.eval(f"localStorage.getItem({json.dumps(v2_key)})") is None)
        driver.press("Escape")
        s = open_rack(driver, page, a3)
        add_equipment(driver, page, "Synthetic patch panel PP-01", "42")
        wait_panel(page, "equipment", "patch panel")
        driver.press("Escape")
        doc = json.loads(page.eval(f"localStorage.getItem({json.dumps(v2_key)})"))
        notes_v2 = {e["recordId"]: e for e in doc["rackNotes"]}
        checks.check("the first save writes format 2 with every carried note (unknown included); version 1 untouched",
                     notes_v2[a3["recordId"]]["description"] == notes["A3"] and notes_v2[b4["recordId"]]["revision"] == 2 and
                     MIGRATION_UNKNOWN in notes_v2 and doc["migration"]["fromKey"] == v1_key and
                     doc["migration"]["sourceEntries"] == 3 and
                     page.eval(f"localStorage.getItem({json.dumps(v1_key)})") == out["v1_raw"])
        reload_page(page)
        a = open_note(page, a3["recordId"])
        driver.press("Escape")
        checks.check("after a reload this build still shows the carried note and the new equipment",
                     a["description"] == notes["A3"] and [e["name"] for e in a["equipment"]] == ["Synthetic patch panel PP-01"])

    def old_again(page, browser):
        prepare(page, browser, downloads)
        a = open_note(page, a3["recordId"])
        checks.check("the first demo build still finds its own saved notes afterwards",
                     a["description"] == notes["A3"] and a["revision"] == 1 and
                     page.eval(f"localStorage.getItem({json.dumps(v1_key)})") == out["v1_raw"])

    _, code = run_session(old, results, old_session)
    _, code = run_session(args, results, new_session)
    _, code = run_session(old, results, old_again)
    return out


def close_browser(browser_cdp):
    if browser_cdp is None:
        return
    try:
        browser_cdp.call("Browser.close", timeout=10)
    except Exception:
        pass


def port_in_use(port):
    """True if anything listens on this loopback port (IPv4 or IPv6)."""
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                if probe.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            pass
    return False


def run_session(args, results, body):
    """Start the demo with the throwaway profile and run body(page, browser).

    The browser this check started is always closed, also after a failure, so no test window is
    left behind. Returns (body result, demo server exit code); the server stops by itself once
    the page has gone (or is terminated after 90 s, which shows as a negative exit code)."""
    proc, log = start_demo(args, results, args.devtools_port)
    browser = page = None
    try:
        page, browser = connect(args.devtools_port)
        result = body(page, browser)
    finally:
        close_browser(browser)
        for cdp in (page, browser):
            try:
                if cdp is not None:
                    cdp.ws.close()
            except Exception:
                pass
        try:
            proc.wait(timeout=90)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=10)
        log.close()
    return result, proc.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--browser", default="chrome", choices=["chrome", "brave", "chromium", "edge"])
    parser.add_argument("--binary")
    parser.add_argument("--profile-dir", required=True, help="throwaway persistent profile for this check")
    parser.add_argument("--devtools-port", type=int, default=9333)
    parser.add_argument("--bundle", help="extracted Windows demo bundle to check instead of Builds/InteractiveDemo")
    parser.add_argument("--part", default="all", choices=["all", "authoring", "migration"])
    parser.add_argument("--old-bundle", help="extracted first-demo bundle (for --part migration)")
    args = parser.parse_args()
    if args.part == "migration":
        if not args.old_bundle or not os.path.isfile(os.path.join(args.old_bundle, "bundle.json")):
            raise SystemExit("--part migration needs --old-bundle <extracted first-demo bundle folder>")
        args.old_bundle = os.path.abspath(args.old_bundle)
    if os.path.isdir(args.profile_dir) and os.listdir(args.profile_dir) and args.part == "migration":
        raise SystemExit("--part migration needs a new, empty --profile-dir")
    if args.bundle:
        args.bundle = os.path.abspath(args.bundle)
        if not os.path.isfile(os.path.join(args.bundle, "bundle.json")):
            raise SystemExit(f"{args.bundle} is not an extracted demo bundle (no bundle.json)")
    if args.devtools_port == 9002:
        raise SystemExit("port 9002 is reserved")
    args.profile_dir = os.path.abspath(args.profile_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    results = os.path.join(PROJECT, "TestResults", "raw", "interactive-demo", f"verify-{stamp}-{args.browser}")
    downloads = os.path.join(results, "downloads")
    os.makedirs(downloads, exist_ok=True)
    with open(SITE, encoding="utf-8") as f:
        site = json.load(f)
    checks = Checks()
    summary = {"browser": args.browser, "started": stamp, "profile": "throwaway profile for this check", "part": args.part,
               "target": "bundle " + json.load(open(os.path.join(args.bundle, "bundle.json"), encoding="utf-8"))["build"]["label"]
               if args.bundle else "Builds/InteractiveDemo"}

    # Never attach to someone else's browser or demo server: a busy port could mean an old test
    # window, whose page would then be checked instead of a fresh one.
    busy = [p for p in (args.devtools_port, DEMO_PORT) if port_in_use(p)]
    if busy:
        raise SystemExit(f"Port(s) {busy} already in use (an open test browser or demo server?). Close it first.")

    def first(page, browser):
        summary["browser_version"] = http_json(f"http://127.0.0.1:{args.devtools_port}/json/version").get("Browser")
        prepare(page, browser, downloads)
        result = run_session_one(args, page, browser, Driver(page), checks, site, results, downloads)
        page.eval("unityInstance.SendMessage('VRHEDemo', 'JsCommand', 'report')")
        time.sleep(0.5)
        return result

    def second(page, browser):
        prepare(page, browser, downloads)
        run_session_two(page, Driver(page), checks, site, outcome["notes"], outcome["authoring"])

    def authoring_first(page, browser):
        summary["browser_version"] = http_json(f"http://127.0.0.1:{args.devtools_port}/json/version").get("Browser")
        prepare(page, browser, downloads)
        driver = Driver(page)
        ctx = run_authoring_checks(page, driver, checks, site)
        reload_page(page)
        check_authoring_persisted(page, driver, checks, ctx, "a page reload")
        driver.click_selector("button[data-action=data]")
        driver.click_element("data-export")
        export = json.loads(wait(lambda: page.eval("VRHEDemoPage.test.lastExportJson()"), 5, what="export"))
        check_authoring_export(export, ctx, checks)
        driver.press("Escape")
        page.eval("unityInstance.SendMessage('VRHEDemo', 'JsCommand', 'report')")
        time.sleep(0.5)
        return {"authoring": ctx, "pacing": ctx["pacing"]}

    def authoring_second(page, browser):
        prepare(page, browser, downloads)
        driver = Driver(page)
        check_authoring_persisted(page, driver, checks, outcome["authoring"], "closing and restarting the browser")
        driver.click_selector("button[data-action=data]")
        driver.click_element("data-reset")
        driver.click_element("data-reset-yes")
        time.sleep(0.3)
        check_reset_v2(page, checks, site)
        driver.press("Escape")

    if args.part == "migration":
        summary["browser_version"] = "see launcher logs"
        summary["old_bundle"] = json.load(open(os.path.join(args.old_bundle, "bundle.json"), encoding="utf-8"))["build"]["label"]
        run_migration(args, results, downloads, checks, site)
    else:
        outcome, code = run_session(args, results, first if args.part == "all" else authoring_first)
        summary["pacing"] = outcome["pacing"]
        checks.check("closing the browser stops the demo server by itself", code == 0, f"exit {code}")
        run_session(args, results, second if args.part == "all" else authoring_second)

    summary["checks"] = checks.items
    summary["passed"] = len(checks.items) - len(checks.failed)
    summary["failed"] = len(checks.failed)
    with open(os.path.join(results, "verify.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{summary['passed']} passed, {summary['failed']} failed. Results: {results}")
    return 0 if not checks.failed else 1


if __name__ == "__main__":
    sys.exit(main())
