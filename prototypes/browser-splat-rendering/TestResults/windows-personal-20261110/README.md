# Personal Windows browser baseline — November 10, 2026

## Finding

Both completed runs record Windows display mode **3840x2160 @ 30 Hz**. Frame intervals stay near 33.3 ms across 25k, 100k and 250k splats, while measured CPU work rises from about 1 ms to 9 ms. Display-paced browser scheduling is the leading explanation for the flat 30 fps result; these runs do not establish the machine's uncapped rendering capacity. GPU execution time was not measured.

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

## Frame timings

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

## Drawing order

Both runs match all eight expected overlap outcomes. The merged renderer and its preloaded active ranges draw the expected states. Separate renderers still misorder the overlap, and forced draw order still covers the wrong region; 8/8 means reproduced expectations, not that the known defect was fixed.

![One merged renderer: expected overlap](overlap_merged_single_renderer.jpg)

![Forced renderer order: backdrop covers the wrong region](overlap_separate_A_forced_last.jpg)

These synthetic switches do not establish cabinet registration, partial-rescan replacement, streaming, stable data anchors or interaction geometry.

## Memory, logs and cleanup

- Maximum allocated WebAssembly heap capacity observed in each page: 198.75 MiB. This is not total browser RAM or GPU memory.
- Each page console records zero errors and one expected CPU-sort warning.
- Chrome process stdout additionally contains push-registration/authentication and updater-pipe diagnostics. They are separate from page-console errors; the result files provide no evidence that they prevented the test.
- Each HTTP server log has only a favicon 404 among non-success responses.
- Both harness records report no leftover test processes and successful deletion of the temporary profile.
- Arlen's pasted Edge console shows WinError 10054 during browser shutdown. The source closes the browser before stopping the HTTP server, and Python's default request error handler prints peer-reset tracebacks. All case data and completion records are present. This supports a shutdown-logging issue; retain unexpected errors and incomplete-run failures when fixing it.
- Both runs came from the OneDrive-synced folder identified by the harness. This can add measurement noise but is not evidence that OneDrive caused the flat frame rate.

## Next measured step

On the personal PC, inspect Windows Advanced display for the screen used by the browser. If a supported 60 Hz or higher mode is available, choose it and repeat the two unchanged baselines from a folder outside OneDrive, preserving the original run folders. Collect a new results ZIP. If only 30 Hz is offered, first identify the display and connection/virtual-display setup. No program, driver or security setting should be changed merely to force a result.

Browser animation callbacks generally follow display refresh ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)); Windows exposes supported refresh choices in Advanced display ([Microsoft](https://support.microsoft.com/en-us/windows/hardware/display-graphics/change-the-refresh-rate-on-your-monitor-in-windows)). A higher-refresh repeat can test the pacing explanation; it does not guarantee any particular higher frame rate.

Company Toughbook execution remains blocked pending company authorization (D035), and its 30 fps qualification remains open. Standalone Quest and phone tests remain open. Benchmark code, the original ZIP, rendering settings and measured values were not changed during this review.
