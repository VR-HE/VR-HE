# Developer and assistant handoff

Updated November 11, 2026.

## Current state

VR-HE/VR-HE is the selected private repository. ChatGPT/Codex is authenticated as VR-HE with read and write permissions. Initial documentation is prepared on docs/project-foundation; check the pull request for whether it has been merged.

The baseline main commit before this documentation change is d731a368d7121f31d248446f7feac04ddb6e6e06. Consult GitHub history for the current head; a document cannot reliably name its own final commit in advance.

There is no VR-HE application yet. The first implementation milestone, browser Gaussian-splat rendering (D032), has a rendering-only Unity prototype in prototypes/browser-splat-rendering on branch proto/browser-splat-rendering; its results are in the browser milestone section below. The same Unity project now also holds a first interactive browser demo prototype on branch proto/interactive-browser-demo. It is checked in Chrome and Brave on the Linux laptop, and its Windows bundle awaits Arlen's first run (see the interactive demo section below). Branch proto/equipment-descriptions builds the saved mouse Y-inversion option and adds local equipment, RU, description and description-name authoring, carrying over earlier saved rack descriptions as rack notes. It has automated Chrome/Brave checks on Linux and now partial manual Windows evidence from the new ZIP (see the reviewed manual sessions below). Navigation and editing exist only in that demo's local synthetic slice. No capture, backend, sync or security implementation exists, and no phone or Quest test has run. The prepared Windows benchmark completed Edge/Chrome baselines on the personal PC at recorded 30 Hz and 60 Hz modes; the 60 Hz repeat reaches about 60 fps through 250k splats, without establishing uncapped capacity (see the reviewed Windows results below). Arlen's supplied laptop output confirms Git 2.43.0 and successful installation of the gh 2.45.0 Ubuntu package. Arlen supplied a screenshot confirming completed local authorization and account lookup as VR-HE. His subsequent screenshot confirms a successful clone into ~/Projects/VR-HE, docs/project-foundation tracking origin/docs/project-foundation, and no working-tree changes. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration. Claude Code's November 10 local inspection recorded the installed Unity tooling below; the inspection itself created or changed no Unity project.

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
15. [Interactive browser demo task](INTERACTIVE_BROWSER_DEMO_TASK.md) and [its Linux results](../prototypes/browser-splat-rendering/TestResults/interactive-demo-linux-20261111/README.md)
16. [November 11 authoring task](EQUIPMENT_DESCRIPTIONS_TASK.md), [its Linux results](../prototypes/browser-splat-rendering/TestResults/equipment-descriptions-linux-20261111/README.md) and [production authenticator requirement](PRODUCTION_AUTHENTICATION.md)

The earlier ISP_Virtual_Tour_Product_Brief.md informed this baseline. The repository specification is now the maintained project source of truth; do not maintain competing copies.

## November 11 user feedback and next changes

Arlen says the core mechanics work as he hoped. He requests optional mouse Y inversion, multiple equipment records per rack with occupied RU ranges, one unnamed description initially per equipment item, optional further descriptions and an editable reusable dropdown of description names (D036-D039). This message contains no new result archive or explicit host/browser facts; do not claim a completed Windows/performance qualification from it.

Codex added a Help > Settings > Invert mouse Y-axis checkbox in the page source. It defaults off, saves in this browser profile alongside sensitivity and flips only the shared vertical mouse-look delta. It covers drag/captured mouse and the input consumed by first/third person; it does not invert picking coordinates, wheel zoom or Q/E/X. Isolated source checks are recorded in the log. No Unity build or new demo ZIP was produced in this workspace: the delivered 294f4b2 bundle is unchanged. Claude Code later built and checked the option locally; see the authoring section below.

The 294f4b2 demo's data is ten rack records with one description string each, not an equipment/RU editor. The [local authoring task](EQUIPMENT_DESCRIPTIONS_TASK.md) rebuilt and verified the mouse option, then added rack/equipment/RU records and multiple descriptions with migration of saved demo edits; that work is on branch proto/equipment-descriptions (see below). Arlen has now resolved the in-use-name question (D041): removal requires a valid new/updated replacement name and preservation of every affected equipment description. Correct a spelling by renaming, or reassign all old-label references to a replacement name before removing the old choice. No replacement means removal is blocked. Preserve description identities/text through collisions, failed updates and spreadsheet mappings. Catalog scope and exact storage/mapping design remain open; do not reopen the preservation/replacement decision.

Arlen additionally requires Google Authenticator-compatible verification for production alongside VPN and password access (D040). See [production authentication](PRODUCTION_AUTHENTICATION.md). This is a recorded security requirement, not an implemented login backend. The demo remains exempt; connection-loss locking and designated-editor rules are unchanged.

## Next setup work

Local VR-HE sign-in, clone, the Claude session configuration and the local Unity inventory are complete. Arlen approved Unity 6.3 LTS 6000.3.15f1 with the plain URP 3D template for the initial prototype (D031). The prototype branch is **proto/browser-splat-rendering**, created from docs/project-foundation at ff1e070. It holds the prototype and this milestone's documentation updates; docs/project-foundation does not have them. The interactive demo branch, **proto/interactive-browser-demo**, was created from proto/browser-splat-rendering at f993dd6 and holds the demo and its documentation updates. The authoring branch, **proto/equipment-descriptions**, was created from origin/proto/interactive-browser-demo at 6f802b1 and holds the mouse-option checks, the equipment and description authoring prototype and their documentation. He answered Yes to Git credential configuration during login; do not repeat authentication solely to change that answer. Do not assume commands in a cloud workspace ran on his laptop.

Authentication and repository read access are confirmed. Local push access is verified: the inspection commit ff1e070 is on origin/docs/project-foundation. Local commits use the repository-local Git identity VR-HE with the account's GitHub noreply address, as Arlen chose on November 10. Do not paste passwords, tokens or login codes into chat.

If these branches are still unmerged, check out proto/equipment-descriptions, which contains proto/interactive-browser-demo and proto/browser-splat-rendering, when continuing; do not mistake the starter README on main for the full project.

## MAX effort for Claude build work

Arlen explicitly requires MAX effort. The [launcher](../scripts/start-claude.sh) sets a process-scoped effort request and starts Claude in this repository.

For later sessions:
1. Pull the latest working branch with git pull --ff-only.
2. Check claude --version.
3. Run bash scripts/start-claude.sh.
4. Check the active model/effort control, using /model or /effort, before starting build work.
5. Record the observed version, model and actual effort.

The current Claude Code docs support session launch requests and a process environment setting; they do not accept max as a persisted effortLevel value. The client/model can reduce an unsupported request, so a successful launch alone does not prove MAX.

The November 10 screenshot completes the current startup checkpoint: v2.1.321, Opus 5.5, max effort, correct project folder. The inspection session confirmed it locally: the process was started as claude --effort max, with CLAUDE_CODE_EFFORT_LEVEL=max, from the 2.1.321 binary. Claude Code then updated itself on disk to 2.1.322, and Opus 5.5 was selected for that session only. At the next start, select Opus 5.5 again and re-check version and effort. If a session shows a lower level, resolve and record the difference. The November 11 authoring session ran the same way: its own process was the 2.1.321 binary started with --effort max, with CLAUDE_CODE_EFFORT_LEVEL=max, on Opus 5.5. This was rechecked after the session's context was continued.

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
- A second uploaded archive adds two 60 Hz baselines: Edge 157.0.4341.42 and unchanged Chrome 155.0.8059.82 both reach about 60 fps through 250k splats at the same 1280x720 canvas. CPU means at 250k are 9.32 ms and 9.01 ms, respectively. This strongly supports display pacing as the old ceiling. All 108 earlier archive entries except collection metadata are unchanged; the new runs add no page-console errors or >=36 ms intervals, with a 20 ms longest interval in Chrome. The full comparison is in the report.
- Across the four runs, all 44 case records match their summaries, frame arrays reproduce FPS, and corresponding PNG pairs at each refresh rate are byte-identical across browsers. All eight expected overlap outcomes match in each run; the known separate-renderer errors remain.
- There are no page-console errors or measured intervals of 36 ms or longer. Peak allocated WebAssembly capacity is 198.75 MiB. All four harness records report no leftover test processes and deleted temporary profiles.
- The pasted Edge WinError 10054 tracebacks occurred while closing the browser. Complete saved data supports a cleanup-logging issue; fix it narrowly in future tooling without masking failed runs or unrelated errors.
- Chrome process stdout includes background push/updater diagnostics. Unity's browser hardware placeholders differ from native Windows facts; use the latter. The initial pasted Edge console identifies a OneDrive-synced folder; the sanitized archives do not establish every run's folder. Short run duration limits generalization.

The higher-refresh diagnostic repeat is complete. The local task it queued, [the first interactive browser demo](INTERACTIVE_BROWSER_DEMO_TASK.md), is now implemented as a prototype; see the next section. The renderer and Unity version stay provisional; long-term selection and other-platform qualification remain open. No benchmark, bundle or user device was changed during this review.

The company Toughbook stays deferred until company authorization is explicitly confirmed (D035); do not suggest a launcher or transfer workaround. Personal-PC results do not qualify it or standalone Quest. Detailed acceptance criteria and partial-rescan streaming remain open.

## Interactive browser demo — November 11

Claude Code carried out [the interactive demo task](INTERACTIVE_BROWSER_DEMO_TASK.md) on the Linux development laptop, on branch proto/interactive-browser-demo. The demo is a new scene and source folder (Assets/InteractiveDemo) in the existing Unity project, with its own page template and build output (Builds/InteractiveDemo). The benchmark scene, its build in Builds/WebGL, its fixtures and the Toughbook bundle are unchanged. File map, commands, record contract and defaults: [the prototype README](../prototypes/browser-splat-rendering/README.md#interactive-browser-demo-prototype). Check and pacing tables: [the Linux results](../prototypes/browser-splat-rendering/TestResults/interactive-demo-linux-20261111/README.md).

Implemented (prototype; synthetic room and records):
- The 250k synthetic room with a fixed spawn point. Walking and picking use invisible proxy boxes from demo-site.json, never the splat.
- Desktop controls: WASD, and arrows as D022 maps them (Up forward, Down back, Left/Right step sideways). Drag to look, or M for pointer lock; Shift goes faster; Q/E change camera height; X restores the 1.6 m eye height and a level view. V switches to third person behind a plain, non-gendered placeholder figure, with drag orbit and wheel zoom; there X also puts the camera back behind the figure. Keyboard and mouse pause while a panel or text field is active.
- Ten rack anchors with stable record IDs (prefixed UUIDs). Pointing outlines a rack and a click selects it. Right-click, Enter, the Open selected record button or the L equipment list opens its record: name, record ID, anchor ID and an editable description. Save or Ctrl+Enter saves; Esc asks before discarding unsaved text.
- Records are saved in the demo browser profile's localStorage under a versioned prototype schema (vrhe.demo.local-records, version 1), keyed by record ID only. JSON export (a browser download plus a copy in the local server's results folder) and a reset are included. Everything is labelled LOCAL DEMO DATA.
- Plain-language help (H) and a HUD with the actual canvas size and fps; no frame cap. The canvas is 1280x720 when the window allows, otherwise reduced to fit and labelled.
- A local server at the fixed address http://127.0.0.1:8791/ opens Edge, Chrome or Brave with a persistent demo profile and stops by itself after that browser closes.
- Defaults are implementation choices listed in the README, not user decisions. Physical scale accuracy is not demonstrated.

Checks on the development laptop (Linux; not Windows evidence):
- 23 of 23 EditMode tests (record identity, persistence, revision conflicts, damaged or newer data, export and the URL rule). The site check matches the proxies to the generated room.
- Automated real-browser checks with trusted DevTools keyboard and mouse input, on the final ZIP extracted and served by its own server:
  - Google Chrome 157.0.8103.50: 69 of 69 checks.
  - Brave 1.99.55 (Chromium 157): 67 of 69. Brave's interface leaves less room in the same 1400x960 window, so the page reduced the canvas to 1220x686 and labelled it, as designed; only the two checks that expect 1280x720 failed.
  - They cover movement and collision, Q/E/X in both views, orbit and zoom, selecting two different racks, typing without movement, separate saved text per record, reload, browser relaunch with the same profile, export and reset.
- Frame pacing during standing, walking, height change, drag look, orbit, third-person walking, typing and the open help panel: 59.5-60.0 fps in every activity in both browsers on the 60 Hz display, with no interval over 50 ms. The longest intervals were 34 ms in Chrome and 42 ms in Brave, both while typing. Main-thread CPU averaged 8.0-9.7 ms per frame, mostly the splat sort. The browser paces frames to the display, so these are not uncapped capacity.
- Wine 9.0 emulation with the bundled Windows Python: 18 of 18 checks, from a folder named with spaces, parentheses and &. The Edge launcher used the portable Python and reported the missing Edge plainly. DEMO-SERVER-ONLY.cmd served this exact build on 127.0.0.1:8791 to Linux Chrome, which loaded it at 1280x720, walked and saved an export copy in results. The collector wrote one results ZIP with the account name removed. Wine is emulation, not Windows.
- A scan of every bundled file found no home path, account name or e-mail address. The 16 compiled-in Editor paths in the wasm are masked as in the Toughbook bundle.

Problems found and fixed before the final build:
- Unity's web request read the relative file name site.json as the host http://site.json/ and refused it, so the first build stalled while loading. Runtime files now sit under data/, an EditMode test pins the rule, and an unexpected startup error now shows a message instead of a stall.
- Hidden loading and error overlays still covered and blocked the view, because a CSS display rule overrode the hidden attribute. Fixed; the checks confirm nothing covers the view.
- The status line shrank Chrome's canvas below 1280x720; it moved into the top bar.
- The help text said nothing goes to a server; it now says the local test server keeps export copies in its results folder.
- The first ZIP turned the view with Left/Right arrows, against D022's mapping. Fixed in e16aaa0; that ZIP was deleted before delivery.
- Unity rewrites one URP bookkeeping line in Assets/Settings/PC_RPAsset.asset on every exit; the demo's Unity script restores exactly that line.

The ZIP (ignored by Git, on the development laptop):
- Path: ~/Projects/VR-HE/prototypes/browser-splat-rendering/Bundles/VRHE-Interactive-Demo-20261111-294f4b2.zip
- Size: 33,056,190 bytes (31.5 MiB); 64 files and 102,698,620 bytes (97.9 MiB) unpacked
- SHA-256: 8dcebd10b6af8f8089028898da6c91d9e0abf366ca655ee9fd24ee7889af6486 (also in the .sha256 file beside it)
- Built by Tools/package_demo_bundle.py from commit 294f4b2 on a clean tree, build label interactive-demo-294f4b21e6b1-20261111T061111Z. Rebuilding gives a new label and ZIP hash.
- Contents: the demo build (wasm paths masked), the regenerated 250k fixture (byte-identical to the development fixture), the demo server, Edge and Chrome launchers, a server-only fallback, a results collector, START-HERE-DEMO.txt and the same pinned portable Python 3.14.10.
- Needs: Windows 10 or 11, Edge and/or Chrome, no administrator rights and nothing installed. The ZIP and its extracted folder take about 136 MB; on Linux each demo browser profile grew to 10-66 MB. Windows profile sizes are unmeasured.

Arlen's next test, on the personal Windows 11 PC (not the company Toughbook, D035):
1. Copy the ZIP to Downloads on the personal PC by an ordinary permitted method, such as USB. Leave Windows protections on.
2. Right-click it, choose Extract All, and open START-HERE-DEMO.txt in the extracted folder.
3. Double-click RUN-DEMO-EDGE.cmd and follow its 12-step test script (about 15 minutes). Optionally repeat in Chrome with RUN-DEMO-CHROME.cmd.
4. Close the demo windows, double-click COLLECT-DEMO-RESULTS.cmd and bring back the VRHE-demo-results-<date>-<time>.zip it shows. Add short notes on fps, stutter, confusing controls or wording, and whether saved text returned after reload and relaunch.

To stop the demo, close its browser window; the black server window stops by itself about a minute later, or at once with Ctrl+C. If Windows or security software blocks a file, stop and report the message; do not work around it.

Still untested:
- Everything on Windows: cmd and Explorer, Edge and Chrome with the demo profile, SmartScreen and downloaded-file marks, the firewall prompt, and saving, relaunch and export there.
- Edge (not installed on the laptop), Firefox, macOS, touch, controllers and VR.
- Human use: pointer-lock feel (the automated check used synthetic events), whether help and controls are clear to non-gamers, non-US keyboard layouts, and Windows display scaling or high-DPI screens (the canvas renders at device-pixel-ratio 1).
- Two tabs editing the same record (the store's revision check is unit-tested only), long sessions, many records, storage limits, network delivery, weaker hardware including the Toughbook (deferred, D035), real captures and physical scale.

After Arlen's run: review the collected ZIP, then settle which record fields, templates and storage adapter come next before extending the demo.

## Equipment and description authoring — November 11

Claude Code carried out [the authoring task](EQUIPMENT_DESCRIPTIONS_TASK.md) on the Linux development laptop, on branch proto/equipment-descriptions. That branch starts from origin/proto/interactive-browser-demo at 6f802b1. Data model, rules, defaults and file map: [the prototype README](../prototypes/browser-splat-rendering/README.md#equipment-descriptions-and-names-branch-protoequipment-descriptions). Check and pacing tables: [the Linux results](../prototypes/browser-splat-rendering/TestResults/equipment-descriptions-linux-20261111/README.md). The benchmark build, the Toughbook ZIP and the 294f4b2 demo ZIP are unchanged.

Implemented (prototype; synthetic room and records, labelled LOCAL DEMO DATA):
- Stage 1: the saved Help > Settings > Invert mouse Y-axis option from Codex's source, now built. It reverses only vertical drag and captured-mouse look and third-person orbit.
- A rack holds several equipment items, each with its own ID and an inclusive RU range; a 2U item is one record. RU bounds are enforced. An overlap with another item in the same rack is saved with a warning, or refused if the setting says block. RU 1 is the bottom of a 42 RU demo rack. Front/rear use and physical position are not recorded; the scan stays a picture.
- A new item starts with exactly one empty, unnamed description. + Add description adds another to that item only. Each description has its own ID, separate from its text, order and name. Only an empty description can be removed.
- Description names come from one reusable list per site, a prototype proposal. Add, Rename and Remove are available; Remove requires a replacement name (D041). The store itself enforces the rules: rename keeps the name's ID, replacement keeps every description's ID, item and text, a clash keeps both descriptions by default, and replaced names are retired, never deleted.
- Record format 2. Rack descriptions saved by the 294f4b2 demo carry over as rack notes, not equipment descriptions. The earlier copy is never changed and is included raw in every export. Export format 2 lists equipment, descriptions, names and retired names, with a notice that no spreadsheet mapping exists.
- The equipment list shows racks with their items. Help has new plain-language sections for racks, equipment, descriptions, names, saving and the carry-over.
- Defaults are prototype proposals, configurable in demo-site.json and listed in the README. No production login/MFA, Google or company connection was added; the demo's access exemptions are unchanged.

Checks on the development laptop (Linux; not Windows evidence):
- 47 of 47 EditMode tests: identity, persistence, conflicts, carry-over, RU rules, descriptions, names, clashes and failed writes.
- Real-browser checks on the final ZIP, extracted and served by its own server, with trusted DevTools keyboard and mouse input in throwaway profiles:
  - Google Chrome 157.0.8103.50: 124 of 124.
  - Brave 1.99.55: 122 of 124. As before, Brave's interface leaves less room in the same window, so the canvas is reduced to 1220x686 and labelled; only the two checks that expect 1280x720 fail.
  - Carry-over, with the 294f4b2 bundle writing a real profile first: 9 of 9 in Chrome and 9 of 9 in Brave.
  - They cover both stages of the task: inversion in first and third person (drag and captured mouse) with reload and restart; unchanged horizontal look, picking, wheel and Q/E/X; no movement while a panel is open. On the authoring side: two devices in one rack including a 2U item; one name with different text on two items; an unnamed description beside named ones; record-local saves; rename, refused removal and replacement across items with clashes; a full-storage failure that changes nothing; reload, restart, export and reset.
- Frame pacing while typing in the equipment editor and in the names panel, and with the names panel open: 59.4-60.0 fps in Chrome and Brave on the 60 Hz display, with no frame interval over 50 ms in any activity; the longest in the new panels was 42 ms (Chrome, typing in the equipment editor). The earlier activities stayed at 59-60 fps. The browser paces frames to the 60 Hz display, so these are not uncapped capacity.
- Wine 9.0 emulation with the bundled Windows Python: 18 of 18 checks from a folder named with spaces, parentheses and &. They cover the Edge launcher's portable-Python start and missing-Edge message, and the server-only launcher serving this build to Linux Chrome after checking 54 files against the bundle's checksums: 1280x720, walking and an export copy. The collector wrote one scrubbed results ZIP. Wine is emulation, not Windows.
- The packager's privacy scan and an independent byte scan of every bundled file found no developer home path, account name or e-mail address. The byte scan's only matches were the engine's generic /home/web_user folder and "arLen" inside .NET identifiers such as charLength. 16 compiled-in Editor paths in the wasm are masked.

Problems found and fixed before the final build:
- A screenshot review found description text typed into the wrong box. A newly focused description could sit hidden under the new sticky Save row; the scripted click then landed on the footer, a typed L reached the List shortcut, and the unsaved-changes question appeared. Nothing was lost, but the page now scrolls focused cards clear of the footer, keeps the caret in place through Ctrl+Enter and returns Keep editing to the field in use. The verifier now refuses to click a covered control.
- The data panel's State line was stale after saves, the rack note counter reported unsaved changes when only the Add equipment name was typed, the editor's Save row could scroll out of view, and some counts read "1 description get". All are fixed.

The ZIP (ignored by Git, on the development laptop):
- Path: ~/Projects/VR-HE/prototypes/browser-splat-rendering/Bundles/VRHE-Interactive-Demo-20261111-4f4f9ac.zip
- Size: 33,134,200 bytes (31.6 MiB); 64 files and 102,857,310 bytes (98.1 MiB) unpacked
- SHA-256: 0be32045b60cfd477f25d95d637f24cb6637c19fadc4b5c62af6698bb08e1b32 (also in the .sha256 file beside it)
- Built by Tools/package_demo_bundle.py from commit 4f4f9ac on a clean tree, build label interactive-demo-4f4f9ac2fd78-20261111T144938Z. Bundle version 2.
- Contents as in the 294f4b2 ZIP, with this build and the updated START-HERE-DEMO.txt. It needs Windows 10 or 11, Edge and/or Chrome, no administrator rights and nothing installed.

Arlen's next test, on the personal Windows 11 PC (not the company Toughbook, D035):
1. Copy the ZIP to Downloads by an ordinary permitted method, such as USB. Leave Windows protections on. Extract All, then open START-HERE-DEMO.txt.
2. Double-click RUN-DEMO-EDGE.cmd and follow its 17-step test script (about 25 minutes). It uses the same Edge demo profile as the 294f4b2 demo, so step 6 checks that earlier saved rack descriptions appear as rack notes.
3. Optionally repeat steps 1-13 in Chrome with RUN-DEMO-CHROME.cmd.
4. Close the demo windows, double-click COLLECT-DEMO-RESULTS.cmd and bring back the results ZIP it shows, with short notes on fps, stutter, confusing wording and whether everything came back after reload and relaunch.

Still untested:
- Complete Windows workflow assertions, including carry-over of the actual 294f4b2 saved text; only partial Windows telemetry is reviewed below. Firefox, macOS, touch, controllers and VR remain untested.
- Native drop-down pop-ups: the checks set the name lists by script because the DevTools protocol cannot drive the pop-up. Every other click and key was a real input event.
- Captured-mouse feel: pointer-lock motion was synthetic. Human clarity of the help and the RU wording, screen readers, non-US keyboard layouts and display scaling are also untested.
- A crash or power loss in the middle of a save. The design argument is that each change is one complete-document write to one localStorage key, so storage holds either the old or the new document, but no interrupted write was physically tested. A refused write (full storage) was tested.
- Two tabs editing at once in a real browser (revision checks are unit-tested only); very many items or names, and realistic data volumes near the browser's storage limit; the Toughbook (D035); real captures and physical scale.

Windows telemetry has now been reviewed in the next section. Arlen says the overall direction is right and more modifications are needed; ask for his first specific change before choosing new implementation work. Full Windows workflow confirmation and the open authoring choices remain: catalog scope, RU numbering/capacity, front/rear use, overlap/clash policies, deleting items or text-bearing descriptions, and templates.

## Reviewed manual Windows authoring sessions — November 11

Arlen uploaded VRHE-demo-results-20261111-105736.zip and said he is pleased with the direction: more modification is needed, but the overall idea is right. This is positive usability feedback, not acceptance of every prototype default or a completed workflow checklist.

[The reviewed report](../prototypes/browser-splat-rendering/TestResults/windows-manual-20261111/README.md) and its compact JSON record archive SHA-256 `6ec401464aabb63b186b296faa61b8909b10ae29c218c024e02ec25074d48d46`, both sessions and limitations. All archive CRCs pass; seven JSON documents and two console streams parse, and all 17 reported pacing buckets are arithmetically consistent.

- Both Windows clients report the 250k synthetic room at a 1280x720 canvas on an RTX 5070 Ti / ANGLE / D3D11 / WebGL 2. Focused categories average about 60 fps, with longest intervals 25 ms and 23 ms and no >50 ms focused interval.
- Each session has a 55/56 ms unfocused interval; loading maxima are 319/327 ms. Do not describe the entire session as stall-free. Only aggregate buckets, not raw frame arrays, are available.
- The first session has a reduced Chrome/157 user agent without exact product/native-launcher facts. The second matches Edge 157.0.4341.42 on Windows 11 Home 26H2 build 26300.9974; native display mode is 1920x1080 @ 60 Hz.
- Counters record three equipment additions total, two equipment saves in Edge and one rack-note save in the first session. No page-console errors, save conflicts or storage errors are recorded.
- No record export or browser profile is included, and both snapshots report zero name-add/rename/replace and export events. Exact text isolation, migration/reload/restart, D041 preservation and mouse-inversion behavior remain unverified by this upload. Prior Linux tests are separate evidence.
- The Edge launcher reports ready, persistent profile kept, window closed and browser exited. First-session launcher metadata is absent.

No application code, ZIP or saved record was changed by this review. Preserve the working core and ask Arlen which specific modification he wants first; do not turn general encouragement into an unrequested feature decision.

## Next mapping work

AI write policy is resolved: Gemini creates drafts; designated editors approve AI-generated entries and updates before live spreadsheet writes. The supplied videos establish facilities-audit and rack/RU mapping targets. Use synthetic examples for the demo and inspect an authorized native workbook/copy before binding real cells. X is resolved: restore both normal camera height and level viewing angle. Q raises and E lowers the viewpoint.

Google Drive, Google Sheets and Gemini compatibility is now required. Do not reopen whether Google Sheets is required. Follow-up decisions are inventory field scope, allowed data/actions, integration-approval roles, workbook organization/mapping and synchronization policies.

Also confirmed: desktop arrow-key movement in addition to WASD, mobile FPS/third-person movement/look/view switching and separate height controls, third-person orbit around the avatar, policy-controlled additional integrations, updateable tours, partial rescanning where feasible, built-in guidance and full VR 6DoF. See the linked design notes. Ask one primary question at a time and record confirmed answers.

## Early implementation work to scope

After the necessary choices are made:
- Select/pin a long-term Unity version and establish the application project layout; 6.3 LTS is approved for the initial prototype only (D031).
- Continue renderer feasibility. The browser path has first results on one laptop (above); test the weakest required computers, Edge and then phones and Quest.
- Extend the interactive demo's synthetic runtime-editing example (durable record IDs, browser-local storage only) toward templates and placement checks. Equipment, RU ranges, descriptions and names exist on proto/equipment-descriptions.
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
- Browser rendering is tested with synthetic scenes on one Linux laptop (Chrome/Firefox/Brave) and one personal Windows 11 PC (Edge/Chrome, reviewed 30 Hz and 60 Hz baselines through 250k at a 1280x720 canvas). Capacity beyond the measured refresh-limited cases, macOS, weaker hardware and real captures remain untested. The bundle now has the recorded personal Windows runs in addition to the earlier Linux/Wine checks. The interactive authoring prototype has automated Linux Chrome/Brave checks and reviewed manual Windows telemetry. The Windows upload records rendering, navigation and some authoring, but not full checklist assertions, record exports or name replacement. Wine launcher checks remain emulation.
- The Toughbook FZ-55 browser reference (i5-8365U, 32 GB RAM, UHD Graphics 620) and 30 fps browser / 60 fps VR floors are selected (D033/D034). Exact OS/browser versions and performance remain unverified. A named Android reference, phone fps, memory/image-quality budgets and detailed acceptance criteria remain open.
- Arrow/WASD movement, Q/E/X reset, mobile movement/look/view/height controls, third-person orbit and VR 6DoF are confirmed. Exact touch/controller layout, camera-height reference, orbit/follow rules, comfort, avatar dimensions and scale verification remain open. The demo prototype implements the desktop keyboard and mouse controls with provisional defaults listed in its README.
- Gemini drafts and designated editors approve before live writes. Field scope, review UI, Google contracts, additional provider scope and integration-administration roles remain open.
- Spreadsheet videos establish visible layouts only. Exact formulas, validation, protection, merged ranges and cell mappings have not been inspected in native workbooks.
- Cabinet states require a registration/segmentation/visibility prototype; local state persistence and setup/inspection permissions still need design.
- Partial rescanning is a required feasibility target, not a tested feature.
- Data types, attachment formats, conflicts, deletion recovery and detailed permissions need decisions. The demo's browser-local record store is a provisional prototype, not the backend or a spreadsheet adapter; its name-list scope, RU numbering, overlap and clash policies are prototype proposals.
- No production integration, real workbook modification or scan upload has occurred.

Keep user-facing explanations plain and concise. Arlen prefers a step-by-step interview and practical instructions he can follow without being an experienced developer.
