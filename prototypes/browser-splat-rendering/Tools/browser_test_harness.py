#!/usr/bin/env python3
"""Local test server and browser launcher for the VR-HE browser splat benchmark.

The Unity Web build reports its own results: the benchmark page POSTs JSON, screenshots and
console output back to this server, so no browser-automation driver is needed.

Commands:
  serve    Serve the build and fixtures until interrupted. The root page (/) starts a run in
           whichever browser opens it: the manual fallback when automatic launching fails.
  run      Serve, launch one browser with a fresh temporary profile, wait for the page to
           report completion, close only that browser and print a plain-language summary.
  collect  Zip a results folder into one file for transfer to the development laptop.

Platforms: Linux (development laptop) and Windows (the reference-PC bundle written by
Tools/package_toughbook_bundle.py). Treat the Windows code paths as untested on real Windows
until a recorded run says otherwise; see docs/HANDOFF.md.

Security and scope:
  * Binds to 127.0.0.1 only. Never uses port 9002, which belongs to another local tool on the
    development laptop. On Windows the port is claimed exclusively.
  * Serves files only from the build and fixture folders. Accepts uploads only under
    <results>/<run>/ with simple file names.
  * Starts the browser with a fresh temporary profile and stops only what it started: the
    process group on Linux, the tracked process tree on Windows. Existing browser windows and
    profiles are not touched, and nothing is installed or reconfigured.
  * Records browser/OS/GPU facts for the test record. It does not record host names, user
    names, serial numbers, account details or credentials, and saved records contain no
    absolute paths inside the user's folders.

Examples:
  python3 -I Tools/browser_test_harness.py run --browser chrome --run 20261110-chrome-1
      --build Builds/WebGL --fixtures Fixtures/Generated --results TestResults/raw
      --profile-root /path/to/scratch/profiles
  python -I tools/browser_test_harness.py run --bundle <bundle folder> --browser edge
      --plan baseline
"""

import argparse
import datetime
import hashlib
import http.server
import json
import os
import platform
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import zipfile

IS_WINDOWS = os.name == "nt"
HARNESS_VERSION = "2"

# Port 9002 is The Veil's Unity AI Assistant relay on the development laptop. It is never
# used, even when free, so a test server can never be mistaken for that relay.
RESERVED_PORTS = frozenset({9002})
# Manual mode prefers a short, typeable address; automatic runs let the OS pick a free port.
MANUAL_PORTS = tuple(range(8765, 8776))

# The browser floor (D034) is 30 application-rendered fps: 33.3 ms per frame. This build's
# frame clock has 1 ms steps and frames follow the display refresh, so a frame that exactly
# meets 30 fps is recorded as 33 or 34 ms. "Slow" therefore starts at 36 ms. These are
# descriptive statistics; detailed acceptance criteria are still open.
FLOOR_FPS = 30.0
SLOW_FRAME_MS = 36.0
STALL_MS = 100.0
# A manual test that has not reported for this long no longer blocks starting the next one.
MANUAL_STALE_SECONDS = 300

SAFE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,159}$")
WINDOWS_DEVICE_NAME = re.compile(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?$", re.IGNORECASE)
# Files the harness writes itself; the page may not overwrite them.
HARNESS_FILES = frozenset({"harness.json", "summary.txt", "server.log", "browser-stdout.log"})

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
    ".txt": "text/plain; charset=utf-8",
}

# Page parameters for the reference-PC plans. Everything else (warm-up and measurement times,
# quality level, render scale, orbit, compression) stays at the benchmark defaults used for
# the November 10 measurements, so results remain comparable.
PLANS = {
    # First run on a new PC: overlap cases plus 25k-250k splats in one page.
    "baseline": {"suites": "overlap,scale", "counts": "25000,100000,250000"},
    # Optional follow-up in a fresh page, so its memory figures stand alone.
    "followup-500k": {"suites": "scale", "counts": "500000"},
}
PLAN_TITLES = {"baseline": "baseline", "followup-500k": "optional 500k follow-up"}

# Install locations. Linux entries are absolute paths or "which:<command>". Windows entries
# are relative to Program Files, Program Files (x86) and the per-user LocalAppData folder;
# the App Paths registry entry for the same .exe name is checked last.
BROWSERS = {
    "chrome": {
        "family": "chromium",
        "label": "Google Chrome",
        "linux": ["/opt/google/chrome/google-chrome"],
        "windows": [r"Google\Chrome\Application\chrome.exe"],
    },
    "edge": {
        "family": "chromium",
        "label": "Microsoft Edge",
        "linux": ["/opt/microsoft/msedge/msedge"],
        "windows": [r"Microsoft\Edge\Application\msedge.exe"],
    },
    "brave": {
        "family": "chromium",
        "label": "Brave",
        "linux": ["/opt/brave.com/brave/brave-browser"],
        "windows": [r"BraveSoftware\Brave-Browser\Application\brave.exe"],
    },
    "chromium": {
        "family": "chromium",
        "label": "Chromium",
        "linux": ["which:chromium", "which:chromium-browser"],
        "windows": [r"Chromium\Application\chrome.exe"],
    },
    "firefox": {
        "family": "firefox",
        "label": "Mozilla Firefox",
        "linux": ["/usr/lib/firefox/firefox", "which:firefox"],
        "windows": [r"Mozilla Firefox\firefox.exe"],
    },
}


def chromium_flags():
    """Harness-only flags: fresh profile without first-run UI, extensions, sync or background
    traffic, and no throttling of a window that loses focus. None changes WebGL or GPU choice.
    The Linux list is unchanged from the November 10 runs."""
    flags = [
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-component-update",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-default-apps",
    ]
    if not IS_WINDOWS:
        flags.append("--password-store=basic")  # avoids a Linux keyring prompt
    flags += [
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
        "--new-window",
    ]
    if IS_WINDOWS:
        # Screen sizes and scaling vary on laptops; a maximized window always fits the screen.
        flags.append("--start-maximized")
    else:
        flags += ["--window-position=0,0", "--window-size=1400,960"]
    return flags


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
KNOWN_WARNING = "[GsplatSorter] GPU wave-op radix sorting is unavailable"
SOFTWARE_RENDERERS = ("swiftshader", "llvmpipe", "softpipe", "basic render", "software rasterizer")

# Region colors recorded for every overlap case on the RTX 4060 laptop in Chrome, Firefox and
# Brave: (a_only, shared_band, b_only). The separate-renderer cases reproduce known ordering
# errors; matching them means the renderer behaves the same way on this PC.
EXPECTED_OVERLAP = {
    "overlap_merged_single_renderer": ("red_A", "red_A", "blue_B"),
    "overlap_separate_renderers": ("red_A", "blue_B", "blue_B"),
    "overlap_separate_A_forced_last": ("red_A", "red_A", "backdrop_A"),
    "overlap_merged_active_ranges__only_A": ("red_A", "red_A", "backdrop_A"),
    "overlap_merged_active_ranges__only_B": ("background", "blue_B", "blue_B"),
    "overlap_merged_active_ranges__A_and_B": ("red_A", "red_A", "blue_B"),
    "overlap_merged_active_ranges__cleared": ("red_A", "red_A", "blue_B"),
    "overlap_merged_active_ranges": ("red_A", "red_A", "blue_B"),
}


# ------------------------------------------------------------------------------- helpers
def safe_name(name):
    """One file or folder name that is safe on Linux and Windows: no separators, '..', drive
    letters or NTFS stream names (':'), trailing dots or Windows device names (CON, NUL...)."""
    return bool(SAFE_NAME.match(name)) and not name.endswith(".") and not WINDOWS_DEVICE_NAME.match(name)


def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temporary, path)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path):
    """A path for saved records, with the user's own folders replaced by placeholders."""
    if not path:
        return path
    full = os.path.abspath(path)
    for var in ("LOCALAPPDATA", "APPDATA", "USERPROFILE", "HOME"):
        base = os.environ.get(var)
        if not base:
            continue
        base = os.path.abspath(base)
        if os.path.normcase(full) == os.path.normcase(base) or \
                os.path.normcase(full).startswith(os.path.normcase(base) + os.sep):
            return "%" + var + "%" + full[len(base):]
    return full


def command_output(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout,
                              stdin=subprocess.DEVNULL).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def remove_tree(path, attempts=20, delay=0.5):
    """Delete a folder, retrying while Windows still holds files open after a browser exits."""
    def make_writable_and_retry(function, target, *_):
        try:
            os.chmod(target, 0o700)
            function(target)
        except OSError:
            pass

    for _ in range(attempts):
        if not os.path.exists(path):
            return True
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=make_writable_and_retry)
        else:
            shutil.rmtree(path, onerror=make_writable_and_retry)
        if not os.path.exists(path):
            return True
        time.sleep(delay)
    return not os.path.exists(path)


def free_space_ok(path, what):
    try:
        free = shutil.disk_usage(path).free
    except OSError:
        return True
    gb = free / 2 ** 30
    if free < 300 * 2 ** 20:
        print(f"Not enough free disk space for the {what} ({gb:.2f} GB free). Free at least 1 GB and try again.")
        return False
    if free < 2 ** 30:
        print(f"Note: only {gb:.2f} GB free for the {what}.")
    return True


# ------------------------------------------------------------------------------- Windows APIs
if IS_WINDOWS:
    import ctypes
    import winreg
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _version = ctypes.WinDLL("version", use_last_error=True)

    _TH32CS_SNAPPROCESS = 0x00000002
    _PROCESS_TERMINATE = 0x0001
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _ENUM_CURRENT_SETTINGS = 0xFFFFFFFF

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    class _FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    class _SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
            ("ACLineStatus", ctypes.c_ubyte),
            ("BatteryFlag", ctypes.c_ubyte),
            ("BatteryLifePercent", ctypes.c_ubyte),
            ("SystemStatusFlag", ctypes.c_ubyte),
            ("BatteryLifeTime", wintypes.DWORD),
            ("BatteryFullLifeTime", wintypes.DWORD),
        ]

    class _DEVMODEW(ctypes.Structure):
        # Display variant of DEVMODEW (220 bytes); the printer fields share the same union.
        _fields_ = [
            ("dmDeviceName", wintypes.WCHAR * 32),
            ("dmSpecVersion", wintypes.WORD),
            ("dmDriverVersion", wintypes.WORD),
            ("dmSize", wintypes.WORD),
            ("dmDriverExtra", wintypes.WORD),
            ("dmFields", wintypes.DWORD),
            ("dmPositionX", wintypes.LONG),
            ("dmPositionY", wintypes.LONG),
            ("dmDisplayOrientation", wintypes.DWORD),
            ("dmDisplayFixedOutput", wintypes.DWORD),
            ("dmColor", ctypes.c_short),
            ("dmDuplex", ctypes.c_short),
            ("dmYResolution", ctypes.c_short),
            ("dmTTOption", ctypes.c_short),
            ("dmCollate", ctypes.c_short),
            ("dmFormName", wintypes.WCHAR * 32),
            ("dmLogPixels", wintypes.WORD),
            ("dmBitsPerPel", wintypes.DWORD),
            ("dmPelsWidth", wintypes.DWORD),
            ("dmPelsHeight", wintypes.DWORD),
            ("dmDisplayFlags", wintypes.DWORD),
            ("dmDisplayFrequency", wintypes.DWORD),
            ("dmICMMethod", wintypes.DWORD),
            ("dmICMIntent", wintypes.DWORD),
            ("dmMediaType", wintypes.DWORD),
            ("dmDitherType", wintypes.DWORD),
            ("dmReserved1", wintypes.DWORD),
            ("dmReserved2", wintypes.DWORD),
            ("dmPanningWidth", wintypes.DWORD),
            ("dmPanningHeight", wintypes.DWORD),
        ]

    class _VS_FIXEDFILEINFO(ctypes.Structure):
        _fields_ = [(name, wintypes.DWORD) for name in (
            "dwSignature", "dwStrucVersion", "dwFileVersionMS", "dwFileVersionLS", "dwProductVersionMS",
            "dwProductVersionLS", "dwFileFlagsMask", "dwFileFlags", "dwFileOS", "dwFileType",
            "dwFileSubtype", "dwFileDateMS", "dwFileDateLS")]

    _kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _kernel32.Process32FirstW.restype = wintypes.BOOL
    _kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _kernel32.Process32NextW.restype = wintypes.BOOL
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(_FILETIME)] * 4
    _kernel32.GetProcessTimes.restype = wintypes.BOOL
    _kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    _kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateProcess.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MEMORYSTATUSEX)]
    _kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
    _kernel32.GetSystemPowerStatus.argtypes = [ctypes.POINTER(_SYSTEM_POWER_STATUS)]
    _kernel32.GetSystemPowerStatus.restype = wintypes.BOOL
    _user32.EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(_DEVMODEW)]
    _user32.EnumDisplaySettingsW.restype = wintypes.BOOL
    _version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    _version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    _version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    _version.GetFileVersionInfoW.restype = wintypes.BOOL
    _version.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p),
                                        ctypes.POINTER(wintypes.UINT)]
    _version.VerQueryValueW.restype = wintypes.BOOL

    def win_process_table():
        """{pid: (parent pid, exe name)} for every process visible to this user."""
        table = {}
        snapshot = _kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
        if not snapshot or snapshot == _INVALID_HANDLE_VALUE:
            return table
        try:
            entry = _PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
            ok = _kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while ok:
                table[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
                ok = _kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            _kernel32.CloseHandle(snapshot)
        return table

    def _handle_creation_time(handle):
        created, exited, kernel, user = _FILETIME(), _FILETIME(), _FILETIME(), _FILETIME()
        if not _kernel32.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                         ctypes.byref(kernel), ctypes.byref(user)):
            return None
        return (created.dwHighDateTime << 32) | created.dwLowDateTime

    def win_process_identity(pid):
        """Creation time of a running process, or None. A PID plus its creation time identifies
        one process instance even after Windows reuses the PID number."""
        handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return None
        try:
            code = wintypes.DWORD()
            if _kernel32.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value != 259:  # STILL_ACTIVE
                return None
            return _handle_creation_time(handle)
        finally:
            _kernel32.CloseHandle(handle)

    def win_terminate(pid, identity):
        """Terminate one process, but only if it is still the instance recorded earlier."""
        handle = _kernel32.OpenProcess(_PROCESS_TERMINATE | _PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            if identity is not None and _handle_creation_time(handle) != identity:
                return False
            return bool(_kernel32.TerminateProcess(handle, 1))
        finally:
            _kernel32.CloseHandle(handle)

    class WindowsProcessTree:
        """The launched browser and every descendant seen while the test runs.

        Chromium and Firefox start renderer, GPU and helper processes. They are recorded while
        their parents are alive (Windows does not re-parent orphans), and each is identified by
        PID plus creation time, so a recycled PID can never cause an unrelated process to be
        stopped. Only these processes are ever terminated."""

        def __init__(self, root_pid):
            self.root = root_pid
            self.root_identity = win_process_identity(root_pid)
            self.known = {}

        def refresh(self):
            table = win_process_table()
            alive = {}
            if self.root_identity is not None and self.root in table and \
                    win_process_identity(self.root) == self.root_identity:
                alive[self.root] = self.root_identity
            for pid, identity in self.known.items():
                if pid in table and win_process_identity(pid) == identity:
                    alive[pid] = identity
            frontier = list(alive.items())
            while frontier:
                parent, parent_identity = frontier.pop()
                for pid, (ppid, _) in table.items():
                    if ppid != parent or pid == self.root or pid in self.known:
                        continue
                    identity = win_process_identity(pid)
                    if identity is None or parent_identity is None or identity < parent_identity:
                        continue  # created before its supposed parent: a recycled PID
                    self.known[pid] = identity
                    frontier.append((pid, identity))

        def running(self):
            table = win_process_table()
            return [pid for pid, identity in self.known.items()
                    if pid in table and win_process_identity(pid) == identity]

        def stop(self, proc):
            """Stop the browser and its tracked descendants; return PIDs still running.
            The browser goes first: stopping a GPU or renderer process first would make the
            browser start a replacement that this tree has not seen yet."""
            self.refresh()
            if proc.poll() is None:
                try:
                    proc.kill()  # TerminateProcess through the handle Popen holds: always this process
                except OSError:
                    pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            for pid, identity in list(self.known.items()):
                win_terminate(pid, identity)
            time.sleep(1)
            for pid in self.running():
                win_terminate(pid, self.known[pid])
            time.sleep(0.5)
            leftovers = self.running()
            if proc.poll() is None:
                leftovers.append(proc.pid)
            return leftovers

    def windows_file_version(path):
        """Product version from an executable's version resource, without starting it."""
        size = _version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buffer = ctypes.create_string_buffer(size)
        if not _version.GetFileVersionInfoW(path, 0, size, buffer):
            return None
        pointer, length = ctypes.c_void_p(), wintypes.UINT()
        if not _version.VerQueryValueW(buffer, "\\", ctypes.byref(pointer), ctypes.byref(length)) or not pointer.value:
            return None
        info = ctypes.cast(pointer, ctypes.POINTER(_VS_FIXEDFILEINFO)).contents
        if info.dwSignature != 0xFEEF04BD:
            return None
        ms, ls = info.dwProductVersionMS, info.dwProductVersionLS
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"

    def _registry_values(root, key, names):
        values = {}
        try:
            with winreg.OpenKey(root, key, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as handle:
                for name in names:
                    try:
                        values[name] = winreg.QueryValueEx(handle, name)[0]
                    except OSError:
                        pass
        except OSError:
            pass
        return values

    def _app_path(exe_name):
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            value = _registry_values(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths" + "\\" + exe_name,
                                     [""]).get("")
            if value:
                value = os.path.expandvars(str(value).strip().strip('"'))
                if os.path.isfile(value):
                    return value
        return None

    def windows_system_facts():
        """Windows edition/build, CPU, RAM, GPU driver, display mode and power state.
        Deliberately omits the computer name, user and owner names and every serial number."""
        current = _registry_values(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                                   ["ProductName", "EditionID", "DisplayVersion", "ReleaseId", "CurrentBuild",
                                    "CurrentBuildNumber", "UBR", "InstallationType"])
        try:
            build = int(current.get("CurrentBuild") or current.get("CurrentBuildNumber") or sys.getwindowsversion().build)
        except (TypeError, ValueError):
            build = sys.getwindowsversion().build
        product = str(current.get("ProductName") or "Windows")
        if build >= 22000 and "Windows 10" in product:
            product = product.replace("Windows 10", "Windows 11")  # the registry keeps "Windows 10"
        facts = {
            "os": f"{product} {current.get('DisplayVersion') or current.get('ReleaseId') or ''}".strip(),
            "windows": {
                "product": product,
                "edition": current.get("EditionID"),
                "display_version": current.get("DisplayVersion") or current.get("ReleaseId"),
                "build": f"{build}.{current.get('UBR')}" if current.get("UBR") is not None else str(build),
                "installation_type": current.get("InstallationType"),
            },
            "machine": platform.machine(),
            "cpu": _registry_values(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                                    ["ProcessorNameString"]).get("ProcessorNameString"),
            "logical_processors": os.cpu_count(),
            "ram_gb": None,
            "gpu_adapters": [],
            "display_mode": None,
            "power": None,
        }
        if isinstance(facts["cpu"], str):
            facts["cpu"] = facts["cpu"].strip()
        memory = _MEMORYSTATUSEX()
        memory.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if _kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            facts["ram_gb"] = round(memory.ullTotalPhys / 2 ** 30, 1)
        display_class = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        for index in range(10):
            adapter = _registry_values(winreg.HKEY_LOCAL_MACHINE, display_class + "\\%04d" % index,
                                       ["DriverDesc", "DriverVersion", "DriverDate", "ProviderName"])
            if adapter.get("DriverDesc"):
                facts["gpu_adapters"].append({k: adapter.get(k) for k in ("DriverDesc", "DriverVersion", "DriverDate",
                                                                          "ProviderName")})
        mode = _DEVMODEW()
        mode.dmSize = ctypes.sizeof(_DEVMODEW)
        if _user32.EnumDisplaySettingsW(None, _ENUM_CURRENT_SETTINGS, ctypes.byref(mode)):
            facts["display_mode"] = f"{mode.dmPelsWidth}x{mode.dmPelsHeight} @ {mode.dmDisplayFrequency} Hz"
        status = _SYSTEM_POWER_STATUS()
        if _kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            facts["power"] = {
                "ac_power": {0: False, 1: True}.get(status.ACLineStatus),
                "battery_percent": None if status.BatteryLifePercent == 255 else status.BatteryLifePercent,
                "battery_saver_on": bool(status.SystemStatusFlag & 1),
            }
        scheme = command_output(["powercfg", "/getactivescheme"])
        if scheme and facts["power"] is not None:
            match = re.search(r"([0-9a-fA-F-]{36})\s*\((.*)\)", scheme)
            facts["power"]["scheme"] = {"guid": match.group(1), "name": match.group(2)} if match else scheme[:120]
        overlay = _registry_values(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes",
                                   ["ActiveOverlayAcPowerScheme", "ActiveOverlayDcPowerScheme"])
        if overlay and facts["power"] is not None:
            facts["power"]["overlay"] = overlay
        return facts


# ------------------------------------------------------------------------------- facts
def linux_system_facts():
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


def system_facts():
    try:
        return windows_system_facts() if IS_WINDOWS else linux_system_facts()
    except Exception as error:  # facts are supporting evidence; never fail a run over them
        return {"error": f"{type(error).__name__}: {error}"[:300]}


def find_browser(name, override=None):
    """(path, where it was found) or (None, places searched). Never starts the browser."""
    if override:
        return (override, "given on the command line") if os.path.isfile(override) else (None, [override])
    info = BROWSERS[name]
    searched = []
    if IS_WINDOWS:
        roots = []
        for var, where in (("ProgramW6432", "Program Files"), ("ProgramFiles", "Program Files"),
                           ("ProgramFiles(x86)", "Program Files (x86)"), ("LOCALAPPDATA", "per-user install")):
            base = os.environ.get(var)
            if base and base not in [r for r, _ in roots]:
                roots.append((base, where))
        for relative in info["windows"]:
            for base, where in roots:
                candidate = os.path.join(base, relative)
                searched.append(display_path(candidate))
                if os.path.isfile(candidate):
                    return candidate, where
            found = _app_path(os.path.basename(relative))
            searched.append("App Paths registry: " + os.path.basename(relative))
            if found:
                return found, "App Paths registry"
        return None, searched
    for entry in info["linux"]:
        candidate = shutil.which(entry[6:]) if entry.startswith("which:") else entry
        searched.append(entry)
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate, "installed"
    return None, searched


def browser_version(name, binary):
    if IS_WINDOWS:
        # "--version" would open a browser window on Windows, so read the file's version.
        try:
            version = windows_file_version(binary)
        except OSError:
            version = None
        if not version:
            folder = os.path.dirname(binary)
            numbered = [d for d in os.listdir(folder) if re.match(r"^\d+(\.\d+){3}$", d)] if os.path.isdir(folder) else []
            if numbered:
                version = max(numbered, key=lambda d: tuple(int(x) for x in d.split(".")))
        return f"{BROWSERS[name]['label']} {version}" if version else BROWSERS[name]["label"]
    return command_output([binary, "--version"])


def python_description():
    executable = os.path.normcase(os.path.abspath(sys.executable))
    here = os.path.normcase(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    portable = executable.startswith(os.path.join(here, "runtime") + os.sep)
    return {"version": platform.python_version(), "implementation": platform.python_implementation(),
            "bits": 64 if sys.maxsize > 2 ** 32 else 32,
            "source": "portable copy in the test bundle" if portable else "installed on this computer"}


# ------------------------------------------------------------------------------- pages
LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VR-HE browser test</title>
<style>
  body { font: 16px/1.5 system-ui, sans-serif; margin: 2em auto; max-width: 44em; padding: 0 1em;
         background: #f6f6f4; color: #1d1d1b; }
  button { display: block; width: 100%; margin: 0.8em 0; padding: 0.9em 1.2em; border: 0; border-radius: 8px;
           background: #1f5fbf; color: #ffffff; font: inherit; font-weight: 600; text-align: left; cursor: pointer; }
  button.secondary { background: #55554f; }
  button:disabled { opacity: 0.6; cursor: wait; }
  .note { color: #45453f; }
</style>
</head>
<body>
<h1>VR-HE browser test</h1>
<p>Browser: <strong id="browser">checking...</strong></p>
<!-- Forms use POST so that a browser preloading links can never start a test by itself. -->
<form method="post" action="new">
  <input type="hidden" name="plan" value="baseline">
  <input type="hidden" name="browser" value="unknown">
  <button type="submit">1. Start the baseline test (about 2-4 minutes)</button>
</form>
<form method="post" action="new">
  <input type="hidden" name="plan" value="followup-500k">
  <input type="hidden" name="browser" value="unknown">
  <button type="submit" class="secondary">2. Optional, after the baseline: start the 500,000-splat follow-up</button>
</form>
<p class="note">Start one test at a time. Keep the window visible and leave the computer alone until the
black server window prints FINISHED (2-4 minutes).</p>
<script>
(function () {
  var ua = navigator.userAgent;
  var name = navigator.brave ? 'brave' : /Edg\\//.test(ua) ? 'edge' : /Firefox\\//.test(ua) ? 'firefox'
    : /Chrome\\//.test(ua) ? 'chrome' : 'unknown';
  var labels = { edge: 'Microsoft Edge', chrome: 'Google Chrome', firefox: 'Mozilla Firefox', brave: 'Brave',
                 unknown: 'not recognized (the test still works)' };
  document.getElementById('browser').textContent = labels[name];
  Array.prototype.forEach.call(document.forms, function (form) {
    form.elements.browser.value = name;
    form.addEventListener('submit', function () {
      Array.prototype.forEach.call(document.querySelectorAll('button'), function (b) { b.disabled = true; });
    });
  });
})();
</script>
</body>
</html>
"""

# Records the exact browser version (User-Agent Client Hints) and scaling facts, then opens the
# benchmark with the same query. It waits while the tab is hidden, because browsers pause
# animation in background tabs and the measurement would be meaningless. The facts are sent
# within 3 s at most; the benchmark itself is unchanged.
START_PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>VR-HE browser test - starting</title></head>
<body style="font: 16px system-ui, sans-serif; margin: 2em;">
<p id="message">Starting the VR-HE browser test...</p>
<script>
(function () {
  var params = new URLSearchParams(window.location.search);
  var run = (params.get('run') || 'manual').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 80) || 'manual';
  var target = 'index.html?' + params.toString();
  var visibleAtStart = document.visibilityState;
  var info = {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency || null,
    deviceMemoryGB: navigator.deviceMemory || null,
    devicePixelRatio: window.devicePixelRatio,
    screen: { width: screen.width, height: screen.height, availWidth: screen.availWidth,
              availHeight: screen.availHeight, colorDepth: screen.colorDepth },
    window: { innerWidth: window.innerWidth, innerHeight: window.innerHeight,
              outerWidth: window.outerWidth, outerHeight: window.outerHeight },
    crossOriginIsolated: window.crossOriginIsolated === true,
    visibilityAtStart: visibleAtStart
  };
  var sent = false;
  function go() {
    if (document.visibilityState === 'visible') {
      window.location.replace(target);
      return;
    }
    document.getElementById('message').textContent =
      'Waiting: click this tab to bring it to the front. The test starts when this page is visible.';
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') window.location.replace(target);
    });
  }
  function send(uaData) {
    if (sent) return;
    sent = true;
    info.userAgentData = uaData || null;
    try {
      fetch('report/' + encodeURIComponent(run) + '/client.json', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(info)
      }).then(go, go);
    } catch (e) { go(); }
  }
  window.setTimeout(function () { send(null); }, 3000);
  try {
    if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
      navigator.userAgentData.getHighEntropyValues(['architecture', 'bitness', 'fullVersionList',
        'platformVersion', 'wow64']).then(function (v) { send(v); }, function () { send(null); });
    } else {
      send(null);
    }
  } catch (e) { send(null); }
})();
</script>
</body>
</html>
"""


# ------------------------------------------------------------------------------- server
class BenchmarkHandler(http.server.BaseHTTPRequestHandler):
    server_version = "VRHEBench/2"
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

    def _redirect(self, location):
        self.send_response(303)  # "see other": the browser follows a POST with a GET
        self.send_header("Location", location)
        self._common_headers(0, "text/plain; charset=utf-8")
        self.end_headers()

    def _resolve_get(self, url_path):
        parts = [p for p in urllib.parse.unquote(url_path).split("/") if p]
        if not parts or not all(safe_name(p) for p in parts):
            return None
        if parts[0] == "fixtures":
            return os.path.join(self.server.fixtures_dir, parts[1]) if len(parts) == 2 else None
        candidate = os.path.realpath(os.path.join(self.server.build_dir, *parts))
        if not candidate.startswith(self.server.build_dir + os.sep):
            return None
        return candidate

    def do_GET(self):
        split = urllib.parse.urlsplit(self.path)
        if split.path == "/":
            if self.server.mode == "manual":
                self._send_text(200, LANDING_PAGE, "text/html; charset=utf-8")
            else:
                self._send_text(200, "VR-HE test server: an automatic run is in progress in another window.")
            return
        if split.path == "/start":
            self.server.page_requested()
            self._send_text(200, START_PAGE, "text/html; charset=utf-8")
            return
        if split.path == "/new":
            self._send_text(200, '<!DOCTYPE html><meta charset="utf-8"><title>VR-HE browser test</title>'
                                 '<p>Start tests with the buttons on <a href="/">the test page</a>.</p>',
                            "text/html; charset=utf-8")
            return
        if split.path == "/index.html":
            self.server.page_requested()
        path = self._resolve_get(split.path)
        if not path or not os.path.isfile(path):
            self._send_text(404, "not found")
            return
        size = os.path.getsize(path)
        self.send_response(200)
        self._common_headers(size, MIME.get(os.path.splitext(path)[1].lower(), "application/octet-stream"))
        self.end_headers()
        with open(path, "rb") as f:
            shutil.copyfileobj(f, self.wfile, 1 << 20)

    def _new_manual_run(self, form):
        if self.server.mode != "manual":
            self._send_text(404, "not found")
            return
        plan = (form.get("plan") or ["baseline"])[0]
        if plan not in PLANS:
            self._send_text(400, "unknown plan")
            return
        label = re.sub(r"[^a-z0-9]", "", (form.get("browser") or ["unknown"])[0].lower())[:20] or "unknown"
        page_query, busy = self.server.create_manual_run(label, plan)
        if page_query is None:
            self._send_text(409, '<!DOCTYPE html><meta charset="utf-8"><title>VR-HE browser test</title>'
                                 '<p style="font: 16px system-ui, sans-serif">Test <b>%s</b> is still running in '
                                 'another window. Wait until the black server window prints FINISHED, then '
                                 '<a href="/">start the next test</a>.</p>' % busy, "text/html; charset=utf-8")
            return
        self._redirect("/start?" + urllib.parse.urlencode(page_query))

    def do_POST(self):
        split_path = urllib.parse.urlsplit(self.path).path
        parts = [p for p in urllib.parse.unquote(split_path).split("/") if p]
        length = int(self.headers.get("Content-Length") or 0)
        if length > 64 * 1024 * 1024:
            self._send_text(413, "too large")
            return
        body = self.rfile.read(length) if length else b""
        if split_path == "/new":
            self._new_manual_run(urllib.parse.parse_qs(body.decode("ascii", "replace")))
            return
        if len(parts) == 3 and parts[0] == "report" and safe_name(parts[1]) and safe_name(parts[2]) \
                and parts[2] not in HARNESS_FILES:
            folder = os.path.join(self.server.results_dir, parts[1])
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, parts[2]), "wb") as f:
                f.write(body)
            self.server.touch(parts[1], parts[2])
            self._send_text(200, "ok")
            if parts[2] == "done.json":
                self.server.run_finished(parts[1])
            return
        if len(parts) == 2 and parts[0] == "log" and safe_name(parts[1]):
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
    # On Windows SO_REUSEADDR would let this server bind a port that another program is
    # already listening on, so it is off there and the port is claimed exclusively instead.
    allow_reuse_address = not IS_WINDOWS

    def __init__(self, port, build_dir, fixtures_dir, results_dir, access_log=None, mode="run", context=None):
        super().__init__(("127.0.0.1", port), BenchmarkHandler)
        self.build_dir = os.path.realpath(build_dir)
        self.fixtures_dir = os.path.realpath(fixtures_dir)
        self.results_dir = os.path.realpath(results_dir)
        self.access_log = access_log
        self.mode = mode
        self.context = context or {}
        self.log_lock = threading.Lock()
        self.report_lock = threading.Lock()
        self.last_activity = time.time()
        self.first_page_request = None
        self.run_activity = {}
        self.fatal_by_run = {}
        self.events = []
        self.manual_runs = {}

    def page_requested(self):
        if self.first_page_request is None:
            self.first_page_request = time.time()
        self.last_activity = time.time()

    def server_bind(self):
        if IS_WINDOWS and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        socketserver.TCPServer.server_bind(self)
        # HTTPServer.server_bind would look up a host name: slow on some networks, and on
        # Windows it returns the computer's name. The loopback address is all that is needed.
        self.server_name = "127.0.0.1"
        self.server_port = self.server_address[1]

    def touch(self, run, name, entries=None):
        self.last_activity = time.time()
        self.run_activity[run] = self.last_activity
        if name.endswith(".json") and not name.endswith(".frames.json") and \
                name not in ("env.json", "summary.json", "done.json", "client.json"):
            with self.log_lock:
                self.events.append((run, name[:-5]))
        for entry in entries or []:
            text = str(entry.get("text", ""))
            if entry.get("level") in ("error", "pageerror", "unhandledrejection") and any(p in text for p in FATAL_PATTERNS):
                with self.log_lock:
                    self.fatal_by_run.setdefault(run, []).append(text[:500])

    def take_events(self):
        with self.log_lock:
            events, self.events = self.events, []
        return events

    def create_manual_run(self, label, plan):
        """Create a run folder for a test started from the landing page. Returns (page query,
        None), or (None, busy run id) while another manual test is still reporting."""
        with self.report_lock:
            for other, record in list(self.manual_runs.items()):
                if time.time() - self.run_activity.get(other, record["_created"]) < MANUAL_STALE_SECONDS:
                    return None, other
                # No reports for a long time: the page was closed or failed. Record and move on.
                self.manual_runs.pop(other)
                record.pop("_created", None)
                record["finished"] = now_iso()
                record["outcome"] = f"abandoned (no reports for {MANUAL_STALE_SECONDS} s)"
                record["fatal_lines"] = self.fatal_by_run.get(other, [])[:20]
                other_dir = os.path.join(self.results_dir, other)
                write_json(os.path.join(other_dir, "harness.json"), record)
                with open(os.path.join(other_dir, "summary.txt"), "w", encoding="utf-8") as f:
                    f.write(completion_report(other_dir, record, os.path.join("results", other), None) + "\n")
                print(f"\nRun {other} stopped reporting and was recorded as abandoned.", flush=True)
            run_id = new_run_id(self.results_dir, self.context.get("run_prefix", "run"), label + "-manual", plan)
            os.makedirs(os.path.join(self.results_dir, run_id))
            query = {"run": run_id, "browser": label}
            query.update(PLANS[plan])
            record = base_record(run_id, plan, self.context)
            record.update({
                "mode": "manual (browser opened by the tester)",
                "browser": label,
                "label": label,
                "browser_label": label,
                "browser_version": "see client.json (reported by the browser)",
                "profile": "the tester's own browser profile or private window",
                "harness_flags": [],
                "url_query": query,
                "port": self.server_address[1],
            })
            write_json(os.path.join(self.results_dir, run_id, "harness.json"), record)
            record["_created"] = time.time()
            self.manual_runs[run_id] = record
        print(f"\nStarted the {PLAN_TITLES[plan]} test ({label}) as run {run_id}. "
              "Leave the browser window visible until this window prints FINISHED.", flush=True)
        return query, None

    def run_finished(self, run):
        if self.mode != "manual" or run not in self.manual_runs:
            return
        with self.report_lock:
            record = self.manual_runs.pop(run, None)
            if record is None:
                return
            record.pop("_created", None)
            run_dir = os.path.join(self.results_dir, run)
            record["finished"] = now_iso()
            record["outcome"] = "done"
            record["fatal_lines"] = self.fatal_by_run.get(run, [])[:20]
            write_json(os.path.join(run_dir, "harness.json"), record)
            text = completion_report(run_dir, record, os.path.join(self.results_dir, run),
                                     "Start the next test from the browser page, or press Ctrl+C here when finished.")
            with open(os.path.join(run_dir, "summary.txt"), "w", encoding="utf-8") as f:
                f.write(completion_report(run_dir, record, os.path.join("results", run), None))
            print(text, flush=True)


def open_server(preferred_ports, **kwargs):
    """Bind 127.0.0.1 on the first free preferred port; 0 asks the OS for any free port."""
    last_error = None
    for port in preferred_ports:
        if port in RESERVED_PORTS:
            continue
        try:
            return BenchmarkServer(port, **kwargs)
        except OSError as error:
            last_error = error
    raise SystemExit(f"Could not open a local port for the test server: {last_error}")


def requested_ports(args, fallback):
    if not args.port:
        return list(fallback)
    if args.port in RESERVED_PORTS:
        print(f"Port {args.port} is reserved for another tool and is never used; choosing a free port instead.")
        return list(fallback)
    return [args.port] + [p for p in fallback if p != args.port]


# ------------------------------------------------------------------------------- records
def new_run_id(results_dir, prefix, label, plan):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = re.sub(r"[^A-Za-z0-9_-]", "", f"{prefix}-{stamp}-{label}-{plan}")[:72]
    run_id, n = base, 2
    while os.path.exists(os.path.join(results_dir, run_id)):
        run_id, n = f"{base}-{n}", n + 1
    return run_id


def base_record(run_id, plan, context):
    record = {
        "run": run_id,
        "harness_version": HARNESS_VERSION,
        "platform": "windows" if IS_WINDOWS else "linux",
        "plan": plan,
        "plan_query": PLANS.get(plan),
        "python": python_description(),
        "server": "127.0.0.1 (COOP same-origin, COEP require-corp, no-store, no compression)",
        "system": context.get("system") or system_facts(),
        "started": now_iso(),
    }
    bundle = context.get("bundle")
    if bundle:
        record["bundle"] = {k: bundle.get(k) for k in ("bundle_name", "bundle_version", "created", "source_commit",
                                                       "source_dirty")}
    return record


def stat(result, key, field):
    block = result.get(key) or {}
    return block.get(field) if block.get("count") else None


def frame_pacing(run_dir, case_name):
    data = load_json(os.path.join(run_dir, case_name + ".frames.json")) or {}
    intervals = [float(x) for x in data.get("intervalMs") or [] if isinstance(x, (int, float))]
    if not intervals:
        return None
    total = sum(intervals)
    slow = [x for x in intervals if x >= SLOW_FRAME_MS]
    return {
        "frames": len(intervals),
        "slow_frames": len(slow),
        "slow_fraction": len(slow) / len(intervals),
        "slow_time_fraction": (sum(slow) / total) if total else 0.0,
        "longest_ms": max(intervals),
        "stalls": sum(1 for x in intervals if x >= STALL_MS),
    }


def run_results(run_dir):
    summary = load_json(os.path.join(run_dir, "summary.json"))
    if summary and summary.get("results"):
        return summary.get("results"), summary
    results = []
    for name in sorted(os.listdir(run_dir)) if os.path.isdir(run_dir) else []:
        if name.endswith(".json") and name.startswith(("overlap_", "scale_")) and not name.endswith(".frames.json"):
            data = load_json(os.path.join(run_dir, name))
            if data:
                results.append(data)
    return results, summary


def console_counts(run_dir):
    errors, warnings, known = 0, 0, 0
    try:
        with open(os.path.join(run_dir, "console.jsonl"), encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                level = entry.get("level")
                if level in ("error", "pageerror", "unhandledrejection"):
                    errors += 1
                elif level == "warn":
                    if KNOWN_WARNING in str(entry.get("text", "")):
                        known += 1
                    else:
                        warnings += 1
    except OSError:
        pass
    return errors, warnings, known


def client_browser_version(client):
    """'Microsoft Edge 142.0.3595.53' from the browser's own User-Agent Client Hints, if sent."""
    brands = ((client.get("userAgentData") or {}).get("fullVersionList")) or []
    names = {"Microsoft Edge": "Microsoft Edge", "Google Chrome": "Google Chrome", "Brave": "Brave",
             "Chromium": "Chromium"}
    by_brand = {b.get("brand"): b.get("version") for b in brands if isinstance(b, dict)}
    for brand in ("Microsoft Edge", "Google Chrome", "Brave", "Chromium"):
        if by_brand.get(brand):
            return f"{names[brand]} {by_brand[brand]}"
    ua = client.get("userAgent") or ""
    match = re.search(r"Firefox/([0-9.]+)", ua)
    return f"Mozilla Firefox {match.group(1)}" if match else None


def case_title(name):
    if name.startswith("scale_"):
        token = name[6:]
        count = token.replace("_sh3", "")
        return f"{int(count):,} splats" + (" (SH3)" if token.endswith("_sh3") else "") if count.isdigit() else name
    return name.replace("overlap_", "overlap: ")


def completion_report(run_dir, record, results_location, next_hint):
    """Plain-language end-of-run text. ASCII only, so any Windows console can show it."""
    results, summary = run_results(run_dir)
    env = load_json(os.path.join(run_dir, "env.json")) or {}
    try:
        gl = json.loads(env.get("browserInfoJson") or "{}")
    except ValueError:
        gl = {}
    client = load_json(os.path.join(run_dir, "client.json")) or {}
    outcome = record.get("outcome")
    finished = outcome == "done" and summary is not None
    reported = client_browser_version(client)
    browser = record.get("browser_version")
    if not browser or browser.startswith("see client.json"):
        browser = reported or record.get("browser_label") or record.get("browser")
    bar = "=" * 78
    lines = [bar, ("FINISHED" if finished else "DID NOT FINISH") + ": " + f"{browser} - "
             f"{PLAN_TITLES.get(record.get('plan'), record.get('plan') or 'custom')} test",
             f"Run: {record.get('run')}"]
    if not finished:
        lines.append(f"Outcome: {outcome}. Partial results, if any, are listed below.")
    system = record.get("system") or {}
    windows = system.get("windows") or {}
    if windows:
        lines.append(f"Windows: {windows.get('product')} {windows.get('display_version') or ''} "
                     f"(build {windows.get('build')})".replace("  ", " "))
    if record.get("handed_off"):
        lines.append("NOTE: the page ran in an already-open browser window, not the clean test profile.")
    renderer = gl.get("unmaskedRenderer") or gl.get("glRenderer") or env.get("graphicsDeviceName")
    if renderer:
        lines.append(f"Graphics: {renderer} | {gl.get('glVersion') or env.get('graphicsDeviceVersion')}")
        if any(s in str(renderer).lower() for s in SOFTWARE_RENDERERS):
            lines.append("WARNING: the browser used software rendering, not the graphics chip. These results do not "
                         "represent the GPU.")
    elif results:
        lines.append("Graphics: not reported")
    if env:
        scaling = gl.get("devicePixelRatio") or client.get("devicePixelRatio")
        lines.append(f"Canvas {env.get('screenWidth')}x{env.get('screenHeight')}, quality {env.get('qualityLevel')}, "
                     f"render scale {env.get('renderScale')}" + (f", display scaling {scaling}" if scaling else ""))
    lines.append("")
    if results:
        lines.append("Frame rate against the 30 fps browser floor (a description, not a pass/fail verdict):")
        lines.append(f"  {'Case':<44}{'Avg fps':>8}{'Median':>8}{'95th':>7}{'Slow':>7}{'Longest':>9}{'Stalls':>7}")
        for r in results:
            pacing = frame_pacing(run_dir, r.get("caseName", ""))
            fps = r.get("fpsFromMeanInterval")
            median, p95 = stat(r, "intervalMs", "median"), stat(r, "intervalMs", "p95")
            flag = " <30" if isinstance(fps, (int, float)) and fps < FLOOR_FPS else ""
            if r.get("status") != "ok":
                flag += f" [{r.get('status')}: {str(r.get('error') or '')[:60]}]"
            # Plain concatenation keeps this readable by Python 3.8-3.11 (no nested quotes).
            cells = [
                "%.1f" % fps if isinstance(fps, (int, float)) else "-",
                "%.0fms" % median if isinstance(median, (int, float)) else "-",
                "%.0fms" % p95 if isinstance(p95, (int, float)) else "-",
                "%.0f%%" % (100 * pacing["slow_fraction"]) if pacing else "-",
                "%.0fms" % pacing["longest_ms"] if pacing else "-",
                str(pacing["stalls"]) if pacing else "-",
            ]
            lines.append("  " + case_title(r.get("caseName", "?")).ljust(44) + cells[0].rjust(8) + cells[1].rjust(8)
                         + cells[2].rjust(7) + cells[3].rjust(7) + cells[4].rjust(9) + cells[5].rjust(7) + flag)
        lines.append("  Slow = frames of 36 ms or longer (30 fps is 33.3 ms per frame; the timer has 1 ms steps).")
        lines.append("  Stalls = frames of 100 ms or longer. Loading time is measured separately.")
        lines.append("")
        checked = [r for r in results if r.get("caseName") in EXPECTED_OVERLAP and r.get("regions")]
        differ = []
        for r in checked:
            regions = {g.get("name"): g.get("nearest") for g in r.get("regions") or []}
            seen = (regions.get("a_only"), regions.get("shared_band"), regions.get("b_only"))
            if seen != EXPECTED_OVERLAP[r["caseName"]]:
                differ.append(f"{r['caseName']} showed {'/'.join(str(s) for s in seen)}")
        if checked:
            lines.append(f"Overlap drawing order: {len(checked) - len(differ)} of {len(checked)} cases match the "
                         "development-laptop pattern." + ("" if differ else " (Merged sections draw correctly; the "
                                                          "separate-renderer cases reproduce the known errors.)"))
            lines.extend("  DIFFERENT: " + d for d in differ)
        heap = [r.get("wasmHeapMbAfterMeasure") for r in results if isinstance(r.get("wasmHeapMbAfterMeasure"), (int, float))]
        if heap:
            lines.append(f"Peak WebAssembly memory in this page: {max(heap):.0f} MB.")
    else:
        lines.append("No test results were received from the page.")
    errors, warnings, known = console_counts(run_dir)
    lines.append(f"Browser console: {errors} error(s), {warnings} unexpected warning(s)"
                 + (f", {known} expected CPU-sort notice" if known else "") + ".")
    cleanup = record.get("cleanup") or {}
    if cleanup.get("leftover_processes"):
        lines.append(f"Note: {len(cleanup['leftover_processes'])} test browser process(es) could not be stopped; "
                     "close the test browser window yourself.")
    if cleanup and cleanup.get("profile_deleted") is False:
        lines.append("Note: the temporary browser profile could not be deleted yet; Windows removes it with other "
                     "temporary files.")
    lines.append("")
    lines.append("Results folder:")
    lines.append("  " + results_location)
    if next_hint:
        lines.append("")
        lines.append(next_hint)
    lines.append(bar)
    return "\n".join(lines)


# ------------------------------------------------------------------------------- bundle
def resolve_paths(args):
    """Build, fixture and results folders from --bundle or the individual options."""
    bundle_root, manifest = None, None
    if args.bundle:
        bundle_root = os.path.abspath(args.bundle)
        manifest = load_json(os.path.join(bundle_root, "bundle.json"))
        args.build = args.build or os.path.join(bundle_root, "app")
        args.fixtures = args.fixtures or os.path.join(bundle_root, "fixtures")
        args.results = args.results or os.path.join(bundle_root, "results")
    missing = [n for n in ("build", "fixtures", "results") if not getattr(args, n, None)]
    if missing:
        raise SystemExit("Give --bundle, or all of --build, --fixtures and --results (missing: " + ", ".join(missing) + ")")
    os.makedirs(args.results, exist_ok=True)
    return bundle_root, manifest


def folder_notes(bundle_root):
    """Warn about folder locations that can disturb a Windows test run."""
    if len(bundle_root) > 150:
        print("Note: this folder's path is long. If saving results fails, extract the ZIP into a shorter folder,")
        print("for example directly inside Downloads.")
    for var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        base = os.environ.get(var)
        if base and os.path.normcase(bundle_root).startswith(os.path.normcase(os.path.abspath(base)) + os.sep):
            print("Note: this folder is synced by OneDrive. Syncing during the test can disturb the measurements;")
            print("a folder such as Downloads is better. The test data is synthetic, so syncing it is harmless.")
            break


def finished_runs(results_dir, browser, plan):
    found = []
    for name in sorted(os.listdir(results_dir)) if os.path.isdir(results_dir) else []:
        record = load_json(os.path.join(results_dir, name, "harness.json")) or {}
        if record.get("browser") == browser and record.get("plan") == plan and record.get("outcome") == "done":
            found.append(name)
    return found


def verify_bundle(bundle_root, manifest):
    """Check the test inputs against the checksums written when the bundle was made."""
    if not manifest:
        return True
    files = manifest.get("verify") or {}
    problems = []
    for relative, meta in sorted(files.items()):
        path = os.path.join(bundle_root, *relative.split("/"))
        if not os.path.isfile(path):
            problems.append(relative + " is missing")
        elif os.path.getsize(path) != meta.get("size"):
            problems.append(relative + " has the wrong size")
        elif sha256_file(path) != meta.get("sha256"):
            problems.append(relative + " is damaged (checksum differs)")
    if problems:
        print("The test files are incomplete or damaged:")
        for p in problems[:10]:
            print("  " + p)
        print("Delete this folder, extract the ZIP again and retry.")
        return False
    print(f"Test files verified ({len(files)} files match the bundle's checksums).")
    return True


# ------------------------------------------------------------------------------- commands
def build_command(name, binary, profile, url):
    family = BROWSERS[name]["family"]
    if family == "chromium":
        return [binary, f"--user-data-dir={profile}"] + chromium_flags() + [url]
    if family == "firefox":
        with open(os.path.join(profile, "user.js"), "w", encoding="utf-8") as f:
            for key, value in FIREFOX_PREFS.items():
                f.write(f"user_pref({json.dumps(key)}, {json.dumps(value)});\n")
        return [binary, "--no-remote", "--new-instance", "--profile", profile, "-width", "1400", "-height", "960", url]
    raise ValueError(name)


def stop_linux_session(proc, profile):
    """Stop only the browser session started by this harness (its own process group)."""
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
    time.sleep(0.5)
    remaining = command_output(["pgrep", "-f", profile])
    return [int(p) for p in (remaining or "").split() if p.isdigit()]


def run(args):
    bundle_root, manifest = resolve_paths(args)
    plan = args.plan or "custom"
    if args.plan and args.plan not in PLANS:
        raise SystemExit("unknown plan: " + args.plan)
    label = BROWSERS[args.browser]["label"]
    print(f"VR-HE browser test - {label}, {PLAN_TITLES.get(plan, plan)} test")
    py = python_description()
    print(f"Python {py['version']} ({py['source']}).")

    build = os.path.realpath(args.build)
    if not os.path.isfile(os.path.join(build, "index.html")):
        print(f"The test page is missing: {os.path.join(build, 'index.html')}")
        return 2
    if bundle_root:
        if not verify_bundle(bundle_root, manifest):
            return 2
        folder_notes(bundle_root)
    if plan == "followup-500k" and not args.skip_baseline_check and \
            not finished_runs(args.results, args.browser, "baseline"):
        print(f"The 500k follow-up is meant for after the baseline, and no finished {label} baseline was found")
        print("in the results folder. Run the baseline for this browser first (RUN-EDGE.cmd or RUN-CHROME.cmd).")
        return 4
    profile_root = args.profile_root or os.path.join(tempfile.gettempdir(), "vrhe-p" if IS_WINDOWS else "vrhe-browser-profiles")
    os.makedirs(profile_root, exist_ok=True)
    if not (free_space_ok(args.results, "results") and free_space_ok(profile_root, "temporary browser profile")):
        return 2

    binary, where = find_browser(args.browser, args.binary)
    if not binary:
        print(f"{label} was not found on this computer, so it is UNTESTED here.")
        print("Looked in: " + "; ".join(where))
        print("That is a valid result. Continue with the next step in START-HERE.txt." if bundle_root else "")
        return 3
    version = browser_version(args.browser, binary)
    print(f"Found {version or label} ({where}).")

    run_id = args.run or new_run_id(args.results, args.run_prefix, args.browser, plan)
    if not safe_name(run_id) or len(run_id) > 80:
        raise SystemExit("run id must be a simple name of at most 80 characters: " + SAFE_NAME.pattern)
    run_dir = os.path.join(os.path.realpath(args.results), run_id)
    if os.path.exists(run_dir):
        raise SystemExit(f"run folder already exists: {run_dir}")
    os.makedirs(run_dir)
    if IS_WINDOWS:
        profile = tempfile.mkdtemp(prefix="vrhe-", dir=profile_root)  # short: Chromium's own paths are deep
    else:
        profile = tempfile.mkdtemp(prefix=f"{run_id}-", dir=profile_root)

    context = {"system": system_facts(), "bundle": manifest, "run_prefix": args.run_prefix}
    access_log = open(os.path.join(run_dir, "server.log"), "w", encoding="utf-8")
    server = open_server(requested_ports(args, [0]), build_dir=build, fixtures_dir=args.fixtures,
                         results_dir=args.results, access_log=access_log, mode="run", context=context)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    query = {"run": run_id, "browser": args.label or args.browser}
    query.update(PLANS.get(plan, {}))
    for item in args.query or []:
        key, _, value = item.partition("=")
        query[key] = value
    url = f"http://127.0.0.1:{port}/start?" + urllib.parse.urlencode(query)
    command = build_command(args.browser, binary, profile, url)

    record = base_record(run_id, plan, context)
    record.update({
        "mode": "automatic (browser started by the harness)",
        "browser": args.browser,
        "label": args.label or args.browser,
        "browser_label": label,
        "browser_version": version,
        "browser_family": BROWSERS[args.browser]["family"],
        "browser_install": where,
        "browser_binary": display_path(binary),
        "harness_flags": [c for c in command[1:] if c.startswith("-") and not c.startswith("--user-data-dir")],
        "profile": "fresh temporary profile (deleted after the run)",
        "url_query": query,
        "port": port,
    })

    print(f"Local test server: http://127.0.0.1:{port}/ (this computer only).")
    print(f"Opening {label} with a fresh temporary profile. Your own {label} windows and profile are not touched.")
    print("Keep the test window visible and leave the computer alone. This usually takes 2-4 minutes.")
    browser_log = open(os.path.join(run_dir, "browser-stdout.log"), "wb")
    popen_options = {"stdout": browser_log, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
    if IS_WINDOWS:
        popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_options["start_new_session"] = True
    started = time.time()
    proc = subprocess.Popen(command, **popen_options)
    tree = WindowsProcessTree(proc.pid) if IS_WINDOWS else None
    outcome = "timeout"
    deadline = started + args.timeout
    fatal_seen_at = None
    exited_at = None
    handed_off = False
    next_refresh = 0.0
    try:
        while time.time() < deadline:
            for event_run, case in server.take_events():
                if event_run == run_id:
                    print(f"  [{int(time.time() - started) // 60:02d}:{int(time.time() - started) % 60:02d}] "
                          f"finished {case_title(case)}", flush=True)
            if os.path.exists(os.path.join(run_dir, "done.json")):
                outcome = "done"
                time.sleep(2)  # let any trailing uploads land
                break
            if proc.poll() is not None and args.browser != "firefox" and not handed_off:
                if exited_at is None:
                    exited_at = time.time()
                # On Windows a browser that exits within seconds may have passed the page to a
                # window that was already open, for example when a company policy fixes the
                # profile folder. Give that window a moment to ask for the page.
                if not IS_WINDOWS or exited_at - started > 6:
                    outcome = f"browser closed ({proc.returncode}) before the test finished"
                    break
                if server.first_page_request is not None:
                    handed_off = True
                    print(f"Note: {label} passed the test page to a {label} window that was already open (a company")
                    print("policy or setting may prevent separate test profiles). The test continues in that window;")
                    print("its extensions and settings may affect the results. Close that tab yourself afterwards.")
                elif time.time() - exited_at > 20:
                    outcome = f"browser exited ({proc.returncode}) without opening the test page"
                    break
            if server.first_page_request is None and time.time() - started > args.open_timeout:
                outcome = (f"the browser did not open the test page within {args.open_timeout} s (it may be showing "
                           "a sign-in, welcome or policy screen)")
                break
            fatal = server.fatal_by_run.get(run_id)
            if fatal and fatal_seen_at is None:
                fatal_seen_at = time.time()
                print("fatal page error:", fatal[0][:200])
            if fatal_seen_at and time.time() - fatal_seen_at > 15:
                outcome = "page error"
                break
            if time.time() - server.last_activity > args.stall:
                outcome = f"stalled ({args.stall} s without reports)"
                break
            if tree is not None and time.time() >= next_refresh:
                tree.refresh()
                next_refresh = time.time() + 3
            time.sleep(1)
    except KeyboardInterrupt:
        outcome = "stopped by the tester (Ctrl+C)"
    finally:
        print("Closing the test browser...", flush=True)
        leftovers = tree.stop(proc) if tree is not None else stop_linux_session(proc, profile)
        server.shutdown()
        server.server_close()
        access_log.close()
        browser_log.close()
        profile_deleted = None
        if not args.keep_profile:
            profile_deleted = remove_tree(profile)

    record["finished"] = now_iso()
    record["outcome"] = outcome
    record["fatal_lines"] = server.fatal_by_run.get(run_id, [])[:20]
    record["cleanup"] = {"leftover_processes": leftovers, "profile_deleted": profile_deleted}
    if handed_off:
        record["profile"] = ("handed to an already-open browser window: the temporary profile and harness flags "
                             "were NOT in effect")
        record["handed_off"] = True
    write_json(os.path.join(run_dir, "harness.json"), record)
    hint = None
    if bundle_root:
        if outcome == "done" and plan == "baseline":
            hint = ("Next (see START-HERE.txt): the baseline in the other browser, the optional 500k follow-ups, "
                    "then COLLECT-RESULTS.cmd.")
        elif outcome == "done":
            hint = "Next (see START-HERE.txt): the other optional follow-up if you like, then COLLECT-RESULTS.cmd."
        elif server.first_page_request is None:
            hint = ("The test page never opened. Close any test browser window that is still open, then try "
                    "MANUAL-SERVER.cmd (see START-HERE.txt).")
        else:
            hint = "See 'If something goes wrong' in START-HERE.txt. Partial results are kept."
    print(completion_report(run_dir, record, run_dir, hint))
    with open(os.path.join(run_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(completion_report(run_dir, record, os.path.join("results", run_id), None) + "\n")
    return 0 if outcome == "done" else 2


def serve(args):
    bundle_root, manifest = resolve_paths(args)
    if bundle_root and not verify_bundle(bundle_root, manifest):
        return 2
    context = {"system": system_facts(), "bundle": manifest, "run_prefix": args.run_prefix}
    access_log = open(os.path.join(args.results, "manual-server.log"), "a", encoding="utf-8")
    server = open_server(requested_ports(args, list(MANUAL_PORTS) + [0]), build_dir=args.build,
                         fixtures_dir=args.fixtures, results_dir=args.results, access_log=access_log,
                         mode="manual", context=context)
    port = server.server_address[1]
    print("")
    print("Manual test server is running (this computer only).")
    print("1. Open Microsoft Edge or Google Chrome yourself. An InPrivate or Incognito window is best.")
    print(f"2. Go to this address:   http://127.0.0.1:{port}/")
    print("3. Click the baseline button and leave the computer alone until this window prints FINISHED.")
    print("   This window then prints a summary. Repeat in the other browser if you like.")
    print("Results are saved in:")
    print("  " + os.path.realpath(args.results))
    print("When you are finished, press Ctrl+C here (or close this window).")
    print(f"(Direct benchmark page without the menu: http://127.0.0.1:{port}/index.html?run=<name>)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nManual test server stopped.")
    finally:
        server.server_close()
        access_log.close()
    return 0


TEXT_SUFFIXES = (".json", ".jsonl", ".log", ".txt")
OWN_WORDS = frozenset(set(BROWSERS) | set(PLANS) | {part for plan in PLANS for part in plan.split("-")} | {
    "run", "test", "tests", "done", "manual", "results", "user", "users", "windows", "microsoft", "google",
    "python", "intel", "unity", "webgl", "local", "localhost", "true", "false", "null", "none", "default"})
# A user folder in a path, in plain, JSON-escaped or forward-slash form: C:\Users\<name>. Folder
# names may contain spaces, so the name runs to the next separator, quote or line end; replacing
# a little too much of a log line is the safe direction.
USER_FOLDER = re.compile(r"(?i)(\\\\|\\|/)(Users)(\\\\|\\|/)([^\\/\"'<>|?*\r\n]+)")


def scrubbers():
    """Replacements applied to text files copied into the results ZIP. The harness never
    records these on purpose; this catches anything a browser might print into its own logs."""
    rules = [(USER_FOLDER, lambda m: m.group(1) + m.group(2) + m.group(3) + "<user>")]
    for var, placeholder in (("COMPUTERNAME", "<computer>"), ("USERDOMAIN", "<domain>"), ("USERNAME", "<user>")):
        value = os.environ.get(var)
        # Skip names that are also ordinary words in these records, so the data stays intact.
        if value and len(value) >= 3 and value.lower() not in OWN_WORDS:
            # Letters and digits only count as part of a word: a name joined by "-", "_" or "."
            # (for example in a folder name) is still found.
            rules.append((re.compile(r"(?i)(?<![A-Za-z0-9])" + re.escape(value) + r"(?![A-Za-z0-9])"),
                          lambda m, p=placeholder: p))
    return rules


def scrub_text(data, rules):
    text = data.decode("utf-8", "replace")
    count = 0
    for pattern, replacement in rules:
        text, n = pattern.subn(replacement, text)
        count += n
    return text.encode("utf-8"), count


def collect(args):
    if not args.bundle and not args.results:
        raise SystemExit("Give --bundle or --results")
    root = os.path.abspath(args.bundle) if args.bundle else os.path.dirname(os.path.abspath(args.results))
    results = os.path.abspath(args.results or os.path.join(root, "results"))
    runs = [d for d in sorted(os.listdir(results)) if os.path.isdir(os.path.join(results, d))] if os.path.isdir(results) else []
    if not runs:
        print("There are no results yet. Run RUN-EDGE.cmd or RUN-CHROME.cmd first.")
        return 1
    if not free_space_ok(root, "results ZIP"):
        return 2
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.join(root, f"VRHE-results-{stamp}.zip")
    rules = scrubbers()
    scrubbed = {}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        manifest = os.path.join(root, "bundle.json")
        if os.path.isfile(manifest):
            archive.write(manifest, "bundle.json")
        for folder, dirs, files in os.walk(results):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(folder, name)
                arcname = os.path.relpath(full, os.path.dirname(results)).replace(os.sep, "/")
                if name.lower().endswith(TEXT_SUFFIXES):
                    with open(full, "rb") as f:
                        data, count = scrub_text(f.read(), rules)
                    if count:
                        scrubbed[arcname] = count
                    archive.writestr(arcname, data)
                else:
                    archive.write(full, arcname)
        archive.writestr("collect.json", json.dumps({
            "created": now_iso(), "harness_version": HARNESS_VERSION, "runs": runs,
            "note": "Text files had user-folder, user, domain and computer names replaced by placeholders; "
                    "the count of replacements per file is listed. The originals stay on the test PC.",
            "replacements": scrubbed}, indent=2))
    size_mb = os.path.getsize(out) / 2 ** 20
    print(f"Packed {len(runs)} run folder(s) into one file ({size_mb:.1f} MB):")
    print("  " + out)
    if scrubbed:
        print(f"({sum(scrubbed.values())} user or computer name(s) in browser logs were replaced by placeholders.)")
    print("Copy this one file to the USB drive and bring it back to the development laptop.")
    if IS_WINDOWS and not args.no_open:
        try:
            subprocess.Popen(f'explorer.exe /select,"{out}"')
        except OSError:
            pass
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "run", "collect"):
        p = sub.add_parser(name)
        p.add_argument("--bundle", help="test-bundle folder containing app/, fixtures/ and results/")
        p.add_argument("--build")
        p.add_argument("--fixtures")
        p.add_argument("--results")
        p.add_argument("--port", type=int, default=0)
        p.add_argument("--run-prefix", default="run", help="prefix for generated run ids")
    r = sub.choices["run"]
    r.add_argument("--browser", required=True, choices=sorted(BROWSERS))
    r.add_argument("--binary")
    r.add_argument("--run", help="run id (default: generated from time, browser and plan)")
    r.add_argument("--label")
    r.add_argument("--plan", choices=sorted(PLANS), help="page-parameter preset for the reference-PC tests")
    r.add_argument("--query", action="append", help="extra page parameter key=value (repeatable)")
    r.add_argument("--timeout", type=int, default=900)
    r.add_argument("--stall", type=int, default=240)
    r.add_argument("--open-timeout", type=int, default=90,
                   help="seconds to wait for the browser to request the test page")
    r.add_argument("--profile-root", help="folder for temporary browser profiles (default: system temp)")
    r.add_argument("--keep-profile", action="store_true")
    r.add_argument("--skip-baseline-check", action="store_true",
                   help="allow the follow-up plan without a finished baseline for the same browser")
    sub.choices["collect"].add_argument("--no-open", action="store_true", help="do not open Explorer afterwards")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(line_buffering=True)  # progress reaches logs and consoles at once
    except (AttributeError, ValueError):
        pass
    if args.command == "run":
        return run(args)
    if args.command == "serve":
        return serve(args)
    return collect(args)


if __name__ == "__main__":
    sys.exit(main())
