# Browser Gaussian-splat rendering prototype

First VR-HE implementation milestone: prove or disprove Gaussian-splat rendering in desktop browsers before committing to a renderer. This folder is an isolated Unity project. It is a measurement prototype, not the VR-HE application.

Status and results: see [TestResults/browser-splat-results.md](TestResults/browser-splat-results.md), the [handoff](../../docs/HANDOFF.md) and the [development log](../../docs/DEVELOPMENT_LOG.md).

## Results so far (November 10, 2026)

Tested on one laptop: Linux Mint 22.3, Intel Core i7-13620H, NVIDIA RTX 4060 Laptop GPU, 60 Hz display.

- Chrome 157, Firefox 159 and Brave 1.99 (Chromium 157) all rendered the synthetic scenes over WebGL 2, with no browser flags and no console errors. Edge and Chromium were not installed and are untested.
- UnitySplats sorts on the browser's main thread every frame, and that sort set the frame rate. About 500k splats held 60 fps in Chrome and Brave (55 in Firefox); 1M gave about 30 fps and 2M about 10.
- Overlapping sections drew in the correct order only when merged into one asset and renderer. Two separate renderers misordered the overlap in every browser, and forcing their order only moved the error. Active ranges on the merged asset switched sections correctly without reloading.
- Runtime decoding of a 500k-splat SH3 PLY peaked at 1.7 GB of WebAssembly heap.

This is an upper bound from one high-end laptop with synthetic data, not an acceptance result.

## What it contains

| Path | Purpose |
| --- | --- |
| `Assets/BrowserSplatTest/Runtime/BrowserBenchmark.cs` | Self-reporting benchmark. It loads fixtures over HTTP, renders them with UnitySplats, measures frames and posts JSON and screenshots back to the local server |
| `Assets/BrowserSplatTest/Runtime/FrameTimer.cs` | Player-loop timestamps around UnitySplats' CPU sort hook and URP rendering |
| `Assets/BrowserSplatTest/Plugins/WebGL/BrowserBridge.jslib` | Reads browser/WebGL facts (renderer string, WebGL version, isolation) and the page status line |
| `Assets/BrowserSplatTest/Editor/BenchmarkProjectSetup.cs` | Batch-mode setup (UnitySplats settings, URP feature, scene, WebGL player settings) and WebGL build |
| `Assets/WebGLTemplates/VRHEBenchmark/` | Page template: fixed 1280x720 canvas at device-pixel-ratio 1; console output forwarded to the local server |
| `Tools/generate_synthetic_splats.py` | Writes synthetic 3DGS PLY fixtures (procedural room, overlap sections) |
| `Tools/browser_test_harness.py` | Local server plus browser launcher for Linux and Windows (fresh temporary profile; stops only the browser it started), manual-mode server and results collector |
| `Tools/package_toughbook_bundle.py` | Builds the Windows reference-PC test ZIP from the existing build (see below) |
| `Tools/windows-bundle/` | Windows launchers and plain-language instructions copied into that ZIP |
| `Tools/summarize_results.py` | Condenses raw runs into `TestResults/` |
| `TestResults/` | Tracked summary and selected half-size screenshots. `TestResults/raw/` is ignored |

Generated folders (`Library/`, `Builds/`, `Logs/`, `UserSettings/`, `Fixtures/Generated/`, `TestResults/raw/`, `Bundles/`) are ignored by this folder's `.gitignore`.

## Dependencies and licenses

Unity 6.3 LTS 6000.3.15f1 with the URP blank template (`com.unity.template.urp-blank` 17.0.14) was approved for this initial prototype only. The long-term Unity version and renderer remain provisional.

| Package | Pinned version | License notes |
| --- | --- | --- |
| `com.arloopa.unitysplats` (UnitySplats 2.0.0) | Git revision `689e0a7dd2acfad813494a205f8ebbe8eee86434` | MIT. Its Third Party Notices list MIT-licensed gsplat-unity, PlayCanvas Engine, UnityGaussianSplatting, GPUSorting, Spark, Niantic SPZ and ZstdSharp; Unity.WebP is MIT and libwebp is BSD-3-Clause. A GPL-3.0 Blender add-on (Splatlight) is listed as a behavior reference only; the notice states no Splatlight code is included |
| `com.netpyoung.webp` | 0.3.22 from the OpenUPM scoped registry (`com.netpyoung` scope only) | Required by UnitySplats. Unity reports it as installed without a package signature |
| `com.unity.mathematics` | Resolved by Unity (see `Packages/packages-lock.json`) | Unity package |

No AI Assistant or Pipeline package is installed in this project, and it has no Unity bridge/MCP connection.

## Regenerate and rebuild

Use explicit project paths so no other Unity project or Editor bridge is affected.

```bash
P=~/Projects/VR-HE/prototypes/browser-splat-rendering
UNITY=~/Unity/Hub/Editor/6000.3.15f1/Editor/Unity

python3 -I "$P/Tools/generate_synthetic_splats.py" --out "$P/Fixtures/Generated" --overlap

"$UNITY" -batchmode -quit -nographics -projectPath "$P" \
  -executeMethod VRHE.BrowserSplatTest.Editor.BenchmarkProjectSetup.SetupBatch -logFile setup.log

"$UNITY" -batchmode -quit -nographics -projectPath "$P" -buildTarget WebGL \
  -executeMethod VRHE.BrowserSplatTest.Editor.BenchmarkProjectSetup.BuildWebGLBatch \
  -vrheBuildOutput "$P/Builds/WebGL" -logFile build.log
```

Under `-nographics`, UnitySplats logs missing compute kernels during setup. The null graphics device has no compute support, so these errors do not affect the WebGL path, which uses no compute shaders.

## Run a browser test

```bash
python3 -I "$P/Tools/browser_test_harness.py" run --browser chrome --run <run-id> \
  --build "$P/Builds/WebGL" --fixtures "$P/Fixtures/Generated" --results "$P/TestResults/raw" \
  --profile-root <scratch folder for temporary profiles>
python3 -I "$P/Tools/summarize_results.py" --raw "$P/TestResults/raw" --out "$P/TestResults" \
  --runs <run-id>[,<run-id>...] --copy-screenshots
```

`--browser` accepts `chrome`, `edge`, `firefox`, `brave` or `chromium`; a browser that is not installed is reported as untested (exit code 3). The window must stay visible while the test runs, because browsers throttle hidden pages. Page parameters (`suites`, `counts`, `measure`, `quality`, `scale` and others) are documented at the top of `BrowserBenchmark.cs` and are passed with `--query key=value`. `--plan baseline` (overlap cases plus 25k, 100k and 250k splats in one page) and `--plan followup-500k` (500k in a fresh page, only after a finished baseline for the same browser) set the reference-PC parameters; everything else stays at the benchmark defaults. Without `--run`, a run id is generated from the time, browser and plan. The harness now opens the benchmark through a small `/start` page that records the browser's own version (User-Agent Client Hints), screen and scaling facts in `client.json` and waits while the tab is hidden; the benchmark page, build and measurement are unchanged. On Linux the browser flags are the same as in the November 10 runs.

`serve` starts the manual-mode server: its page at `/` starts a run in whichever browser opens it, and the server prints the same completion report when the page finishes. `collect` packs a results folder into one ZIP, replacing user-folder, user, domain and computer names in text files with placeholders.

## Windows reference-PC bundle

`Tools/package_toughbook_bundle.py` builds one ZIP for the browser reference PC (the Toughbook FZ-55, D033) without rebuilding anything:

```bash
python3 -I "$P/Tools/package_toughbook_bundle.py"        # refuses to run on uncommitted changes
```

- It copies the existing `Builds/WebGL` build. IL2CPP compiles the Unity Editor's install path into 16 error-message strings in `WebGL.wasm`; where that path is inside the developer's home folder, the bundle's copy has the folder name replaced by `x` characters of the same length. This changes data bytes only, not code, and `bundle.json` records both hashes.
- It regenerates the 25k-500k scenes and overlap fixtures and fails unless they are byte-identical to `Fixtures/Generated`.
- It adds the harness, the launchers from `Tools/windows-bundle/` (converted to CRLF, ASCII only) and the unmodified Python 3.14.10 embeddable package for 64-bit Windows from python.org (pinned SHA-256; PSF License; about 24 MB unpacked) as a fallback when no Python 3.8+ is installed. It also adds the UnitySplats and WebP license notices.
- `bundle.json` lists checksums that the harness verifies before each run. The script then scans every bundled file for the developer's home path and account name and for the global Git identity, plus any terms given in `VRHE_PRIVACY_TERMS`; it fails if any is found.
- Output, ignored by Git: `Bundles/VRHE-Toughbook-Browser-Test-<date>-<commit>.zip` and a `.sha256` file. `Bundles/cache/` holds the downloaded Python package.

On Windows the launchers find an installed Python (`py -3`, `python`, `python3`; the Microsoft Store Python is skipped because it redirects temporary-folder writes) or use the bundled one. They avoid parenthesized blocks so that folder names with spaces, parentheses or `&` work. The harness finds Edge and Chrome under Program Files, Program Files (x86), the per-user LocalAppData folder or the App Paths registry key, and reads their version from the executable's version resource without starting them. It claims its loopback port exclusively and never uses 9002. It tracks the launched browser's process tree, identifying each process by ID and creation time, and stops only that tree. It reports a browser that never opens the page (for example a sign-in screen) or that hands the page to an already-open window. It records the Windows edition and build, CPU, RAM, GPU driver, display mode and power state, but not host, user or owner names or serial numbers. Treat all of this as untested on real Windows until a recorded Toughbook run; see the handoff for what was checked on Linux and under Wine.

## Test design

- Fixtures are synthetic: a procedural equipment room (floor, walls, two rack rows with RU-like bands and LEDs, a wall cabinet) sampled at 25k-2M splats, plus overlap sections. No capture or operational data is used.
- Overlap sections model a partial rescan. Section A, the larger existing capture, has a red sheet at z = 0.0 and a far backdrop. Section B, the rescanned area, has a blue sheet at z = 0.3. They share the band x = -0.5 to 0.5, where A's sheet is in front of B's. Correct per-splat ordering shows red in that band. If whole renderers are ordered by bounds-center distance, B draws last and the band turns blue. Forcing A to draw last fixes the band but paints A's backdrop over B's own region. The cases compare one merged renderer, two separate renderers, forced render order and active-range switching on one merged asset.
- A screenshot proves the page rendered something. Region colors sampled from the screenshot check that the overlap cases rendered in the expected order. A successful build alone is not treated as rendering evidence.
