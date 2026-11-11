#!/usr/bin/env python3
"""Condense raw browser-benchmark runs into a tracked summary.

Reads TestResults/raw/<run>/ folders written by browser_test_harness.py and the Unity page,
and writes:
  <out>/browser-splat-results.md    human-readable tables
  <out>/browser-splat-results.json  condensed machine-readable results
  <out>/screenshots/<run>/*.jpg     selected half-size screenshots (optional)

Raw per-frame series, full-size PNGs, console logs and server logs stay in the ignored raw
folder. Absolute paths and host names are not copied into the summary.

Usage:
  python3 -I Tools/summarize_results.py --raw TestResults/raw --out TestResults \
      --runs 20261110-chrome-1,20261110-firefox-1 [--copy-screenshots [--screenshot-runs RUNS]]
"""

import argparse
import json
import os
import shutil

SCREENSHOT_CASES = (
    "overlap_merged_single_renderer",
    "overlap_separate_renderers",
    "overlap_separate_A_forced_last",
    "overlap_merged_active_ranges__only_A",
    "overlap_merged_active_ranges__only_B",
    "scale_25000",
    "scale_1000000",
    "scale_2000000",
)


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def console_summary(run_dir):
    path = os.path.join(run_dir, "console.jsonl")
    counts, errors, warnings = {}, [], []
    if not os.path.exists(path):
        return {"lines": 0}
    lines = 0
    with open(path, encoding="utf-8") as f:
        for raw in f:
            lines += 1
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            level = entry.get("level", "?")
            counts[level] = counts.get(level, 0) + 1
            text = str(entry.get("text", "")).strip().splitlines()[0][:300] if entry.get("text") else ""
            if level in ("error", "pageerror", "unhandledrejection") and text not in errors:
                errors.append(text)
            elif level == "warn" and text not in warnings:
                warnings.append(text)
    return {"lines": lines, "levels": counts, "unique_errors": errors[:20], "unique_warnings": warnings[:20]}


def condense_run(raw, run):
    run_dir = os.path.join(raw, run)
    harness = load_json(os.path.join(run_dir, "harness.json"), {})
    env = load_json(os.path.join(run_dir, "env.json"), {})
    summary = load_json(os.path.join(run_dir, "summary.json"))
    browser_info = {}
    if env.get("browserInfoJson"):
        try:
            browser_info = json.loads(env["browserInfoJson"])
        except ValueError:
            browser_info = {"unparsed": env["browserInfoJson"][:500]}

    results = summary.get("results", []) if summary else []
    if not results:
        # Partial run: collect any per-case files that were posted before a failure.
        for name in sorted(os.listdir(run_dir)) if os.path.isdir(run_dir) else []:
            if name.endswith(".json") and (name.startswith("overlap_") or name.startswith("scale_")) \
                    and not name.endswith(".frames.json"):
                data = load_json(os.path.join(run_dir, name))
                if data:
                    results.append(data)

    system = harness.get("system", {})
    record = {
        "run": run,
        "browser": harness.get("browser"),
        "browser_version": harness.get("browser_version"),
        "outcome": harness.get("outcome"),
        "harness_flags": harness.get("harness_flags"),
        "started": harness.get("started"),
        "system": {k: system.get(k) for k in ("os", "kernel", "session_type", "desktop", "cpu", "nvidia",
                                              "prime_select", "display_mode")},
        "unity": {k: env.get(k) for k in ("unityVersion", "graphicsDeviceType", "graphicsDeviceName",
                                          "graphicsDeviceVendor", "graphicsDeviceVersion", "qualityLevel",
                                          "renderPipelineAsset", "renderScale", "hdr", "msaa", "colorSpace",
                                          "compression", "screenWidth", "screenHeight", "gsplatCpuFallback",
                                          "gsplatGpuSort", "gsplatVertexTextures", "gsplatBackgroundCpuSort",
                                          "gsplatSettingsValid", "gsplatMaxRenderOrder",
                                          "frameTimerFoundGsplatHook")},
        "browser_webgl": {k: browser_info.get(k) for k in ("userAgent", "isWebGL2", "glVersion", "glslVersion",
                                                           "glRenderer", "unmaskedVendor", "unmaskedRenderer",
                                                           "maxTextureSize", "crossOriginIsolated",
                                                           "devicePixelRatio", "contextSource",
                                                           "webgpuApiPresent")},
        "total_seconds": summary.get("totalSeconds") if summary else None,
        "page_status": summary.get("status") if summary else "no summary (page did not finish)",
        "results": results,
        "console": console_summary(run_dir),
    }
    # Facts recorded by the Windows reference-PC bundle (harness version 2). Older Linux records
    # lack these keys, so their summaries are unchanged.
    for key in ("windows", "logical_processors", "ram_gb", "gpu_adapters", "power"):
        if key in system:
            record["system"][key] = system[key]
    for key in ("platform", "plan", "mode", "python", "bundle", "cleanup", "handed_off"):
        if key in harness:
            record[key] = harness[key]
    client = load_json(os.path.join(run_dir, "client.json"))
    if client:
        record["client"] = {k: client.get(k) for k in ("devicePixelRatio", "screen", "window", "userAgentData",
                                                      "visibilityAtStart")}
        # Manual runs: the browser reports its own exact version through User-Agent Client Hints.
        if str(record["browser_version"] or "").startswith("see client.json"):
            brands = {b.get("brand"): b.get("version")
                      for b in ((client.get("userAgentData") or {}).get("fullVersionList") or []) if isinstance(b, dict)}
            for brand in ("Microsoft Edge", "Google Chrome", "Brave", "Chromium"):
                if brands.get(brand):
                    record["browser_version"] = f"{brand} {brands[brand]} (reported by the browser)"
                    break
    return record


def fmt(value, digits=1):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def stat(result, key, field="mean", digits=2):
    block = result.get(key) or {}
    if not block.get("count"):
        return "-"
    return fmt(block.get(field), digits)


def markdown(condensed):
    out = ["# Browser splat benchmark results", "",
           "Generated by `Tools/summarize_results.py` from raw runs in `TestResults/raw/` (not tracked).",
           "Times are milliseconds. `interval` is frame start to next frame start (browser frame pacing,",
           "capped by the display refresh rate). `sort` is UnitySplats' main-thread CPU sort, order upload and",
           "draw submission; `cpu` is frame start to the end of URP rendering on the main thread. GPU execution",
           "is asynchronous in WebGL and is not measured directly.", ""]

    out += ["## Environments", "",
            "| Run | Browser | Outcome | WebGL renderer | API | Isolated | Canvas | Quality / scale |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in condensed:
        u, b = c["unity"], c["browser_webgl"]
        renderer = b.get("unmaskedRenderer") or b.get("glRenderer") or u.get("graphicsDeviceName")
        out.append(f"| {c['run']} | {c.get('browser_version') or c.get('browser')} | {c.get('outcome')} | "
                   f"{renderer} | {u.get('graphicsDeviceType')} ({b.get('glVersion')}) | "
                   f"{b.get('crossOriginIsolated')} | {u.get('screenWidth')}x{u.get('screenHeight')} | "
                   f"{u.get('qualityLevel')} / {u.get('renderScale')} |")
    out.append("")

    out += ["## Overlapping sections", "",
            "Nearest reference color per screen region. Correct depth order gives a_only red_A, shared_band "
            "red_A and b_only blue_B. Whole-renderer ordering by bounds center predicts shared_band blue_B; "
            "forcing A to draw last predicts b_only backdrop_A. Active-range steps hide one section: only_A "
            "should show backdrop_A in b_only, and only_B should show background in a_only.", "",
            "| Run | Case | Status | a_only | shared_band | b_only | Mean interval | Sort |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in condensed:
        for r in c["results"]:
            if r.get("suite") != "overlap":
                continue
            regions = {g["name"]: g for g in r.get("regions") or []}

            def cell(name):
                g = regions.get(name)
                if not g:
                    return "-"
                return f"{g['nearest']} ({g['r']:.2f},{g['g']:.2f},{g['b']:.2f})"

            out.append(f"| {c['run']} | {r['caseName']} | {r['status']} | {cell('a_only')} | "
                       f"{cell('shared_band')} | {cell('b_only')} | {stat(r, 'intervalMs')} | {stat(r, 'sortMs')} |")
    out.append("")

    out += ["## Splat-count scaling", "",
            "Full runs load fixtures in sequence in one page, so their heap column is a cumulative WebAssembly "
            "high-water mark (the heap never shrinks). The `mem-*` runs load one fixture into a fresh page and "
            "show that fixture's own peak. FPS is capped by the 60 Hz display; CPU time shows headroom below "
            "16.7 ms. Per-frame times have 1 ms resolution in this build, so p95 values are whole milliseconds.", "",
            "| Run | Fixture | Status | FPS | Interval median / p95 | Sort mean / p95 | CPU mean | "
            "Download / decode / upload | Heap after load (MB) |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in condensed:
        for r in c["results"]:
            if r.get("suite") != "scale":
                continue
            out.append(
                f"| {c['run']} | {r['caseName'].replace('scale_', '')} | {r['status']} | "
                f"{fmt(r.get('fpsFromMeanInterval'))} | "
                f"{stat(r, 'intervalMs', 'median')} / {stat(r, 'intervalMs', 'p95')} | "
                f"{stat(r, 'sortMs')} / {stat(r, 'sortMs', 'p95')} | {stat(r, 'cpuMs')} | "
                f"{fmt(r.get('downloadMs'), 0)} / {fmt(r.get('decodeMs'), 0)} / {fmt(r.get('uploadMs'), 0)} | "
                f"{fmt(r.get('wasmHeapMbAfterLoad'), 0)} |" + (f" error: {r['error']}" if r.get("error") else ""))
    out.append("")

    out += ["## Console errors and warnings", ""]
    for c in condensed:
        con = c["console"]
        out.append(f"- {c['run']}: {con.get('lines', 0)} console lines, levels {con.get('levels', {})}.")
        for e in con.get("unique_errors", []):
            out.append(f"  - error: `{e}`")
        for w in con.get("unique_warnings", [])[:8]:
            out.append(f"  - warning: `{w}`")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--runs", required=True, help="comma-separated run ids")
    parser.add_argument("--copy-screenshots", action="store_true")
    parser.add_argument("--screenshot-runs", help="comma-separated subset of runs whose screenshots are copied")
    args = parser.parse_args()

    runs = [r.strip() for r in args.runs.split(",") if r.strip()]
    condensed = [condense_run(args.raw, run) for run in runs]
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "browser-splat-results.json"), "w", encoding="utf-8") as f:
        json.dump(condensed, f, indent=2)
    with open(os.path.join(args.out, "browser-splat-results.md"), "w", encoding="utf-8") as f:
        f.write(markdown(condensed))

    if args.copy_screenshots:
        subset = {r.strip() for r in (args.screenshot_runs or "").split(",") if r.strip()}
        for c in condensed:
            if subset and c["run"] not in subset:
                continue
            target = os.path.join(args.out, "screenshots", c["run"])
            for case in SCREENSHOT_CASES:
                source = os.path.join(args.raw, c["run"], case + ".jpg")
                if os.path.exists(source):
                    os.makedirs(target, exist_ok=True)
                    shutil.copyfile(source, os.path.join(target, case + ".jpg"))
    print("wrote", os.path.join(args.out, "browser-splat-results.md"))


if __name__ == "__main__":
    main()
