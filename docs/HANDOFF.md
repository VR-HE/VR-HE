# Developer and assistant handoff

Updated November 10, 2026.

## Current state

VR-HE/VR-HE is the selected private repository. ChatGPT/Codex is authenticated as VR-HE with read and write permissions. Initial documentation is prepared on docs/project-foundation; check the pull request for whether it has been merged.

The baseline main commit before this documentation change is d731a368d7121f31d248446f7feac04ddb6e6e06. Consult GitHub history for the current head; a document cannot reliably name its own final commit in advance.

There is no VR-HE application or runnable demo yet. The first implementation milestone, browser Gaussian-splat rendering (D032), has a rendering-only Unity prototype in prototypes/browser-splat-rendering on branch proto/browser-splat-rendering; its results are in the browser milestone section below. No capture, navigation, editing, backend, sync or security implementation exists, and no phone or Quest test has run. The prepared Windows bundle completed Edge/Chrome baselines on the personal Windows 11 PC; its recorded 30 Hz display mode limits performance interpretation (see the reviewed Windows results below). Arlen's supplied laptop output confirms Git 2.43.0 and successful installation of the gh 2.45.0 Ubuntu package. Arlen supplied a screenshot confirming completed local authorization and account lookup as VR-HE. His subsequent screenshot confirms a successful clone into /home/arlen/Projects/VR-HE, docs/project-foundation tracking origin/docs/project-foundation, and no working-tree changes. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration. Claude Code's November 10 local inspection recorded the installed Unity tooling below; the inspection itself created or changed no Unity project.

## Read in this order

1. [Shared instructions](../AGENTS.md)
2. [Product specification](PRODUCT_SPEC.md)
3. [Confirmed decisions](DECISIONS.md)
4. [Spreadsheet synchronization](SPREADSHEET_SYNC.md)
5. [Proposed architecture](ARCHITECTURE.md)
6. [Test plan](TEST_PLAN.md)
7. [Integration controls](INTEGRATIONS.md)
8. [Capture updates](CAPTURE_UPDATES.md)
9. [Built-in user guide plan](USER_GUIDE_PLAN.md)
10. [Development log](DEVELOPMENT_LOG.md)
11. [Cabinet inspection states](CABINET_STATES.md)
12. [AI-assisted capture inventory](AI_CAPTURE_INVENTORY.md)
13. [Supplied spreadsheet examples](SPREADSHEET_EXAMPLES.md)
14. [Browser splat-rendering prototype](../prototypes/browser-splat-rendering/README.md)

The earlier ISP_Virtual_Tour_Product_Brief.md informed this baseline. The repository specification is now the maintained project source of truth; do not maintain competing copies.

## Next setup work

Local VR-HE sign-in, clone, the Claude session configuration and the local Unity inventory are complete. Arlen approved Unity 6.3 LTS 6000.3.15f1 with the plain URP 3D template for the initial prototype (D031). The prototype branch is **proto/browser-splat-rendering**, created from docs/project-foundation at ff1e070. It holds the prototype and this milestone's documentation updates; docs/project-foundation does not have them. He answered Yes to Git credential configuration during login; do not repeat authentication solely to change that answer. Do not assume commands in a cloud workspace ran on his laptop.

Authentication and repository read access are confirmed. Local push access is verified: the inspection commit ff1e070 is on origin/docs/project-foundation. Local commits use the repository-local Git identity VR-HE with the account's GitHub noreply address, as Arlen chose on November 10. Do not paste passwords, tokens or login codes into chat.

If these branches are still unmerged, check out proto/browser-splat-rendering when continuing; do not mistake the starter README on main for the full project.

## MAX effort for Claude build work

Arlen explicitly requires MAX effort. The [launcher](../scripts/start-claude.sh) sets a process-scoped effort request and starts Claude in this repository.

For later sessions:
1. Pull the latest working branch with git pull --ff-only.
2. Check claude --version.
3. Run bash scripts/start-claude.sh.
4. Check the active model/effort control, using /model or /effort, before starting build work.
5. Record the observed version, model and actual effort.

The current Claude Code docs support session launch requests and a process environment setting; they do not accept max as a persisted effortLevel value. The client/model can reduce an unsupported request, so a successful launch alone does not prove MAX.

The November 10 screenshot completes the current startup checkpoint: v2.1.321, Opus 5.5, max effort, correct project folder. The inspection session confirmed it locally: the process was started as claude --effort max, with CLAUDE_CODE_EFFORT_LEVEL=max, from the 2.1.321 binary. Claude Code then updated itself on disk to 2.1.322, and Opus 5.5 was selected for that session only. At the next start, select Opus 5.5 again and re-check version and effort. If a session shows a lower level, resolve and record the difference.

References: [model/effort configuration](https://code.claude.com/docs/en/model-config), [CLI reference](https://code.claude.com/docs/en/cli-reference).

## Local Unity inspection — November 10 findings

Claude Code completed [the inspection task](LOCAL_UNITY_INSPECTION.md) with read-only checks. Installed files and Hub/CLI metadata are installation evidence only. During the inspection no Editor was launched, nothing was built, and no device, browser or splat renderer was tested; the browser milestone below came later.

Verified on Arlen's laptop:
- Unity Hub 3.22.6 (apt package unityhub, /usr/bin/unityhub) and Unity CLI 1.0.0-beta.13 (~/.local/bin/unity).
- Editors are installed at ~/Unity/Hub/Editor/VERSION/Editor/Unity:

| Editor | Hub label | Android: SDK, NDK r27c, OpenJDK 17 | Web | Newer patch listed |
| --- | --- | --- | --- | --- |
| 6000.0.84f1 | Unity 6.0 | Files present | Not installed | 6000.0.85f2 |
| 6000.3.15f1 | Unity 6.3 LTS | Files present | Files present | 6000.3.28f1 |
| 6000.6.2f1 | Unity 6.6 | Not installed | Files present | 6000.6.8f1 |
| 6000.6.4f1 | Unity 6.6 | Files present | Not installed | 6000.6.8f1 |

- 6000.3.15f1 is the only installed editor with both Android and Web support. No editor has iOS Build Support.
- No Android or Quest device was attached to adb. The disk had 24 GB free (95% used); the 6000.3.15f1 install alone uses 27 GB.

Bridges and existing projects:
- Claude Code has no MCP servers configured for the user, VR-HE or any other project; Claude Desktop has none. The installed Unity plugin for Claude Code (unity@unity-agent-plugin 0.1.9-beta) provides skills only and drives editors through the unity CLI.
- unity status reports one running Editor: The Veil (6000.6.4f1, /home/arlen/Desktop/The Veil (Unity)/The Veil), Pipeline state ready. A Unity AI Assistant MCP relay from The Veil's packages is attached to the same Editor; its MCP client port 9002 listens on all network interfaces. At inspection time another Claude Code session was working in The Veil's folder.
- At inspection time VR-HE had no Unity project. The browser prototype added since has no Pipeline or AI Assistant package and no bridge; it is driven only by batch-mode Editor runs with its explicit project path. Fourteen existing Unity projects were found outside this repository; none was modified.
- Never send unity command or MCP requests to The Veil's Editor. Open VR-HE's own project in its own Editor and pass its full path with --project-path on every Editor command.

Recommendation (Arlen approved the version and template for the initial prototype; D031):
- Create the first prototype with the installed Unity 6.3 LTS editor (6000.3.15f1) and its bundled URP blank 3D template (com.unity.template.urp-blank, labeled 3D URP in its metadata). The template includes URP and the Input System.
- Add OpenXR, OpenXR Meta and the XR Interaction Toolkit when the Quest slice starts, through Unity 6.3's Meta Quest build profile. The cached 6.3 VR template's versions (OpenXR 1.17.1, OpenXR Meta 2.5.1, XR Interaction Toolkit 3.5.1) are the reference set.
- Reasons: no download is needed on a nearly full disk. Unity supports 6.3 LTS until December 2027; 6.0 LTS was supported through October 2026, and Update releases such as 6.6 are supported only until the next release. A plain URP project keeps browser and phone builds free of the VR template's XR, AR and hand-tracking packages and its VR-only rig.
- Unity's guidance is mixed: its support page prefers Update releases for new productions, while its 6.3 LTS announcement recommends 6.3 for them. If Arlen wants to start with Quest, the cached 6.3 VR template (10.0.0) is the alternative.

Untested assumptions and risks:
- Browser: Unity 6.3 labels WebGPU experimental; Unity 6.6 says it is out of experimental release. Neither enables WebGPU automatically. The aras-p/UnityGaussianSplatting README names D3D12, Metal and Vulkan as the only known-working graphics APIs, says mobile/web are not tested and says WebGPU "might work someday". Treat the browser path as the highest-risk target. If 6.3's experimental WebGPU blocks it, retest on a newer release before changing the version decision. The browser milestone below tested arloopa/UnitySplats over WebGL 2 instead; WebGPU remains untested.
- Phone and Quest in one project: Unity 6.3's Meta Quest build profile shares Android Player settings and can override Player, Graphics and Quality settings. The docs do not say XR plug-in settings can differ per profile, so test an Android phone profile without XR beside the Quest profile.
- Quest 2: Unity 6.3 lists Quest 2, 3, 3S and Pro for development, but the splat README reports only Quest 3 and Quest Pro among Quest headsets.
- iPhone: native builds need iOS Build Support plus a Mac with Xcode, or Unity Build Automation. No Mac is known to be available.
- The aras-p splat candidate is MIT-licensed, and its author plans no significant further development (README, November 2026). It remains a candidate, not a selection.

Before creating the project (resolved November 10 for the browser prototype):
- Arlen approved the version and template (D031).
- The project is in prototypes/browser-splat-rendering with its own scoped .gitignore; the root ignore rules stay anchored to the repository root.
- No AI Assistant or Pipeline package was added, as Arlen instructed. Without Pipeline, Claude drives the Editor only through batch-mode -executeMethod runs with the explicit project path. Whether later VR-HE projects include these packages remains open.
- Disk space was checked before each step: 25 GB free before project creation and 21 GB after fixtures and builds. No editor or module was installed and nothing was deleted.

Sources: [Unity 6 support](https://unity.com/releases/unity-6/support), [Unity 6.3 WebGPU limitations](https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/webgl/develop/graphics/web-gpu/limitations), [What's new in Unity 6.6](https://docs.unity.com/en-us/engine/6000.6/manual/whats-new/unity66), [Unity 6.3 Meta Quest packages and templates](https://docs.unity.com/en-us/engine/6000.3/manual/xr/configuring-project-for/meta-quest-develop/packages), [Unity 6.3 build-profile overrides](https://docs.unity.com/en-us/engine/6000.3/manual/building-and-publishing/build-settings/build-profiles-override-settings), [Unity 6.3 iOS setup](https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/iphone/getting-started/ios-environment-setup), [UnityGaussianSplatting README](https://github.com/aras-p/UnityGaussianSplatting).

## Browser splat-rendering milestone — November 10 results

Scope: rendering feasibility only (D032). The [prototype](../prototypes/browser-splat-rendering/README.md) is a separate Unity measurement project, not the VR-HE application. Branch: proto/browser-splat-rendering. Full tables: [benchmark results](../prototypes/browser-splat-rendering/TestResults/browser-splat-results.md).

Setup:
- Unity 6000.3.15f1, created in batch mode from its bundled URP blank template (com.unity.template.urp-blank 17.0.14, labeled 3D URP). Every Editor run passed the prototype's explicit project path. No AI Assistant or Pipeline package was added, the project has no bridge or MCP connection, and no command was sent to The Veil's Editor.
- Web build: WebGL 2 only, no compression, 4096 MB maximum memory, and a fixed 1280x720 canvas at device-pixel-ratio 1. Rendering used the Mobile quality level (the WebGL default) at render scale 1.0, with HDR on, MSAA off and linear color space. Both builds succeeded with 0 errors.
- UnitySplats 2.0.0 is pinned to Git revision 689e0a7dd2acfad813494a205f8ebbe8eee86434. Its WebP dependency, com.netpyoung.webp 0.3.22, comes from the OpenUPM registry scoped to com.netpyoung; Unity reports that package unsigned.
- Fixtures are synthetic, generated locally and not committed. They comprise a procedural equipment room at 25k, 100k, 250k, 500k, 1M and 2M splats with base color only (SH0), the 500k room with third-degree spherical harmonics (SH3), and two overlapping sections. The page downloads PLY files from a local server and converts them at runtime with UnitySplats' default Spark compression.
- The harness served the build on 127.0.0.1 only and started each browser with a fresh temporary profile. It stopped only the browser session it had started, and all temporary profiles were deleted.

UnitySplats evaluation at the pinned revision:
- Web path: no compute shaders. Splat data and draw order are packed into RGBA8 textures. A full-precision CPU radix sort runs on the browser's main thread every frame, because Unity Web builds have no managed background threads. The cross-renderer global merge is unavailable on the web, so each renderer draws separately and separate renderers are sorted as whole objects.
- The package forces this texture path for every Unity Web build and disables GPU sorting whenever the path is active. Reading the code, a WebGPU build of the same package would still sort on the main thread; this was not built or tested.
- License: MIT. The Third Party Notices list MIT-licensed gsplat-unity, PlayCanvas Engine, UnityGaussianSplatting, GPUSorting, Spark, Niantic SPZ and ZstdSharp, MIT Unity.WebP and BSD-3-Clause libwebp. A GPL-3.0 Blender add-on, Splatlight, is listed as a behavior reference only; the notice states that none of its code is included.
- Runtime formats: PLY, SOG, SPZ and GLB. Only PLY was tested.

Test laptop: Linux Mint 22.3 (kernel 7.0.0-42, X11, Cinnamon), Intel Core i7-13620H, NVIDIA GeForce RTX 4060 Laptop GPU with driver 595.99.02 and the NVIDIA PRIME profile. The display ran at 1920x1200 and 60 Hz; its 165 Hz mode was not tested.

| Browser | Version | WebGL renderer reported | Runs | Result |
| --- | --- | --- | --- | --- |
| Google Chrome | 157.0.8103.50 | ANGLE on the RTX 4060 Laptop GPU (OpenGL 4.5.0) | 2 full, 3 memory | Rendered |
| Mozilla Firefox | 159.0 | "NVIDIA GeForce GTX 980, or similar" (Firefox reports a generalized GPU name) | 1 full, 2 memory | Rendered |
| Brave | 1.99.55 (Chromium 157) | Same as Chrome | 1 full | Rendered |
| Microsoft Edge | Not installed | — | — | Untested |
| Chromium | Not installed | — | — | Untested |

- Unity reported its OpenGLES3 device, which is WebGL 2.0, in every browser. No browser flags were required. The harness's automation flags (fresh profile, no extensions or sync, no background throttling, fixed window) are recorded in the results JSON. Pages were cross-origin isolated. Chrome and Brave expose the WebGPU API and Firefox 159 did not; WebGPU was not built or tested.
- Each browser rendered the room and the overlap sections; screenshots are in the prototype's TestResults/screenshots folder. The overlap verdicts below come from screen-region colors sampled from screenshots. No run logged a browser console error. Each page logged one expected warning that UnitySplats was using its CPU sort fallback.

Overlapping sections, identical in all four full runs: section A, the larger existing capture, has a red sheet and a far backdrop. Section B, the rescanned area, has a blue sheet 0.3 m behind A's. In their shared band, A must be in front.

| Case | Shared band shows | B-only region shows | Verdict |
| --- | --- | --- | --- |
| One merged asset and renderer | A | B | Correct |
| Two separate renderers | B | B | Wrong: B's bounds center is nearer the camera, so all of B draws over A |
| Two renderers, A forced last | A | A's backdrop | Wrong: A's backdrop now covers B |
| Merged asset with active ranges | Expected section in each step | Expected section in each step | Correct for only A, only B, both and cleared; switching needed no reload |

Splat-count scaling, as frames per second / mean main-thread sort time in ms. The 60 Hz display caps the frame rate.

| Splats | Chrome | Firefox | Brave |
| --- | --- | --- | --- |
| 25k | 60 / 1.3 | 60 / 2.0 | 60 / 1.4 |
| 100k | 60 / 4.1 | 60 / 7.0 | 60 / 3.7 |
| 250k | 60 / 7.7 | 59.8 / 11.3 | 59.9 / 8.1 |
| 500k | 60 / 14.6 | 54.5 / 16.8 | 59.8 / 14.8 |
| 500k SH3 | 60 / 14.6 | 54.8 / 16.7 | 59.7 / 14.8 |
| 1M | 29.4 / 32.9 | 26.2 / 37.0 | 29.1 / 33.3 |
| 2M | 11.4 / 86.9 | 10.4 / 94.9 | 11.0 / 89.7 |

- A second Chrome run matched the first within 2% from 500k splats up.
- The sort dominated frame time. It cost about 29–33 ns per splat in Chrome and Brave from 250k to 1M splats, and 43–45 ns at 2M; Firefox cost 34–45 ns, and 47 ns at 2M. URP rendering took 0.5–1.3 ms on the main thread. GPU time was not measured.
- SH3 did not change frame time at 500k splats; it cost load time and memory.
- Over localhost, Chrome took 132 ms to download, 1.9 s to decode and 94 ms to upload 2M splats. The 500k SH3 file took 4.4–4.8 s to decode.
- Memory, as the WebAssembly heap peak for one file in a fresh page (about 80 MB before loading): 454 MB for 1M splats, 833 MB for 2M and 1.7 GB for 500k SH3 from a 112.5 MB file. Loading every fixture in one page reached 2.0–2.2 GB, above Unity's default 2048 MB limit; this build allows 4096 MB.

Failures and fixes during the milestone:
- The first overlap fixture's backdrop was too narrow, so the forced-order failure showed only as a thin strip that the region check missed. The backdrop was widened and the fixtures regenerated; that smoke run is excluded from the results.
- The first scale screenshot was a blurry close-up. The camera now takes an overview before orbiting.
- Setup under -nographics logs missing UnitySplats compute kernels. The null graphics device has no compute support, and the web path uses no compute shaders.
- During setup the batch Editor logged that it was stopping the ADB server. No device was attached; The Veil's Editor and its relay were checked afterwards and were still running.

Limitations of this evidence:
- One high-end laptop. Weaker CPUs will sort more slowly. Integrated graphics, Windows, macOS and Edge were not tested.
- Synthetic fixtures with simple geometry and mostly base color; real captures differ in density, shape and overdraw.
- Localhost delivery only: no network, compression, caching or slow connection.
- Short sessions of about 90 s per full run. Context loss, long sessions and user interaction were not tested.
- Frame times have 1 ms resolution, and the 60 Hz display hides any headroom above 60 fps.

Why 6000.6.2f1 was not compared: the measured limit is UnitySplats' main-thread CPU sort. The package selects it for every Unity Web build, so it is not an engine limitation. A 6.6 WebGL 2 or WebGPU build of the same package would take the same path unless the package changes, so the comparison would not test the bottleneck.

Remaining platform tests: Edge; Chrome and Firefox on Windows and macOS; the weakest PCs the browser view must support, including integrated graphics; this laptop's 165 Hz mode; a representative real or authorized capture; network delivery; long sessions; and WebGPU if a GPU sort is pursued. Native phone and Quest builds are a separate milestone.

Recommendation, not a decision:
- Keep UnitySplats at the pinned revision as the leading browser candidate on Unity 6.3 LTS. It rendered correctly in all three installed browsers over plain WebGL 2, with no flags and no console errors.
- Budget browser scenes by splat count per view. On this laptop about 500k splats held 60 fps in Chrome and Brave (55 in Firefox), 1M gave about 30 fps and 2M about 10. Slower computers will have a lower budget, which needs measuring.
- For partial rescans and cabinet states in the browser, merge overlapping sections into one asset and switch them with active ranges. Separate renderers misordered the overlap in every browser, and forcing the order only moved the error. By inference, the merge step must place each replaceable section or cabinet state in its own contiguous range.
- Avoid runtime SH3 PLY decoding in browsers (1.7 GB peak at 500k splats). Test the compact SOG or SPZ formats, or lower SH degrees, next.
- If the agreed target needs much more than about 500k splats per view at 60 fps on target hardware, the lever is the sort, not the engine version. Moving it to a Web Worker or a WebGPU compute pass would mean changing or forking UnitySplats; neither option has been tested.

Confirmed after the prototype review (D033/D034):
- Browser reference PC: Arlen's Panasonic Toughbook FZ-55 work laptop.
- Minimum frame rates: 30 fps for the browser; 60 fps for VR headsets. These are requirements, not measured Toughbook/headset results.
- Arlen's November 10 Task Manager photos identify an i5-8365U (4 cores / 8 logical processors), 32 GB RAM and Intel UHD Graphics 620. GPU driver 31.0.101.2141 and a Samsung SATA SSD with 477 GB capacity are shown. Exact OS/browser versions, active browser backend and performance remain unverified. Phone fps, representative content, resolution, memory/quality budgets and detailed pass criteria remain open.
- For Quest, keep application-rendered fps separate from display refresh and synthesized frames. The initial 72 fps at 72 Hz operating target is an engineering recommendation; it does not replace the user floor. Sources and checks are in [the test plan](TEST_PLAN.md).

The Toughbook browser-test bundle requested next is prepared; see the following section.

## Toughbook browser test bundle — November 10

Claude Code carried out [the packaging task](TOUGHBOOK_BROWSER_TEST_TASK.md) on Arlen's development laptop. At packaging signoff the ZIP had not run on Windows. Subsequent personal-PC runs are recorded below; no Toughbook result is claimed.

The ZIP (ignored by Git, on the development laptop):
- Path: ~/Projects/VR-HE/prototypes/browser-splat-rendering/Bundles/VRHE-Toughbook-Browser-Test-20261110-7d07732.zip
- Size: 39,641,682 bytes (37.8 MiB); 68 files and 148,954,133 bytes (142 MiB) unpacked
- SHA-256: c934948138f8c3be35b966a82e64f698c9b2d3f5dbec22bc09d0b0fbe759f526 (also in the .sha256 file beside it)
- Built by Tools/package_toughbook_bundle.py from tooling commit 7d07732 on a clean tree. Rebuilding gives a new creation time in bundle.json and so a different ZIP hash.

Contents:
- The existing November 10 WebGL build, not rebuilt.
- Regenerated synthetic fixtures (25k-500k scenes and the overlap sections), byte-identical to those behind the November 10 results.
- The harness, Edge and Chrome launchers, optional 500k launchers, a manual-server fallback, a results collector and START-HERE.txt.
- A portable Python 3.14.10 fallback: the python.org Windows embeddable package, PSF License, with a pinned SHA-256. OpenSSL verified its Sigstore signature against the signing certificate; the certificate chain and transparency-log entry were not verified.

Privacy:
- IL2CPP had compiled the Unity Editor's install path, which contains the developer's account name, into 16 error-message strings in WebGL.wasm. The bundle's copy replaces that folder name with x characters of the same length. Only data bytes change, and bundle.json records both hashes; the Linux runs below used the masked build.
- A scan of every bundled file found no home path, account name or e-mail address.
- Result ZIPs made by COLLECT-RESULTS.cmd replace user-folder, user, domain and computer names with placeholders.

Toughbook requirements: Windows 10 or 11, Microsoft Edge and/or Google Chrome, at least 0.3 GB free disk space (1 GB recommended), no administrator rights and nothing to install. An installed Python 3.8 or newer is used if present, otherwise the bundled one.

Current test-host constraint (D035): Arlen needs company authorization before executing the benchmark on his work Toughbook and does not have it. Initial Edge/Chrome baselines on his personal Windows 11 VR gaming PC are now reviewed below. Keep the Toughbook minimum reference and 30 fps floor unchanged; this run can establish only the personal PC's Windows/browser behavior and performance.

Arlen's steps on his personal Windows 11 PC:
1. Transfer the existing ZIP from the Linux development laptop into Downloads on the personal PC using an ordinary permitted method, such as USB. Leave Windows security protections enabled.
2. Right-click the ZIP and choose Extract All.
3. In the extracted folder, read START-HERE.txt.
4. Double-click RUN-EDGE.cmd and leave the computer alone until the black window prints FINISHED (2-4 minutes). Then do the same with RUN-CHROME.cmd.
5. Optionally, after both, run OPTIONAL-500K-EDGE.cmd and OPTIONAL-500K-CHROME.cmd.
6. Double-click COLLECT-RESULTS.cmd and copy the VRHE-results-<date>-<time>.zip it shows back to the development laptop. It holds the Edge and Chrome runs.

If the automatic start fails, START-HERE.txt describes the manual fallback (MANUAL-SERVER.cmd and an InPrivate or Incognito window). If Windows or company security blocks a file, stop and report the message; do not work around it.

Checks that ran, on the development laptop only:
- Linux with real browsers, from extracted ZIPs in a folder named with spaces, parentheses and &:
  - Five baselines completed: four in Chrome 157 (automatic and manual, one of each from the final ZIP) and one in Firefox 159. A Chrome 500k follow-up also completed. Every baseline matched 8 of 8 overlap cases, with no console errors.
  - Edge, which is not installed here, was reported untested, and a follow-up without a baseline was refused.
- Manual mode with real Chrome, plus server probes, on the final ZIP's files: 48 of 48 checks. They covered loopback-only binding, port fallback, refusal of 9002, path traversal, Windows device and stream names, upload limits, the POST-only start page and refusal of a second concurrent test.
- Results collection and name scrubbing on the final ZIP's files: 19 of 19 checks.
- Wine 9.0 emulation with the bundled Windows Python. The launchers tested are byte-identical to the final ZIP's.
  - The .cmd launchers: the portable-Python fallback and the not-extracted, incomplete and no-Python messages.
  - 30 of 30 checks of the Windows-only code. They covered process-tree tracking and cleanup with real child processes, recycled-PID guards, version resources, Program Files and App Paths discovery, system facts and exclusive port binding.
  - A Windows run-mode pass with a mock browser that replayed recorded results.
  - The Windows-hosted manual server serving the real benchmark to Linux Chrome.
- Every automatic run, including the Wine runs, recorded no leftover processes and a deleted temporary profile. After the final manual-mode test, no test browser or server process remained.
- These runs measured 52-60 fps, below the earlier November 10 results. The original harness measured the same range on the same cases at the same time, so the new tooling is not the cause; background load (load average 2.4-3.3) is the likely one. These runs check the bundle, not performance.

Still needs the Toughbook:
- Real Windows cmd and Explorer behavior.
- Edge and Chrome launching with fresh profiles, and cleanup of real Chromium process trees.
- SmartScreen, downloaded-file marks and company policies.
- Real registry, powercfg and display facts.
- All Toughbook performance and memory results.

Wine is emulation, and the mock browser is not a browser.

## Reviewed personal Windows results — November 10

Arlen supplied a collected ZIP containing completed Edge 155.0.4283.45 and Chrome 155.0.8059.82 baselines. [The report and compact metrics](../prototypes/browser-splat-rendering/TestResults/windows-personal-20261110/README.md) preserve archive provenance and selected synthetic screenshots.

- Actual host: Ryzen 7 7800X3D, native RAM report 31.2 GiB, RTX 5070 Ti through ANGLE / Direct3D 11, Windows 11 Home 26H2 build 26300.9711.
- Both Windows records show **3840x2160 @ 30 Hz**. All cases are near 30 fps, including the lightest scenes; 250k CPU work averages 9.06 ms (Edge) and 9.01 ms (Chrome). Display pacing is the leading explanation, not measured uncapped capacity.
- All 22 case records match their summaries, frame arrays reproduce FPS, and corresponding PNGs are byte-identical across browsers. All eight expected overlap outcomes match in each run; the known separate-renderer errors remain.
- There are no page-console errors or measured intervals of 36 ms or longer. Peak allocated WebAssembly capacity is 198.75 MiB. Both harnesses report no leftover test processes and deleted temporary profiles.
- The pasted Edge WinError 10054 tracebacks occurred while closing the browser. Complete saved data supports a cleanup-logging issue; fix it narrowly in future tooling without masking failed runs or unrelated errors.
- Chrome process stdout includes background push/updater diagnostics. Unity's browser hardware placeholders differ from native Windows facts; use the latter. OneDrive synchronization and short run duration remain confounders.

Next step: confirm which display hosted the browser and inspect its supported refresh modes. If a supported 60 Hz or higher mode is available, repeat the unchanged baselines outside OneDrive, retaining the original runs; if not, identify the display and connection/virtual-display setup first. Do not infer maximum FPS from CPU time alone. The same ZIP remains usable; no benchmark or bundle was changed during this review.

The company Toughbook stays deferred until company authorization is explicitly confirmed (D035); do not suggest a launcher or transfer workaround. Personal-PC results do not qualify it or standalone Quest. Detailed acceptance criteria and partial-rescan streaming remain open.

## Next mapping work

AI write policy is resolved: Gemini creates drafts; designated editors approve AI-generated entries and updates before live spreadsheet writes. The supplied videos establish facilities-audit and rack/RU mapping targets. Use synthetic examples for the demo and inspect an authorized native workbook/copy before binding real cells. X is resolved: restore both normal camera height and level viewing angle. Q raises and E lowers the viewpoint.

Google Drive, Google Sheets and Gemini compatibility is now required. Do not reopen whether Google Sheets is required. Follow-up decisions are inventory field scope, allowed data/actions, integration-approval roles, workbook organization/mapping and synchronization policies.

Also confirmed: desktop arrow-key movement in addition to WASD, mobile FPS/third-person movement/look/view switching and separate height controls, third-person orbit around the avatar, policy-controlled additional integrations, updateable tours, partial rescanning where feasible, built-in guidance and full VR 6DoF. See the linked design notes. Ask one primary question at a time and record confirmed answers.

## Early implementation work to scope

After the necessary choices are made:
- Select/pin a long-term Unity version and establish the application project layout; 6.3 LTS is approved for the initial prototype only (D031).
- Continue renderer feasibility. The browser path has first results on one laptop (above); test the weakest required computers, Edge and then phones and Quest.
- Build a small synthetic runtime-editing example with durable record identity.
- Prototype Google Sheets synchronization against synthetic audit-form and rack/RU layouts using the confirmed AI approval gate. Preserve formula/validation/format semantics.
- Prove partial-rescan alignment/replacement using a small changed section.
- Design provider approval enforcement and Gemini capabilities before connecting real data.
- Include novice-friendly guidance with the implemented workflows.
- Prototype a cabinet with aligned closed/open appearance and separate door/interior record anchors.
- Prototype Gemini extraction from synthetic/authorized label frames; evaluate transcription and asset matching before live writes.
- Keep production access enforcement as a separate explicit workstream with acceptance evidence.

These are proposed stages, not a promise that every device has a compatible renderer or that capture/training can run on every viewing device.

## Start prompt for a coding assistant

Read AGENTS.md, this handoff, PRODUCT_SPEC.md and DECISIONS.md before editing. Report the actual repository state and current branch. Preserve confirmed requirements and identify open choices. Use verified MAX effort for Claude build work. Continue the assigned small task, record human/AI contributions and test evidence, and leave a concrete handoff. Do not claim unrun device tests, infer shared credentials or silently redefine confirmed Google requirements, X semantics, AI powers or the renderer.

## Current limitations

- Application license and third-party dependencies are undecided.
- No long-term Unity version, renderer, backend or capture processing location is selected. Unity 6.3 LTS with the URP blank 3D template is approved for the initial prototype only (D031). UnitySplats leads for the browser on one laptop's evidence; it is not a selection.
- Browser rendering is tested with synthetic scenes on one Linux laptop (Chrome/Firefox/Brave) and one personal Windows 11 PC (Edge/Chrome, 30 Hz display-paced baselines). Higher-refresh Windows capacity, macOS, weaker hardware and real captures are untested. The Windows test bundle was checked on Linux and under Wine emulation only.
- The Toughbook FZ-55 browser reference (i5-8365U, 32 GB RAM, UHD Graphics 620) and 30 fps browser / 60 fps VR floors are selected (D033/D034). Exact OS/browser versions and performance remain unverified. A named Android reference, phone fps, memory/image-quality budgets and detailed acceptance criteria remain open.
- Arrow/WASD movement, Q/E/X reset, mobile movement/look/view/height controls, third-person orbit and VR 6DoF are confirmed. Exact touch/controller layout, camera-height reference, orbit/follow rules, comfort, avatar dimensions and scale verification remain open.
- Gemini drafts and designated editors approve before live writes. Field scope, review UI, Google contracts, additional provider scope and integration-administration roles remain open.
- Spreadsheet videos establish visible layouts only. Exact formulas, validation, protection, merged ranges and cell mappings have not been inspected in native workbooks.
- Cabinet states require a registration/segmentation/visibility prototype; local state persistence and setup/inspection permissions still need design.
- Partial rescanning is a required feasibility target, not a tested feature.
- Data types, attachment formats, conflicts, deletion recovery and detailed permissions need decisions.
- No production integration, real workbook modification or scan upload has occurred.

Keep user-facing explanations plain and concise. Arlen prefers a step-by-step interview and practical instructions he can follow without being an experienced developer.
