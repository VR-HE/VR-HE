# Next local task: Toughbook browser test bundle

Status: bundle prepared November 10, 2026 from commit 7d07732 and initially checked on Linux and under Wine emulation; subsequent personal Windows runs are recorded below. Company authorization is required for the work Toughbook and has not been provided. Arlen completed Edge/Chrome baselines on his personal Windows 11 VR gaming PC (D035) using the existing bundle; the uploaded archive was reviewed. The higher-refresh follow-up was also reviewed: both browsers reach about 60 fps through 250k splats at a recorded 60 Hz display mode and 1280x720 canvas. See the handoff for the next proposed interactive-demo task. Uncapped/larger-scene capacity and all Toughbook results remain pending.

## Context and target

Work in ~/Projects/VR-HE on proto/browser-splat-rendering. Follow [AGENTS.md](../AGENTS.md), the [handoff](HANDOFF.md), [test plan](TEST_PLAN.md) and [prototype README](../prototypes/browser-splat-rendering/README.md).

Arlen's reference Toughbook FZ-55 has an Intel Core i5-8365U (4 cores / 8 logical processors), 32 GB RAM and Intel UHD Graphics 620. Task Manager shows graphics driver 31.0.101.2141 and a Samsung SATA SSD with 477 GB capacity. These are screenshot observations; exact Windows/browser versions, free disk space, browser WebGL backend and runtime performance are unverified.

The browser floor is 30 application-rendered fps (D034). Do not infer a splat budget or a pass from the RTX 4060 laptop runs. The separate VR floor remains 60 fps; this task does not test VR.

Execution update (D035): do not run or propose a workaround on the company Toughbook before company authorization. Test the existing ZIP on the personal Windows 11 PC and report its actual hardware, OS/browser behavior and performance. The original packaging specification below remains as the completed-task record; the bundle name is not evidence that the Toughbook was tested.

## Session and scope

- Continue with verified Opus 5.5 and MAX effort. Check the branch and tree, preserve existing work, and fast-forward pull only when safe.
- Use the existing local WebGL 2 benchmark build and reproducibly generated synthetic fixtures where possible. Preserve the baseline renderer, quality and fixture definitions before optimization.
- Keep The Veil and its bridge untouched. Every required Editor operation must name the explicit prototype project path; no new editor/module is needed for packaging.
- Use generated artifacts on the development laptop. No operational capture, workbook, uploaded photograph, credential or personal identifier belongs in the test bundle or Git history.

## Deliverable

Prepare one ZIP that Arlen can transfer to the Toughbook, extract and use without installing Unity, Git or Claude there.

1. Include the WebGL build, required small synthetic fixtures, local test server and short plain-language instructions. Offer separate Edge and Chrome launchers and a documented manual fallback.
2. Detect prerequisites, especially Python 3, instead of assuming they are installed. Use an existing runtime when available; if a portable runtime is required, document its source, version, license and size. State any unresolved prerequisite clearly.
3. Support paths containing spaces. Discover actual Windows browser installations. Use fresh temporary test profiles and stop only processes created by the test; preserve existing browser sessions and profiles.
4. Bind the server to loopback and handle an occupied port. Do not use or alter The Veil's port 9002. Avoid administrator requirements and system-wide settings changes.
5. Start with overlap cases and 25k, 100k and 250k splats. Offer 500k as an optional follow-up after the smaller cases; do not automatically run SH3, 1M or 2M stress cases on the first work-laptop run.
6. Keep the 1280x720 canvas, quality level and render scale comparable to the prior measurements; record actual values. Use fresh pages for independent memory comparisons.
7. Collect browser version, actual WebGL/GPU facts, frame-time statistics, errors and screenshots using the existing benchmark. Capture Windows build information where available without collecting host names, user names, serial numbers or operational data.
8. Present a clear completion/error message and the results-folder path. Treat 30 fps as the user floor and report frame pacing/stalls; detailed production acceptance criteria remain open.

## Verification and handoff

Verify the packaged files and local server/browser behavior on the available Linux laptop. Check the Windows launchers and process-cleanup code, preserving Linux behavior. Keep real Windows execution untested until an actual Windows run occurs, and identify the host. A personal Windows 11 run can establish that PC's behavior; it does not qualify the company Toughbook. Syntax checks or mocks do not constitute either device test.

Commit and push source, scripts and documentation. Keep ZIPs, builds, caches, generated fixture binaries and raw results ignored; retain the established synthetic-summary policy.

Finish by reporting:
- The exact absolute ZIP path on the development laptop, its size and checksum.
- Simple transfer/extract/launch instructions for Arlen and any runtime prerequisite.
- Which checks actually ran and what still requires the Toughbook.
- How Arlen retrieves the Edge and Chrome result files after the run.

Keep compact-format tests, sort-refresh experiments and real captures for later measured steps; do not combine them with this first hardware baseline.
