# Personal Windows browser baseline — November 10, 2026

## Finding

The initial two runs record **3840x2160 @ 30 Hz** and roughly 30 fps. Two follow-up runs record **3840x2160 @ 60 Hz** and roughly 60 fps through 250k splats, with similar CPU costs. This strongly supports display pacing as the earlier ceiling. Both tests are refresh-limited short synthetic baselines; uncapped capacity and GPU execution time remain unmeasured.

The browser prototype rendered the synthetic scenes in real Windows Edge and Chrome on Arlen's personal gaming PC. This is not Toughbook qualification, a standalone Quest test, or a test of the complete work utility.

## Provenance and checks

- Input: user-uploaded VRHE-results-20261110-212233.zip, SHA-256 `62be2a96730f29f79c8da69c889a6090bbebf3ca0e7babc25af87dc639ca8b2c`.
- Archive: 109 entries, 13,076,034 bytes unpacked; all CRC checks passed.
- Bundle tooling/source: `7d077329695f9b0a1fbc835fd8dfa2c96d0d9f89`; collection harness version 2.
- Edge run: tb-20261110-210406-edge-baseline.
- Chrome run: tb-20261110-211805-chrome-baseline.
- Both done records and summaries report completion. All 22 case JSON records match their summary copies, and all required per-case JSON, frame arrays, JPG and PNG files are present.
- FPS was recomputed from every per-frame interval array and agrees with the recorded averages. Eleven corresponding full-resolution PNGs are byte-identical between browsers.
- Selected merged, forced-order and room screenshots were visually inspected. Two small synthetic screenshots are retained below; the raw archive, full-resolution images and raw frame arrays remain outside Git.

## Recorded configuration

| Item | Value |
| --- | --- |
| Host | Personal Windows 11 Home 26H2, build 26300.9711 |
| CPU | AMD Ryzen 7 7800X3D, 16 logical processors |
| RAM | Native Windows collector reports 31.2 GiB usable physical memory |
| Active WebGL renderer | NVIDIA GeForce RTX 5070 Ti through ANGLE / Direct3D 11, WebGL 2 |
| Browsers | Edge 155.0.4283.45; Chrome 155.0.8059.82 |
| Display mode | 3840x2160 @ 30 Hz in both native Windows records |
| Benchmark | Unity 6000.3.15f1; UnitySplats revision 689e0a7; CPU fallback enabled |
| Canvas and quality | 1280x720; Mobile quality; render scale 1.0; browser pixel ratio 1.75 |
| Source and runtime | Synthetic SH0 fixtures; bundled Python 3.14.10; fresh temporary browser profiles |

The native adapter inventory also lists Virtual Desktop, Meta virtual-monitor and Mixed Reality Link display drivers. Their presence does not prove the test was viewed through VR or establish which physical/virtual display hosted the browser. Confirm the display used before changing its mode.

Unity's browser SystemInfo reports Windows 10, one processor and 128 MB system memory. These do not match the native Windows records; do not use those browser placeholders as the actual PC configuration.

## Initial 30 Hz frame timings

CPU is frame start to end of URP rendering on the main thread. The sort stage includes sorting, order upload and draw submission. GPU execution is asynchronous and unmeasured. Times are milliseconds and individual samples have about 1 ms resolution.

| Browser | Splats | Mean fps | CPU mean | Sort-stage mean | Interval p95 | Longest interval | Frames >=36 ms / >=100 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| edge | 25,000 | 29.997 | 1.12 | 0.67 | 34 | 34 | 0 / 0 |
| edge | 100,000 | 30.000 | 3.39 | 3.23 | 34 | 34 | 0 / 0 |
| edge | 250,000 | 30.000 | 9.06 | 8.91 | 34 | 34 | 0 / 0 |
| chrome | 25,000 | 29.995 | 1.29 | 0.81 | 34 | 34 | 0 / 0 |
| chrome | 100,000 | 30.000 | 3.66 | 3.35 | 34 | 34 | 0 / 0 |
| chrome | 250,000 | 30.000 | 9.01 | 8.80 | 34 | 34 | 0 / 0 |

Across all 22 cases, the longest recorded interval is approximately 34 ms; no measured frame reached either descriptive slow/stall threshold. This is short-run evidence at a 30 Hz display mode, not a finalized production acceptance verdict.

The console's `<30` labels compare the unrounded average with 30. Some values are 29.999999999999996 due to floating-point arithmetic; others differ by about 0.003-0.010 fps because of finite sampling and timer steps. Rounded display of 30.0 with a `<30` marker is not evidence of a meaningful drop by itself. Preserve the user floor; clarify reporting rather than changing acceptance silently.

## Follow-up at 60 Hz

Arlen uploaded VRHE-results-20261110-214722.zip (SHA-256 `3fc34c692447265edcf24240c6b12bba2dace69e3a0d238a8675c1275674195a`). It contains the original two runs plus two new baselines, not four new runs. All 108 entries from the earlier archive other than collect.json are byte-identical; the cumulative archive passes every CRC check.

| New run | Browser | Native display mode |
| --- | --- | --- |
| tb-20261110-214316-edge-baseline | Edge 157.0.4341.42 | 3840x2160 @ 60 Hz |
| tb-20261110-214528-chrome-baseline | Chrome 155.0.8059.82 | 3840x2160 @ 60 Hz |

Hardware, bundle source 7d07732, 1280x720 canvas, Mobile quality and scale 1.0 match the original records. Edge changed from 155 to 157, so that comparison is not isolated to display refresh. Chrome stayed at exactly the same version and its frame cadence doubled too. Together these results strongly support display pacing as the earlier limit; they do not measure uncapped capacity or GPU execution time.

| Browser | Splats | Mean fps | CPU mean ms | Sort-stage mean ms | Interval p95 ms | Longest interval ms |
| --- | --- | --- | --- | --- | --- | --- |
| edge | 25,000 | 60.000 | 1.09 | 0.97 | 17 | 17 |
| edge | 100,000 | 60.000 | 3.67 | 3.34 | 17 | 17 |
| edge | 250,000 | 60.000 | 9.32 | 8.99 | 17 | 17 |
| chrome | 25,000 | 60.000 | 1.01 | 0.73 | 17 | 20 |
| chrome | 100,000 | 60.000 | 3.51 | 3.18 | 17 | 17 |
| chrome | 250,000 | 60.000 | 9.01 | 8.74 | 17 | 17 |

Both new runs complete all 11 cases. Every case JSON matches its summary and all frame arrays reproduce recorded FPS. Each browser matches all eight expected overlap outcomes; the known separate-renderer errors remain. The 11 corresponding new PNG pairs are byte-identical between browsers.

No new page-console error or measured interval >=36 ms occurred. All p95 intervals are about 17 ms; the longest is 20 ms in Chrome's 25k case, while Edge stays near 17 ms. WebAssembly capacity still peaks at 198.75 MiB, and both harness records report clean process/profile cleanup. No 500k or larger follow-up is included.

The native display mode is 4K, but the measured Unity canvas remains 1280x720. These are not 4K-rendering, minimum-Toughbook, real-capture, long-session, phone or standalone Quest results. No benchmark code, bundle, driver setting or user device was changed by Codex during the review.

## Drawing order

All four runs match all eight expected overlap outcomes. The merged renderer and its preloaded active ranges draw the expected states. Separate renderers still misorder the overlap, and forced draw order still covers the wrong region; 8/8 means reproduced expectations, not that the known defect was fixed.

![One merged renderer: expected overlap](overlap_merged_single_renderer.jpg)

![Forced renderer order: backdrop covers the wrong region](overlap_separate_A_forced_last.jpg)

These synthetic switches do not establish cabinet registration, partial-rescan replacement, streaming, stable data anchors or interaction geometry.

## Memory, logs and cleanup

- Maximum allocated WebAssembly heap capacity observed in each page: 198.75 MiB. This is not total browser RAM or GPU memory.
- Each page console records zero errors and one expected CPU-sort warning.
- Chrome process stdout additionally contains push-registration/authentication and updater-pipe diagnostics. They are separate from page-console errors; the result files provide no evidence that they prevented the test.
- Each HTTP server log has only a favicon 404 among non-success responses.
- All four harness records report no leftover test processes and successful deletion of the temporary profile.
- Arlen's pasted Edge console shows WinError 10054 during browser shutdown. The source closes the browser before stopping the HTTP server, and Python's default request error handler prints peer-reset tracebacks. All case data and completion records are present. This supports a shutdown-logging issue; retain unexpected errors and incomplete-run failures when fixing it.
- The initial pasted Edge console identifies a OneDrive-synced folder. The sanitized archives do not independently establish every run's working folder. Sync activity can add noise, but it is not recorded evidence of the flat frame-rate cause.

## Next measured step

The requested higher-refresh repeat is complete. No further repetition of these small baselines is required before the next browser interaction prototype. Preserve the benchmark as comparison evidence while preparing [the interactive browser demo task](../../../../docs/INTERACTIVE_BROWSER_DEMO_TASK.md). Larger/compact scenes, weakest-device qualification and standalone Quest rendering remain separate measured work.

Browser animation callbacks generally follow display refresh ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)); Windows exposes supported refresh choices in Advanced display ([Microsoft](https://support.microsoft.com/en-us/windows/hardware/display-graphics/change-the-refresh-rate-on-your-monitor-in-windows)). The observed higher-refresh repeat supports the pacing explanation; it does not establish uncapped throughput.

Company Toughbook execution remains blocked pending company authorization (D035), and its 30 fps qualification remains open. Standalone Quest and phone tests remain open. Benchmark code, the original ZIP, rendering settings and measured values were not changed during this review.
