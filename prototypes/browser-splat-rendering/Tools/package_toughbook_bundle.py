#!/usr/bin/env python3
"""Build the Windows browser-test bundle (one ZIP) for the browser reference PC.

The reference PC is the Toughbook FZ-55 (D033). The ZIP holds the existing Unity WebGL 2
benchmark build, freshly generated synthetic fixtures, the local test server, Windows
launchers, plain-language instructions and a portable Python fallback. It holds no
operational data, credentials or personal identifiers.

Inputs, all on the development laptop:
  Builds/WebGL/                        the existing benchmark build (this script never rebuilds it)
  Tools/generate_synthetic_splats.py   regenerates the fixtures used by the reference-PC plans
  Tools/browser_test_harness.py        local test server and browser launcher
  Tools/windows-bundle/                launchers and instructions (LF in Git, CRLF in the ZIP)
  Bundles/cache/<Python embeddable ZIP>  portable Python, checked against a pinned SHA-256
  Library/PackageCache/                license notices of the packages compiled into the build

Output (ignored by Git):
  Bundles/VRHE-Toughbook-Browser-Test-<yyyymmdd>-<commit>.zip and the same name + .sha256

Privacy: IL2CPP compiles the Unity Editor's install path into some error-message strings in
WebGL.wasm. Where that path lies inside the developer's home folder, the bundle's copy has the
folder name replaced by the same number of "x" characters: data bytes only, same file size, no
code change. Both hashes are recorded. Every bundled file is then scanned for the home path,
the account name and the global Git identity, and the script fails if any remain. The values
are read at run time, so no name is written into this source file.

Usage (from any folder):
  python3 -I Tools/package_toughbook_bundle.py [--allow-dirty] [--keep-staging]
"""

import argparse
import datetime
import getpass
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import zipfile

sys.dont_write_bytecode = True  # importing the harness below must not leave __pycache__ behind

TOOLS = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(TOOLS)
BUNDLES = os.path.join(PROTO, "Bundles")
BUNDLE_NAME = "VRHE-Toughbook-Browser-Test"
BUNDLE_VERSION = "1"
UNITY_VERSION = "6000.3.15f1"
FIXTURE_COUNTS = "25000,100000,250000,500000"

PYTHON = {
    "version": "3.14.10",
    "package": "Windows embeddable package (64-bit, amd64), unmodified",
    "file": "python-3.14.10-embed-amd64.zip",
    "url": "https://www.python.org/ftp/python/3.14.10/python-3.14.10-embed-amd64.zip",
    "sha256": "90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159",
    "size": 12619664,
    "license": "Python Software Foundation License Version 2 (PSF-2.0); runtime/python/LICENSE.txt holds the "
               "full text, including the licenses of the third-party libraries it ships",
    "verification": "SHA-256 matches the python.org release. The Sigstore bundle signature was checked with OpenSSL "
                    "against its Fulcio certificate (identity hugo@python.org, issuer https://github.com/login/oauth). "
                    "The full Sigstore certificate chain and transparency-log inclusion were not verified.",
}

# (source glob under the prototype, file name in NOTICES/)
NOTICES = [
    ("Library/PackageCache/com.arloopa.unitysplats@*/LICENSE.md", "UnitySplats-LICENSE.md"),
    ("Library/PackageCache/com.arloopa.unitysplats@*/Third Party Notices.md", "UnitySplats-Third-Party-Notices.md"),
    ("Library/PackageCache/com.netpyoung.webp@*/LICENSE.md", "netpyoung-webp-LICENSE.md"),
    ("Library/PackageCache/com.netpyoung.webp@*/THIRD PARTY NOTICES.md", "netpyoung-webp-Third-Party-Notices.md"),
]

BUILD_FILES = ["index.html", "Build/WebGL.data", "Build/WebGL.framework.js", "Build/WebGL.loader.js",
               "Build/WebGL.wasm"]
WINDOWS_FILES = ["START-HERE.txt", "RUN-EDGE.cmd", "RUN-CHROME.cmd", "OPTIONAL-500K-EDGE.cmd",
                 "OPTIONAL-500K-CHROME.cmd", "MANUAL-SERVER.cmd", "COLLECT-RESULTS.cmd",
                 "tools/launch.cmd", "tools/find_python.cmd"]

NOTICES_README = """Third-party notices for the VR-HE browser test
===============================================

app\\  Unity WebGL build made with Unity {unity} (Unity's own terms). It includes:
  - UnitySplats 2.0.0 (com.arloopa.unitysplats, Git revision {splats_rev}), MIT License:
    UnitySplats-LICENSE.md and UnitySplats-Third-Party-Notices.md
  - com.netpyoung.webp {webp_version}, MIT License; libwebp is BSD-3-Clause:
    netpyoung-webp-LICENSE.md and netpyoung-webp-Third-Party-Notices.md

runtime\\python\\  Python {python}, Python Software Foundation License: runtime\\python\\LICENSE.txt

fixtures\\, tools\\ and the launchers are VR-HE project files: synthetic test data and scripts.
"""

RUNTIME_README = """Portable Python for the VR-HE browser test
==========================================

What:      Python {version}, {package}.
Why:       The local test server is a Python script. If this computer already has Python 3.8 or
           newer, that is used instead; this copy is only the fallback. Nothing is installed.
           It runs from this folder and writes only to the test folder and the temporary folder.
Source:    {url}
Download:  {size:,} bytes, SHA-256 {sha256}
Extracted: {files} files, {extracted:,} bytes (about {extracted_mib:.1f} MiB), in runtime\\python
License:   {license}.
Checked:   {verification}
"""

RESULTS_README = """VR-HE browser test results
==========================

Each test run saves its results in a sub-folder here. COLLECT-RESULTS.cmd packs all of them into
one VRHE-results-<date>-<time>.zip file next to START-HERE.txt for copying to the USB drive.
"""


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", PROTO] + list(args), capture_output=True, text=True, check=False).stdout.strip()


def load_harness():
    spec = importlib.util.spec_from_file_location("vrhe_harness", os.path.join(TOOLS, "browser_test_harness.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def home_folders():
    """The developer's home folder, as written and with symbolic links resolved."""
    found = []
    for path in (os.path.expanduser("~"), os.path.realpath(os.path.expanduser("~"))):
        path = path.rstrip("/")
        parent, name = os.path.split(path)
        if name and len(name) >= 2 and path not in [p for p, _ in found]:
            found.append((path, os.path.join(parent, "x" * len(name))))
    return found


def anonymize_paths(data):
    """Replace the home-folder name inside absolute paths with x characters of equal length."""
    total = 0
    for real, masked in home_folders():
        needle, replacement = (real + "/").encode(), (masked + "/").encode()
        assert len(needle) == len(replacement)
        total += data.count(needle)
        data = data.replace(needle, replacement)
    return data, total


def private_markers():
    """(description, compiled bytes pattern) for identifiers that must not be in the bundle."""
    markers = []
    for real, _ in home_folders():
        markers.append(("developer home path", re.compile(re.escape(real.encode()))))
    account = getpass.getuser()
    if account and len(account) >= 3:
        # A whole word only: the account name can be part of ordinary words in compiled code.
        markers.append(("developer account name",
                        re.compile(rb"(?i)(?<![A-Za-z0-9])" + re.escape(account.encode()) + rb"(?![A-Za-z0-9])")))
    for key, label in (("user.email", "global Git e-mail"), ("user.name", "global Git name")):
        value = subprocess.run(["git", "config", "--global", "--get", key], capture_output=True, text=True,
                               check=False).stdout.strip()
        if value and len(value) >= 3:
            markers.append((label, re.compile(rb"(?i)" + re.escape(value.encode()))))
    # Further terms (for example a personal e-mail address) can be given at run time, never in source.
    for value in os.environ.get("VRHE_PRIVACY_TERMS", "").split(","):
        value = value.strip()
        if len(value) >= 3:
            markers.append(("extra privacy term", re.compile(rb"(?i)" + re.escape(value.encode()))))
    return markers


def to_crlf_ascii(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as error:
        raise SystemExit(f"{path} must be ASCII only (cmd.exe and Notepad defaults): {error}")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text.replace("\n", "\r\n").encode("ascii")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--allow-dirty", action="store_true", help="package although the prototype has uncommitted changes")
    parser.add_argument("--keep-staging", action="store_true", help="keep Bundles/staging after zipping")
    args = parser.parse_args()

    # ---- source state
    commit = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain", "--", ".")
    if not commit:
        raise SystemExit("not a Git checkout")
    if dirty and not args.allow_dirty:
        raise SystemExit("the prototype has uncommitted changes; commit them first or pass --allow-dirty:\n" + dirty)
    commit_time = int(git("log", "-1", "--format=%ct") or "0")
    harness = load_harness()

    # ---- inputs
    build = os.path.join(PROTO, "Builds", "WebGL")
    for relative in BUILD_FILES:
        if not os.path.isfile(os.path.join(build, *relative.split("/"))):
            raise SystemExit(f"missing build file Builds/WebGL/{relative}; this script does not rebuild")
    python_zip = os.path.join(BUNDLES, "cache", PYTHON["file"])
    if not os.path.isfile(python_zip):
        raise SystemExit(f"missing {python_zip}; download it from {PYTHON['url']}")
    if os.path.getsize(python_zip) != PYTHON["size"] or sha256_file(python_zip) != PYTHON["sha256"]:
        raise SystemExit(f"{python_zip} does not match the pinned size and SHA-256")
    notices = []
    for pattern, name in NOTICES:
        matches = glob.glob(os.path.join(PROTO, pattern))
        if len(matches) != 1:
            raise SystemExit(f"expected exactly one match for {pattern}, found {len(matches)}")
        notices.append((matches[0], name))
    lock = json.load(open(os.path.join(PROTO, "Packages", "packages-lock.json"), encoding="utf-8"))["dependencies"]
    splats_rev = lock["com.arloopa.unitysplats"].get("hash", "")
    webp_version = lock["com.netpyoung.webp"].get("version", "")
    if not os.path.basename(os.path.dirname(notices[0][0])).endswith("@" + splats_rev[:12]):
        raise SystemExit("the UnitySplats package cache does not match the pinned revision " + splats_rev)

    # ---- staging
    staging_parent = os.path.join(BUNDLES, "staging")
    root = os.path.join(staging_parent, BUNDLE_NAME)
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)

    # app/: the existing build, with home-folder names masked in compiled-in paths
    build_info = {}
    for relative in BUILD_FILES:
        with open(os.path.join(build, *relative.split("/")), "rb") as f:
            original = f.read()
        data, masked = anonymize_paths(original)
        if len(data) != len(original):
            raise SystemExit("path masking changed a file size")
        write(os.path.join(root, "app", *relative.split("/")), data)
        build_info[relative] = {"size": len(data), "sha256": sha256_bytes(data)}
        if masked:
            build_info[relative].update({"development_build_sha256": sha256_bytes(original),
                                         "masked_home_folder_paths": masked})
        print(f"app/{relative}: {len(data):,} bytes" + (f", {masked} compiled-in paths masked" if masked else ""))

    # fixtures/: regenerate and confirm they equal the fixtures used for the November 10 runs
    fixtures = os.path.join(root, "fixtures")
    subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "generate_synthetic_splats.py"), "--out", fixtures,
                    "--counts", FIXTURE_COUNTS, "--overlap"], check=True, stdout=subprocess.DEVNULL)
    manifest = json.load(open(os.path.join(fixtures, "manifest.json"), encoding="utf-8"))
    identical = {}
    for entry in manifest["files"]:
        previous = os.path.join(PROTO, "Fixtures", "Generated", entry["name"])
        if os.path.isfile(previous):
            identical[entry["name"]] = sha256_file(previous) == sha256_file(os.path.join(fixtures, entry["name"]))
            if not identical[entry["name"]]:
                raise SystemExit(f"regenerated {entry['name']} differs from Fixtures/Generated: the fixture "
                                 "definition changed, so results would not be comparable")
    print(f"fixtures/: {len(manifest['files'])} files regenerated (seed {manifest['seed']}); "
          f"{sum(identical.values())} byte-identical to Fixtures/Generated")

    # tools/, launchers and instructions
    os.makedirs(os.path.join(root, "tools"), exist_ok=True)
    shutil.copyfile(os.path.join(TOOLS, "browser_test_harness.py"), os.path.join(root, "tools", "browser_test_harness.py"))
    for relative in WINDOWS_FILES:
        write(os.path.join(root, *relative.split("/")), to_crlf_ascii(os.path.join(TOOLS, "windows-bundle", *relative.split("/"))))

    # runtime/python: the unmodified embeddable package
    runtime = os.path.join(root, "runtime", "python")
    os.makedirs(runtime)
    extracted, count = 0, 0
    with zipfile.ZipFile(python_zip) as archive:
        for info in archive.infolist():
            name = info.filename
            if name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/") or ":" in name:
                raise SystemExit(f"unsafe name in {PYTHON['file']}: {name}")
            if info.is_dir():
                continue
            write(os.path.join(runtime, *name.split("/")), archive.read(info))
            extracted += info.file_size
            count += 1
    python_info = dict(PYTHON, extracted_files=count, extracted_bytes=extracted)
    readme_fields = dict(PYTHON)
    for key in ("license", "verification"):  # wrap long fields for Notepad
        readme_fields[key] = textwrap.fill(PYTHON[key].replace("runtime/python/", "runtime\\python\\"), width=96,
                                           subsequent_indent=" " * 11)
    write(os.path.join(root, "runtime", "README.txt"), RUNTIME_README.format(
        files=count, extracted=extracted, extracted_mib=extracted / 2 ** 20, **readme_fields)
        .replace("\n", "\r\n").encode("ascii"))

    # NOTICES/ and results/
    os.makedirs(os.path.join(root, "NOTICES"), exist_ok=True)
    for source, name in notices:
        shutil.copyfile(source, os.path.join(root, "NOTICES", name))
    write(os.path.join(root, "NOTICES", "README.txt"), NOTICES_README.format(
        unity=UNITY_VERSION, splats_rev=splats_rev, webp_version=webp_version,
        python=PYTHON["version"]).replace("\n", "\r\n").encode("ascii"))
    write(os.path.join(root, "results", "README.txt"), RESULTS_README.replace("\n", "\r\n").encode("ascii"))

    # ---- bundle.json: what the bundle is and checksums of everything the test depends on
    verify = {}
    for folder, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(folder, name)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            if relative.startswith("results/") or name.lower().endswith((".txt", ".md")):
                continue  # instructions and notices may be opened and saved; they do not affect the test
            verify[relative] = {"size": os.path.getsize(full), "sha256": sha256_file(full)}
    created = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    bundle = {
        "bundle_name": BUNDLE_NAME,
        "bundle_version": BUNDLE_VERSION,
        "created": created.isoformat(),
        "source_commit": commit,
        "source_dirty": bool(dirty),
        "status": "Windows execution of this bundle is untested until a recorded run on the reference PC.",
        "target": {"pc": "Panasonic Toughbook FZ-55 browser reference PC (D033)",
                   "browsers": ["Microsoft Edge", "Google Chrome"], "browser_floor_fps": 30,
                   "floor_note": "30 application-rendered fps is the user floor (D034); detailed acceptance "
                                 "criteria are still open"},
        "plans": harness.PLANS,
        "build": {"unity_version": UNITY_VERSION, "target": "WebGL 2 (OpenGLES3)",
                  "renderer": f"UnitySplats {splats_rev[:12]} (CPU sort on the main thread)",
                  "page": "fixed 1280x720 canvas, devicePixelRatio 1 (VRHEBenchmark template)",
                  "rebuilt_for_bundle": False, "files": build_info,
                  "path_masking": "Compiled-in IL2CPP source paths inside the developer's home folder have the "
                                  "folder name replaced by x characters of equal length (data bytes only)."},
        "fixtures": {"generator": manifest.get("generator"), "generator_version": manifest.get("generator_version"),
                     "seed": manifest.get("seed"), "synthetic": manifest.get("synthetic"),
                     "counts": [int(c) for c in FIXTURE_COUNTS.split(",")], "overlap": True,
                     "files": manifest["files"], "identical_to_development_fixtures": identical},
        "harness": {"file": "tools/browser_test_harness.py", "harness_version": harness.HARNESS_VERSION,
                    "sha256": verify["tools/browser_test_harness.py"]["sha256"]},
        "python_runtime": python_info,
        "verify": verify,
    }
    write(os.path.join(root, "bundle.json"), (json.dumps(bundle, indent=2) + "\n").encode("utf-8"))

    # ---- privacy scan of every staged file
    markers = private_markers()
    problems = []
    for folder, _, files in os.walk(root):
        for name in files:
            full = os.path.join(folder, name)
            with open(full, "rb") as f:
                data = f.read()
            for label, pattern in markers:
                hits = len(pattern.findall(data))
                if hits:
                    problems.append(f"{os.path.relpath(full, root)}: {hits} x {label}")
    if problems:
        raise SystemExit("private identifiers found in the bundle:\n  " + "\n  ".join(problems))
    print(f"privacy scan: no {', '.join(sorted({label for label, _ in markers}))} in any bundled file")

    # ---- ZIP with one top-level folder; members in a fixed order with the commit's timestamp
    stamp = datetime.datetime.now().strftime("%Y%m%d")  # local date, as the tester sees it
    zip_path = os.path.join(BUNDLES, f"{BUNDLE_NAME}-{stamp}-{commit[:7]}.zip")
    temporary = zip_path + ".partial"
    when = datetime.datetime.fromtimestamp(commit_time or created.timestamp(), datetime.timezone.utc)
    date_time = (max(when.year, 1980), when.month, when.day, when.hour, when.minute, when.second)
    members = []
    for folder, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            members.append(os.path.join(folder, name))
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for full in members:
            info = zipfile.ZipInfo(BUNDLE_NAME + "/" + os.path.relpath(full, root).replace(os.sep, "/"), date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(full, "rb") as f:
                archive.writestr(info, f.read(), compresslevel=9)
    os.replace(temporary, zip_path)

    # ---- check the ZIP against the staged files
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"ZIP self-test failed at {bad}")
        names = archive.namelist()
        if len(names) != len(members) or any(not n.startswith(BUNDLE_NAME + "/") for n in names):
            raise SystemExit("ZIP member list is wrong")
        for relative, meta in verify.items():
            if sha256_bytes(archive.read(BUNDLE_NAME + "/" + relative)) != meta["sha256"]:
                raise SystemExit(f"ZIP member {relative} differs from the staged file")
        converted = set(WINDOWS_FILES) | {"runtime/README.txt", "NOTICES/README.txt", "results/README.txt"}
        for name in names:
            if name[len(BUNDLE_NAME) + 1:] in converted:
                data = archive.read(name)
                if data.replace(b"\r\n", b"").count(b"\n") or data.replace(b"\r\n", b"").count(b"\r"):
                    raise SystemExit(f"{name} does not use CRLF line endings throughout")
    digest = sha256_file(zip_path)
    size = os.path.getsize(zip_path)
    with open(zip_path + ".sha256", "w", encoding="ascii", newline="\n") as f:
        f.write(f"{digest}  {os.path.basename(zip_path)}\n")
    unpacked = sum(os.path.getsize(m) for m in members)
    if not args.keep_staging:
        shutil.rmtree(staging_parent)
    print(f"\nZIP:      {zip_path}")
    print(f"size:     {size:,} bytes ({size / 2 ** 20:.1f} MiB); {len(members)} files, {unpacked:,} bytes unpacked")
    print(f"SHA-256:  {digest}")
    print(f"commit:   {commit}" + (" (with uncommitted changes)" if dirty else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
