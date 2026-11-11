# Browser Gaussian-splat rendering prototype

First VR-HE implementation milestone: prove or disprove Gaussian-splat rendering in desktop browsers before committing to a renderer. This folder is an isolated Unity project. It is a measurement prototype, not the VR-HE application.

Status and results: see [TestResults/browser-splat-results.md](TestResults/browser-splat-results.md), the [handoff](../../docs/HANDOFF.md) and the [development log](../../docs/DEVELOPMENT_LOG.md).

The same project also holds the first [interactive browser demo](#interactive-browser-demo-prototype) (branch proto/interactive-browser-demo) in its own scene, source folders and WebGL template. The benchmark below is unchanged and still builds into `Builds/WebGL`.

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

## Interactive browser demo (prototype)

A small work-utility slice built on the tested 250k synthetic room ([task](../../docs/INTERACTIVE_BROWSER_DEMO_TASK.md)): walk around, select a rack, open its record, edit the description and find the saved text again after a reload or browser restart. Everything is synthetic, and the records are labelled LOCAL DEMO DATA. Results, the Windows bundle and the next user test are in the [handoff](../../docs/HANDOFF.md).

| Path | Purpose |
| --- | --- |
| `Assets/InteractiveDemo/Data/demo-site.json` | Synthetic site: frozen site/record/anchor IDs (prefixed UUIDs), ten rack anchors, proxy obstacles and the spawn point. `Tools/check_demo_site.py` checks it against the generated room |
| `Assets/InteractiveDemo/Records/` | Assembly `VRHE.InteractiveDemo.Records`: site validation and authoring settings (`DemoSiteDefinition`), the stored, view and draft shapes (`DemoRecordModel`), `DemoRecordStore` (record format 2: rack notes, equipment, descriptions and names; revision checks; carry-over of format 1; labelled JSON export), `IKeyValueStorage` and `DemoPaths` |
| `Assets/InteractiveDemo/Runtime/` | `DemoApp` (startup, per-frame flow, page bridge), `DemoPlayer` (walking, camera height, first/third person, orbit), `DemoInput` (input gate and sources), selection, outlines and frame pacing |
| `Assets/InteractiveDemo/Plugins/WebGL/DemoBridge.jslib` | Page bridge: messages, mouse frames and localStorage access with error envelopes |
| `Assets/InteractiveDemo/Editor/DemoProjectSetup.cs` | Creates the scene and materials; builds only the demo scene into `Builds/InteractiveDemo` |
| `Assets/InteractiveDemo/Tests/Editor/` | EditMode tests: record identity, persistence, conflicts, damaged or newer data, carry-over of format 1, equipment and RU rules, descriptions, names (D041), failed writes, export and the URL rule |
| `Assets/WebGLTemplates/VRHEInteractiveDemo/` | Page: panels, help, the rack panel (rack note and equipment list), the equipment editor, the Description names panel, input gate, mouse and pointer lock, HUD, local results reporting |
| `Tools/interactive_demo_unity.sh` | `setup`, `test` and `build` with this project's explicit path only |
| `Tools/demo_server.py` | Local demo server at the fixed address `http://127.0.0.1:8791/`; `run` opens Edge, Chrome or Brave with a persistent demo profile; `serve`; `collect` |
| `Tools/verify_interactive_demo.py` | Real-browser checks through the Chrome DevTools Protocol, on the development build or an extracted bundle (`--bundle`). `--part all` (default), `authoring`, or `migration --old-bundle <extracted earlier bundle>` |
| `Tools/package_demo_bundle.py`, `Tools/windows-demo-bundle/` | Windows ZIP, launchers and `START-HERE-DEMO.txt` |

```bash
P=~/Projects/VR-HE/prototypes/browser-splat-rendering
"$P/Tools/interactive_demo_unity.sh" test     # EditMode tests (Unity batch mode, explicit project path)
"$P/Tools/interactive_demo_unity.sh" build    # Builds/InteractiveDemo; never touches Builds/WebGL
python3 -I "$P/Tools/check_demo_site.py"      # proxies against the generated room
python3 -I "$P/Tools/demo_server.py" run --browser chrome --build "$P/Builds/InteractiveDemo" \
  --fixtures "$P/Fixtures/Generated" --results "$P/TestResults/raw/interactive-demo/manual"
python3 -I "$P/Tools/verify_interactive_demo.py" --browser chrome --profile-dir <throwaway folder>
python3 -I "$P/Tools/verify_interactive_demo.py" --browser chrome --profile-dir <new empty folder> \
  --part migration --old-bundle <extracted 294f4b2 bundle folder>   # old build saves, this build carries over
python3 -I "$P/Tools/package_demo_bundle.py"  # needs a clean tree and a build of committed source
```

The Unity script refuses to run while an Editor has this project open, and puts back the one-line URP migration note (`k_AssetPreviousVersion`) that Unity writes into `Assets/Settings/PC_RPAsset.asset` on exit. `demo_server.py run` keeps one demo profile per browser (Linux: `~/.local/share/vrhe-interactive-demo/browser-profiles/<browser>`; Windows: `%LOCALAPPDATA%\VRHE-Interactive-Demo\browser-profiles\<browser>`) so saved records survive a browser restart. It never stops a browser and ends by itself about a minute after the demo page closes; Ctrl+C stops it at once. Saved records belong to that profile and the exact address, which is why the port is fixed.

How the pieces fit:
- The splat is a picture only. Walking uses a CharacterController against proxy BoxColliders, and picking raycasts against anchor boxes; both come from `demo-site.json`, in metres, Unity's left-handed Y-up frame. The generated room spans x -4..4 and z -3..3 with the floor at y = 0.
- Records are keyed by ID: `recordId` for racks, `equipmentId`, `descriptionId` and `labelId` for the authoring data below. Display names, anchor IDs, list positions and splat indexes are never keys. The store is one document under `vrhe.demo.records.v2.<siteId>` in the page's localStorage, in the `vrhe.demo.local-records` schema, version 2. Every change carries the revision it was based on, and a stale revision is refused. Entries for unknown records are kept. Newer-schema data is read-only. Unreadable data is backed up before the first write. The version 1 key is read for the carry-over and never written.
- Input: the page decides whether Unity may act on the keyboard and mouse (the canvas and window have focus, and no panel or text field is active). Unity forgets held keys at every change. The page sends one packed mouse frame per Unity update and owns pointer lock and the context menu.
- Runtime files sit under `data/` in the build (`DemoPaths`). Unity reads a bare `site.json` as a host name and refuses `http://site.json/`.
- Extension points: a site package or tour content would replace `demo-site.json`. A server, spreadsheet or Gemini-draft adapter would implement `IKeyValueStorage` or replace `DemoRecordStore` behind the same record contract. None is implemented.

Prototype defaults (implementation choices, not user decisions; all are fields in `DemoPlayer`, `DemoApp` or the page script):

| Setting | Default |
| --- | --- |
| Walk / Shift speed | 1.3 / 2.6 m/s |
| Arrow keys | As W/S/A/D (D022): Up forward, Down back, Left/Right step sideways; turning is by mouse. The unexposed `arrowKeysTurn` option in `DemoApp` makes Left/Right turn at 90 deg/s instead |
| Mouse look | 0.15 deg per pixel, adjustable 0.25-3x in Help; first-person pitch limit 80 deg |
| Mouse Y inversion | Optional checkbox in Help > Settings, default off, saved with sensitivity in this profile. Vertical drag/captured look and third-person orbit only; horizontal look, picking, wheel and Q/E/X are unchanged. Not in the 294f4b2 ZIP |
| Eye height, Q/E | 1.6 m; Q/E move 0.6 m/s within -0.9 to +1.0 m; X restores 1.6 m and a level view |
| View switch | V; third person starts 2.6 m behind (wheel 1.2-5 m), orbit pitch -30 to 70 deg, the camera pulls in at walls |
| Placeholder figure | Plain, non-gendered, about 1.73 m tall; a rough size cue, not a verified scale reference |
| Canvas | 1280x720 when the window allows, otherwise reduced to fit and labelled; devicePixelRatio 1; no frame cap |

### Equipment, descriptions and names (branch proto/equipment-descriptions)

A local prototype of [the authoring task](../../docs/EQUIPMENT_DESCRIPTIONS_TASK.md) on synthetic data (D037-D039, D041). Results: [Linux results](TestResults/equipment-descriptions-linux-20261111/README.md). Production data model, templates, roles and spreadsheet mapping remain open.

What a person can do:
- Open a rack by selection, right-click, Enter or the L list. The rack panel holds the **rack note** (rack-level text; the single description of the earlier demo) and the rack's **equipment list**, top of the rack first, with an Add equipment form: name, From RU, to RU.
- A new item opens with exactly one empty, unnamed description. **+ Add description** adds another to that item only. Each description has a name list: "(no name)", the active names, **New name...** and **Manage names...**. Up and down buttons change the display order. Remove is offered only for an empty description.
- **Description names** (toolbar button, or Manage names...) adds a name, **Rename** fixes a spelling everywhere, and **Remove...** first requires an existing or new replacement name (D041).
- The L list shows each rack with its items. Open on an item opens it and selects its rack in the view. Equipment has no anchor of its own: the scan is a picture, and an item is a record, not movable geometry.

Data format 2 is one document per site; field names are in `DemoRecordModel.cs`.

| Part | Holds |
| --- | --- |
| `rackNotes[]` | `recordId`, `description` (the rack note), `revision`, `updatedAt`; the shape of format 1 `entries[]` |
| `equipment[]` | `equipmentId` (`eq-<uuid>`), `rackRecordId`, `name`, `ruStart` and `ruEnd` (inclusive), `revision`, times and `descriptions[]` |
| `equipment[].descriptions[]` | `descriptionId` (`dsc-<uuid>`), `labelId` (empty = unnamed), `text`, times. List order is display order only |
| `labels[]` | `labelId` (`lbl-<uuid>`), `name`, `revision`, `retired`, `replacedByLabelId`, `previousNames[]`, `reassignedDescriptionIds[]` |
| `migration` | Carry-over state, the format 1 key, entry counts and times |

Rules, enforced by the store's commands (the page's live hints and disabled buttons only show them):
- Each command reloads the stored document, checks the change, builds the complete next document and writes it with one `localStorage.setItem`. The in-memory copy changes only after that write succeeds. A refused or failed write, such as a full storage area, leaves the stored data and the screen as they were, so a rename or replacement is never half applied in storage.
- RU ranges are whole numbers within 1 to the rack's units, start no higher than end. An overlap with another item in the same rack is saved with a warning (`ruOverlap: warn`) or refused (`block`). Front/rear use is not recorded.
- A description keeps its ID through text, name and order changes. Only an empty description can be removed, and an item keeps at least one. Deleting text is not offered: D041 does not authorize value deletion.
- Adding a name that already exists (same letters, ignoring case and extra spaces) reuses it and changes no equipment. Rename keeps the `labelId`, so every description follows without its text changing. Renaming onto another active name is refused, with advice to use Replace.
- Replace moves every description that uses the old name to the replacement (an existing name, or a new one created in the same write). Each description keeps its ID, item and text. The old name is retired with `replacedByLabelId`, never deleted. No replacement, a blank, unknown or retired one, or the old name itself is refused with nothing written.
- When an item already has a description under the replacement name, both are kept and the result warns (`labelCollision: keep-both`), or the replacement is refused naming the items (`block`). Values are never merged or overwritten.
- An editor opened before a replacement cannot save the retired name; the save is refused as a conflict naming the replacement.

Carry-over of format 1 (the 294f4b2 demo):
- On first load the format 1 rack descriptions appear as rack notes. They are not turned into equipment descriptions. Nothing is written until the first change; that write creates the format 2 document and records the carry-over in `migration`.
- The format 1 copy is never changed or removed, and every export includes it raw (`storedCopies`). If the old build changes its copy later, this build says so and keeps both; the format 2 document stays the source.
- Reset starts over (original rack notes, no equipment, starter names) and does not bring the format 1 notes back. Records for racks this build does not know are kept and exported (`unmatchedStoredEntries`, `unmatchedEquipment`).

Export format 2 (`vrhe.demo.records-export`): `records[]` (racks with their rack note and equipment summary), `equipment[]` (each item with its descriptions and their names and name states), `labels[]` (including retired names and their replacements), `authoring` (the settings below), `migration`, the unmatched lists and `storedCopies`. A format 1 export's `records[].description` is format 2's `records[].description`, the rack note; format 1 had no equipment or names.

Spreadsheet readiness, without an adapter ([spreadsheet rules](../../docs/SPREADSHEET_SYNC.md)): a mapping would join on these IDs, never on display names or row positions. Renaming a name changes only `labels[].name`; it is not a column rename. A replacement reassigns references; it is not a column merge or delete. Removing an empty description is local to one item, not a shared column delete. The export's `mappingNotice` says so.

Proposals, not decisions; the settings are in the `authoring` block of `demo-site.json`, checked by `DemoSiteDefinition`:

| Setting | Prototype default |
| --- | --- |
| Name list scope and storage | One list per site, stored with that site's records in this browser profile; starter names from `demo-site.json` |
| `rackUnitsDefault` | 42 RU (a rack record may set `rackUnits`) |
| `ruNumbering` | `bottom-up`: RU 1 is the bottom position |
| `ruOverlap` | `warn` (alternative `block`) |
| `labelCollision` | `keep-both` (alternative `block`) |
| `maxEquipmentPerRack`, `maxDescriptionsPerItem`, `maxLabels` | 50, 20, 100 |
| `maxEquipmentNameLength`, `maxLabelNameLength` | 80 and 60 characters; rack notes and descriptions up to 4000 |
| Replaced names | Kept, left out of the name lists and shown under "Replaced names" with their replacement |

Not in this slice: templates for new equipment, deleting equipment or descriptions that hold text, cabinet states, production authentication (including [Google Authenticator-compatible MFA](../../docs/PRODUCTION_AUTHENTICATION.md)), Google Drive/Sheets/Gemini, live sync, capture, partial rescanning, touch and VR controls. Physical scale accuracy is not demonstrated.
