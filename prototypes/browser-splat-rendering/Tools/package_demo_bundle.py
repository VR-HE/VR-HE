#!/usr/bin/env python3
"""Build the Windows bundle (one ZIP) for the VR-HE interactive browser demo (prototype).

The ZIP holds the demo's Unity WebGL build, the regenerated synthetic 250k-splat room, the local
demo server, Windows launchers, plain-language instructions (START-HERE-DEMO.txt) and a portable
Python fallback. It holds no operational data, credentials or personal identifiers. It is meant
for a personal Windows PC; company Toughbook execution is deferred (D035).

Inputs, all on the development laptop:
  Builds/InteractiveDemo/               the demo build (Tools/interactive_demo_unity.sh build);
                                        this script never rebuilds it and never touches Builds/WebGL
  Tools/generate_synthetic_splats.py    regenerates fixtures/scene_250000.ply
  Tools/demo_server.py, Tools/browser_test_harness.py
  Tools/windows-demo-bundle/            launchers and START-HERE-DEMO.txt (LF in Git, CRLF in the ZIP)
  Tools/windows-bundle/tools/find_python.cmd   the benchmark bundle's Python finder, shared
  Bundles/cache/<Python embeddable ZIP> portable Python, checked against the pin in
                                        Tools/package_toughbook_bundle.py
  Library/PackageCache/                 license notices of the packages compiled into the build

Checks before anything is written:
  - the build was made from a clean commit, and nothing under Assets/, Packages/ or
    ProjectSettings/ has changed since that commit (so the bundle matches committed source);
  - the build holds exactly the expected files, its TemplateData equals the committed template
    and its data/site.json equals Assets/InteractiveDemo/Data/demo-site.json;
  - the regenerated room is byte-identical to Fixtures/Generated/scene_250000.ply when present.
Path masking, the privacy scan, the CRLF/ASCII rule and the ZIP self-test work as in
Tools/package_toughbook_bundle.py, whose helpers are reused rather than copied.

Output (ignored by Git):
  Bundles/VRHE-Interactive-Demo-<yyyymmdd>-<commit>.zip and the same name + .sha256

Usage (from any folder):
  python3 -I Tools/package_demo_bundle.py [--allow-dirty] [--keep-staging]
Extra privacy terms (for example an e-mail address) can be given at run time in the
VRHE_PRIVACY_TERMS environment variable (comma separated); they are never written to source.
"""

import argparse
import datetime
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import zipfile

sys.dont_write_bytecode = True  # loading sibling tools by path must not leave __pycache__ behind

TOOLS = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(TOOLS)
BUNDLES = os.path.join(PROTO, "Bundles")
BUNDLE_NAME = "VRHE-Interactive-Demo"
BUNDLE_VERSION = "1"
FIXTURE = "scene_250000.ply"
FIXTURE_COUNT = "250000"
BUILD_RELEVANT = ["Assets", "Packages", "ProjectSettings"]
LABEL = re.compile(r"^interactive-demo-(?P<commit>[0-9a-f]{12}|unknown)(?P<dirty>-dirty)?-(?P<stamp>\d{8}T\d{6}Z)$")

# Every file the demo build must contain (Builds/InteractiveDemo); anything else is refused.
BUILD_FILES = ["index.html", "Build/InteractiveDemo.data", "Build/InteractiveDemo.framework.js",
               "Build/InteractiveDemo.loader.js", "Build/InteractiveDemo.wasm",
               "TemplateData/demo-ui.css", "TemplateData/demo-ui.js",
               "data/site.json", "data/build-info.json"]
# Build files that must equal a committed source file byte for byte.
BUILD_SOURCES = {"TemplateData/demo-ui.css": "Assets/WebGLTemplates/VRHEInteractiveDemo/TemplateData/demo-ui.css",
                 "TemplateData/demo-ui.js": "Assets/WebGLTemplates/VRHEInteractiveDemo/TemplateData/demo-ui.js",
                 "data/site.json": "Assets/InteractiveDemo/Data/demo-site.json"}
# (source under Tools/, path in the bundle); converted to CRLF and checked to be ASCII.
WINDOWS_FILES = [("windows-demo-bundle/START-HERE-DEMO.txt", "START-HERE-DEMO.txt"),
                 ("windows-demo-bundle/RUN-DEMO-EDGE.cmd", "RUN-DEMO-EDGE.cmd"),
                 ("windows-demo-bundle/RUN-DEMO-CHROME.cmd", "RUN-DEMO-CHROME.cmd"),
                 ("windows-demo-bundle/DEMO-SERVER-ONLY.cmd", "DEMO-SERVER-ONLY.cmd"),
                 ("windows-demo-bundle/COLLECT-DEMO-RESULTS.cmd", "COLLECT-DEMO-RESULTS.cmd"),
                 ("windows-demo-bundle/tools/launch.cmd", "tools/launch.cmd"),
                 ("windows-bundle/tools/find_python.cmd", "tools/find_python.cmd")]
SCRIPTS = ["demo_server.py", "browser_test_harness.py"]

NOTICES_README = """Third-party notices for the VR-HE interactive browser demo
==========================================================

app\\  Unity WebGL build made with Unity {unity} (Unity's own terms). It includes:
  - UnitySplats 2.0.0 (com.arloopa.unitysplats, Git revision {splats_rev}), MIT License:
    UnitySplats-LICENSE.md and UnitySplats-Third-Party-Notices.md
  - com.netpyoung.webp {webp_version}, MIT License; libwebp is BSD-3-Clause:
    netpyoung-webp-LICENSE.md and netpyoung-webp-Third-Party-Notices.md

runtime\\python\\  Python {python}, Python Software Foundation License: runtime\\python\\LICENSE.txt

fixtures\\, tools\\, the launchers and the demo page are VR-HE project files: a synthetic room,
synthetic records and scripts.
"""

RUNTIME_README = """Portable Python for the VR-HE interactive demo
==============================================

What:      Python {version}, {package}.
Why:       The local demo server is a Python script. If this computer already has Python 3.8 or
           newer, that is used instead; this copy is only the fallback. Nothing is installed.
           It runs from this folder and writes only to this demo folder.
Source:    {url}
Download:  {size:,} bytes, SHA-256 {sha256}
Extracted: {files} files, {extracted:,} bytes (about {extracted_mib:.1f} MiB), in runtime\\python
License:   {license}.
Checked:   {verification}
"""

RESULTS_README = """VR-HE interactive demo results
==============================

Each time the demo runs, the local demo server saves a record here, with one sub-folder per
page session: timings, console messages and copies of JSON exports. Saved record text is kept
in the demo browser profile, not here, unless you export it. COLLECT-DEMO-RESULTS.cmd packs
this folder into one VRHE-demo-results-<date>-<time>.zip file next to START-HERE-DEMO.txt.
"""


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TB = load("vrhe_toughbook_packager", "package_toughbook_bundle.py")  # shared helpers and the Python pin
git = TB.git


def check_build(build, allow_dirty):
    """The build's description, after refusing a build that does not match committed source."""
    present = sorted(os.path.relpath(os.path.join(folder, name), build).replace(os.sep, "/")
                     for folder, _, files in os.walk(build) for name in files)
    if present != sorted(BUILD_FILES):
        raise SystemExit("Builds/InteractiveDemo does not hold exactly the expected files.\n"
                         f"  missing: {sorted(set(BUILD_FILES) - set(present))}\n"
                         f"  unexpected: {sorted(set(present) - set(BUILD_FILES))}\n"
                         "Rebuild with Tools/interactive_demo_unity.sh build.")
    for relative, source in BUILD_SOURCES.items():
        if TB.sha256_file(os.path.join(build, relative)) != TB.sha256_file(os.path.join(PROTO, source)):
            raise SystemExit(f"Builds/InteractiveDemo/{relative} differs from {source}; rebuild the demo.")
    info = json.load(open(os.path.join(build, "data", "build-info.json"), encoding="utf-8"))
    match = LABEL.match(info.get("label", ""))
    if not match or match.group("commit") == "unknown":
        raise SystemExit(f"unrecognised build label {info.get('label')!r}; rebuild the demo")
    built_from = git("rev-parse", "--verify", "--quiet", match.group("commit") + "^{commit}")
    if not built_from:
        raise SystemExit(f"the build's commit {match.group('commit')} is not in this repository")
    changed = git("diff", "--name-only", built_from, "HEAD", "--", *BUILD_RELEVANT)
    if match.group("dirty") and not allow_dirty:
        raise SystemExit("the build was made from uncommitted source (label ends in -dirty). Commit, then rebuild.")
    if changed and not allow_dirty:
        raise SystemExit(f"build-relevant files changed since the build's commit {built_from[:12]}:\n  "
                         + changed.replace("\n", "\n  ") + "\nRebuild the demo.")
    return info, built_from, bool(match.group("dirty")), changed.splitlines() if changed else []


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--allow-dirty", action="store_true",
                        help="package although source or build do not match a clean commit (for trials only)")
    parser.add_argument("--keep-staging", action="store_true", help="keep Bundles/staging-demo after zipping")
    args = parser.parse_args()

    # ---- source state
    commit = git("rev-parse", "HEAD")
    if not commit:
        raise SystemExit("not a Git checkout")
    dirty = git("status", "--porcelain", "--", ".")
    if dirty and not args.allow_dirty:
        raise SystemExit("the prototype has uncommitted changes; commit them first or pass --allow-dirty:\n" + dirty)
    commit_time = int(git("log", "-1", "--format=%ct") or "0")
    server = load("vrhe_demo_server", "demo_server.py")

    # ---- inputs
    build = os.path.join(PROTO, "Builds", "InteractiveDemo")
    if not os.path.isfile(os.path.join(build, "index.html")):
        raise SystemExit("missing Builds/InteractiveDemo; build it with Tools/interactive_demo_unity.sh build")
    build_info_file, built_from, build_dirty, build_changes = check_build(build, args.allow_dirty)
    python_zip = os.path.join(BUNDLES, "cache", TB.PYTHON["file"])
    if not os.path.isfile(python_zip):
        raise SystemExit(f"missing {python_zip}; download it from {TB.PYTHON['url']}")
    if os.path.getsize(python_zip) != TB.PYTHON["size"] or TB.sha256_file(python_zip) != TB.PYTHON["sha256"]:
        raise SystemExit(f"{python_zip} does not match the pinned size and SHA-256")
    notices = []
    for pattern, name in TB.NOTICES:
        matches = glob.glob(os.path.join(PROTO, pattern))
        if len(matches) != 1:
            raise SystemExit(f"expected exactly one match for {pattern}, found {len(matches)}")
        notices.append((matches[0], name))
    lock = json.load(open(os.path.join(PROTO, "Packages", "packages-lock.json"), encoding="utf-8"))["dependencies"]
    splats_rev = lock["com.arloopa.unitysplats"].get("hash", "")
    webp_version = lock["com.netpyoung.webp"].get("version", "")
    if not os.path.basename(os.path.dirname(notices[0][0])).endswith("@" + splats_rev[:12]):
        raise SystemExit("the UnitySplats package cache does not match the pinned revision " + splats_rev)
    site = json.load(open(os.path.join(PROTO, "Assets", "InteractiveDemo", "Data", "demo-site.json"), encoding="utf-8"))
    if site["splat"]["file"] != FIXTURE:
        raise SystemExit(f"demo-site.json asks for {site['splat']['file']}, this script packages {FIXTURE}")

    # ---- staging
    staging_parent = os.path.join(BUNDLES, "staging-demo")
    root = os.path.join(staging_parent, BUNDLE_NAME)
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)

    # app/: the demo build, with home-folder names masked in compiled-in paths
    build_files = {}
    for relative in BUILD_FILES:
        with open(os.path.join(build, *relative.split("/")), "rb") as f:
            original = f.read()
        data, masked = TB.anonymize_paths(original)
        if len(data) != len(original):
            raise SystemExit("path masking changed a file size")
        TB.write(os.path.join(root, "app", *relative.split("/")), data)
        build_files[relative] = {"size": len(data), "sha256": TB.sha256_bytes(data)}
        if masked:
            build_files[relative].update({"development_build_sha256": TB.sha256_bytes(original),
                                          "masked_home_folder_paths": masked})
        print(f"app/{relative}: {len(data):,} bytes" + (f", {masked} compiled-in paths masked" if masked else ""))

    # fixtures/: regenerate the room and confirm it equals the one used for the Linux checks
    generated = os.path.join(staging_parent, "fixtures-generated")
    if os.path.exists(generated):
        shutil.rmtree(generated)
    subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "generate_synthetic_splats.py"), "--out", generated,
                    "--counts", FIXTURE_COUNT], check=True, stdout=subprocess.DEVNULL)
    manifest = json.load(open(os.path.join(generated, "manifest.json"), encoding="utf-8"))
    entry = [e for e in manifest["files"] if e["name"] == FIXTURE]
    if len(entry) != 1:
        raise SystemExit(f"the generator did not write {FIXTURE}")
    fixture_sha = TB.sha256_file(os.path.join(generated, FIXTURE))
    previous = os.path.join(PROTO, "Fixtures", "Generated", FIXTURE)
    identical = None
    if os.path.isfile(previous):
        identical = TB.sha256_file(previous) == fixture_sha
        if not identical:
            raise SystemExit(f"regenerated {FIXTURE} differs from Fixtures/Generated: the room definition changed")
    os.makedirs(os.path.join(root, "fixtures"))
    shutil.copyfile(os.path.join(generated, FIXTURE), os.path.join(root, "fixtures", FIXTURE))
    shutil.rmtree(generated)
    print(f"fixtures/{FIXTURE}: regenerated (seed {manifest['seed']})"
          + ("; byte-identical to Fixtures/Generated" if identical else "; no development copy to compare"))

    # tools/, launchers and instructions
    os.makedirs(os.path.join(root, "tools"), exist_ok=True)
    for name in SCRIPTS:
        shutil.copyfile(os.path.join(TOOLS, name), os.path.join(root, "tools", name))
    for source, target in WINDOWS_FILES:
        TB.write(os.path.join(root, *target.split("/")), TB.to_crlf_ascii(os.path.join(TOOLS, *source.split("/"))))

    # runtime/python: the unmodified embeddable package
    runtime = os.path.join(root, "runtime", "python")
    os.makedirs(runtime)
    extracted, count = 0, 0
    with zipfile.ZipFile(python_zip) as archive:
        for info in archive.infolist():
            name = info.filename
            if name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/") or ":" in name:
                raise SystemExit(f"unsafe name in {TB.PYTHON['file']}: {name}")
            if info.is_dir():
                continue
            TB.write(os.path.join(runtime, *name.split("/")), archive.read(info))
            extracted += info.file_size
            count += 1
    python_info = dict(TB.PYTHON, extracted_files=count, extracted_bytes=extracted)
    readme_fields = dict(TB.PYTHON)
    for key in ("license", "verification"):  # wrap long fields for Notepad
        readme_fields[key] = textwrap.fill(TB.PYTHON[key].replace("runtime/python/", "runtime\\python\\"), width=96,
                                           subsequent_indent=" " * 11)
    TB.write(os.path.join(root, "runtime", "README.txt"), RUNTIME_README.format(
        files=count, extracted=extracted, extracted_mib=extracted / 2 ** 20, **readme_fields)
        .replace("\n", "\r\n").encode("ascii"))

    # NOTICES/ and results/
    os.makedirs(os.path.join(root, "NOTICES"), exist_ok=True)
    for source, name in notices:
        shutil.copyfile(source, os.path.join(root, "NOTICES", name))
    TB.write(os.path.join(root, "NOTICES", "README.txt"), NOTICES_README.format(
        unity=TB.UNITY_VERSION, splats_rev=splats_rev, webp_version=webp_version,
        python=TB.PYTHON["version"]).replace("\n", "\r\n").encode("ascii"))
    TB.write(os.path.join(root, "results", "README.txt"), RESULTS_README.replace("\n", "\r\n").encode("ascii"))

    # ---- bundle.json: what the bundle is, its status, and checksums of everything the demo runs
    verify = {}
    for folder, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(folder, name)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            if relative.startswith("results/") or name.lower().endswith((".txt", ".md")):
                continue  # instructions and notices may be opened and saved; they do not affect the demo
            verify[relative] = {"size": os.path.getsize(full), "sha256": TB.sha256_file(full)}
    created = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    bundle = {
        "app": server.APP_ID,
        "bundle_name": BUNDLE_NAME,
        "bundle_version": BUNDLE_VERSION,
        "created": created.isoformat(),
        "source_commit": commit,
        "source_dirty": bool(dirty),
        "status": ("PROTOTYPE. Behaviour was checked in Chrome on the Linux development laptop "
                   "(Tools/verify_interactive_demo.py). Running this bundle on Windows, including its controls, "
                   "saving, relaunch and export, is untested until a recorded run on the Windows PC; the earlier "
                   "benchmark runs do not validate it."),
        "data_notice": "LOCAL DEMO DATA: a synthetic room and synthetic records, saved only in the demo browser "
                       "profile on the computer that runs it. No backend, spreadsheet or company system.",
        "target": {"pc": "personal Windows 10 or 11 PC; company Toughbook execution is deferred (D035)",
                   "browsers": ["Microsoft Edge", "Google Chrome"],
                   "address": f"http://127.0.0.1:{server.DEMO_PORT}/ (this computer only)",
                   "profiles": "%LOCALAPPDATA%\\VRHE-Interactive-Demo\\browser-profiles\\<browser>, kept between runs",
                   "browser_floor_fps": 30,
                   "floor_note": "30 application-rendered fps is the user floor (D034), not a cap and not a pass "
                                 "criterion; detailed acceptance criteria are still open"},
        "build": {"label": build_info_file.get("label"), "built_from_commit": built_from,
                  "built_from_uncommitted_source": build_dirty,
                  "build_relevant_changes_since": build_changes,
                  "unity_version": build_info_file.get("unityVersion"), "target": "WebGL 2 (OpenGLES3)",
                  "renderer": f"UnitySplats {splats_rev[:12]} (CPU sort on the main thread)",
                  "page": "1280x720 canvas when the window allows, otherwise reduced to fit and labelled; "
                          "devicePixelRatio 1 (VRHEInteractiveDemo template)",
                  "files": build_files,
                  "path_masking": "Compiled-in IL2CPP source paths inside the developer's home folder have the "
                                  "folder name replaced by x characters of equal length (data bytes only)."},
        "fixture": {"file": FIXTURE, "splats": int(FIXTURE_COUNT), "generator": manifest.get("generator"),
                    "generator_version": manifest.get("generator_version"), "seed": manifest.get("seed"),
                    "synthetic": manifest.get("synthetic"), "sha256": fixture_sha,
                    "identical_to_development_fixture": identical},
        "server": {"file": "tools/demo_server.py", "server_version": server.SERVER_VERSION,
                   "harness_version": server.H.HARNESS_VERSION, "port": server.DEMO_PORT},
        "python_runtime": python_info,
        "verify": verify,
    }
    TB.write(os.path.join(root, "bundle.json"), (json.dumps(bundle, indent=2) + "\n").encode("utf-8"))

    # ---- privacy scan of every staged file
    markers = TB.private_markers()
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

    # ---- ZIP with one top-level folder; members in a fixed order, stamped with the commit time
    # in local time (ZIP times have no zone and Windows shows them as local time)
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    zip_path = os.path.join(BUNDLES, f"{BUNDLE_NAME}-{stamp}-{commit[:7]}.zip")
    temporary = zip_path + ".partial"
    when = datetime.datetime.fromtimestamp(commit_time or created.timestamp())
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
            if TB.sha256_bytes(archive.read(BUNDLE_NAME + "/" + relative)) != meta["sha256"]:
                raise SystemExit(f"ZIP member {relative} differs from the staged file")
        converted = {target for _, target in WINDOWS_FILES} | {"runtime/README.txt", "NOTICES/README.txt",
                                                              "results/README.txt"}
        for name in names:
            if name[len(BUNDLE_NAME) + 1:] in converted:
                data = archive.read(name)
                if data.replace(b"\r\n", b"").count(b"\n") or data.replace(b"\r\n", b"").count(b"\r"):
                    raise SystemExit(f"{name} does not use CRLF line endings throughout")
    digest = TB.sha256_file(zip_path)
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
    print(f"build:    {build_info_file.get('label')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
