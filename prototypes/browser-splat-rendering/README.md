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
| `Tools/browser_test_harness.py` | Local server plus browser launcher (fresh temporary profile; stops only the session it started) |
| `Tools/summarize_results.py` | Condenses raw runs into `TestResults/` |
| `TestResults/` | Tracked summary and selected half-size screenshots. `TestResults/raw/` is ignored |

Generated folders (`Library/`, `Builds/`, `Logs/`, `UserSettings/`, `Fixtures/Generated/`, `TestResults/raw/`) are ignored by this folder's `.gitignore`.

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

`--browser` accepts `chrome`, `firefox`, `brave` or `chromium`; a browser that is not installed is reported as untested. The window must stay visible while the test runs, because browsers throttle hidden pages. Page parameters (`suites`, `counts`, `measure`, `quality`, `scale` and others) are documented at the top of `BrowserBenchmark.cs` and are passed with `--query key=value`.

## Test design

- Fixtures are synthetic: a procedural equipment room (floor, walls, two rack rows with RU-like bands and LEDs, a wall cabinet) sampled at 25k-2M splats, plus overlap sections. No capture or operational data is used.
- Overlap sections model a partial rescan. Section A, the larger existing capture, has a red sheet at z = 0.0 and a far backdrop. Section B, the rescanned area, has a blue sheet at z = 0.3. They share the band x = -0.5 to 0.5, where A's sheet is in front of B's. Correct per-splat ordering shows red in that band. If whole renderers are ordered by bounds-center distance, B draws last and the band turns blue. Forcing A to draw last fixes the band but paints A's backdrop over B's own region. The cases compare one merged renderer, two separate renderers, forced render order and active-range switching on one merged asset.
- A screenshot proves the page rendered something. Region colors sampled from the screenshot check that the overlap cases rendered in the expected order. A successful build alone is not treated as rendering evidence.
