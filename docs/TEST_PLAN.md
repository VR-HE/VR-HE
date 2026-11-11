# Test and acceptance plan

Status: planned checks, November 10, 2026. Only the rendering-only browser prototype has run (synthetic scenes on one Linux laptop and one personal Windows 11 PC; see [the handoff](HANDOFF.md)). No VR-HE application tests or device builds have run.

## Current foundation

The initial change contains documentation and ignore-rule updates. Validate internal document links, required requirement coverage, consistency of implementation-status labels and preservation of the existing Unity ignore rules. Runtime tests are not applicable to this documentation-only foundation.

## Rendering feasibility

Use a representative small synthetic or appropriately authorized scene. Record exact Unity/package versions, graphics backend, device/OS/browser versions, scene size, load time, frame timing, memory and visible artifacts.

The November 10 [browser prototype](../prototypes/browser-splat-rendering/README.md) recorded these for synthetic scenes on one laptop; results are in the handoff. Personal Windows Edge/Chrome baselines are now reviewed in [the Windows results](../prototypes/browser-splat-rendering/TestResults/windows-personal-20261110/README.md). Still to test: higher-refresh Windows performance, macOS, weaker and integrated GPUs, a representative real or authorized capture, network delivery, long sessions, phones and Quest.

### Confirmed reference PC and frame-rate floors

Arlen confirmed these inputs on November 10 (D033/D034):

| Platform | Confirmed reference / minimum | Evidence still needed |
| --- | --- | --- |
| Desktop browser | Panasonic Toughbook FZ-55: i5-8365U, 32 GB RAM, UHD Graphics 620; 30 fps floor (33.3 ms per frame) | OS/browser versions, active browser GPU/backend, resolution, representative content and actual runs |
| VR headset | Quest 2+ viewing target; 60 fps floor (16.7 ms per application-rendered frame) | Standalone device runs, frame pacing, display refresh, CPU/GPU time and thermal behavior |
| iPhone / Android | Requested device targets remain unchanged; no phone fps floor selected | Named Android reference, device runs and a separate phone performance decision |

Floors are requirements, not results. Preserve the measured RTX 4060 laptop results as historical evidence; do not infer a Toughbook splat budget from them. Report mean frame rate together with frame-time percentiles, stalls and time below the agreed floor during representative movement and record-panel interaction. Mark loading separately rather than hiding it in a run-wide average. Resolution, visual quality, memory/content budgets, test duration and the detailed pass/fail rule remain to be agreed.

### Toughbook hardware evidence — November 10

Arlen supplied four photographs of Windows Task Manager on the reference Toughbook. The typed inventory below records readable fields; the photos themselves are not committed.

| Component | Observed value |
| --- | --- |
| CPU | Intel Core i5-8365U; 4 cores and 8 logical processors |
| RAM | 32.0 GB installed, about 31.8 GB usable; 2400 MT/s; 2 of 2 slots occupied |
| GPU shown | Intel UHD Graphics 620; shared system memory, not a separate 15.9 GB dedicated-VRAM allocation |
| GPU driver | 31.0.101.2141; displayed driver date March 30, 2026 |
| Storage | Samsung MZNLH512HALU-00A00 SATA SSD; 477 GB reported capacity. Free space was not shown |
| OS / browsers | Windows Task Manager is visible; exact Windows edition/build and browser versions remain unverified |

These are inventory observations, not a performance run. The images do not prove WebGL 2 availability, active browser acceleration, thermal behavior or the 30 fps requirement. Background utilization in a screenshot is not a benchmark baseline.

### Headset refresh and proposed operating target

Source check, November 10: [Meta VRC.Quest.Performance.1](https://developers.meta.com/vr/resources/vrc-quest-performance-1/) permits a 60 fps rendering minimum and specifies allowed interactive display rates beginning at 72 Hz. [Meta's display-refresh guidance](https://developers.meta.com/vr/documentation/unity/unity-set-disp-freq/) reserves 60 Hz for media apps and calls for sustaining the requested rate.

Engineering recommendation: start Quest tests at 72 Hz and aim for 72 application-rendered fps (13.9 ms per frame), preserving Arlen's 60 fps floor. This is not a user-selected steady 60 Hz mode or a guarantee of comfort/store acceptance. Log application fps, actual/requested display Hz, CPU/GPU frame times and missed frames separately. Do not count compositor/reprojection-generated frames toward the application-rendered floor; a lower native rate using Application SpaceWarp would require a separate explicit decision.

### Next browser hardware gate

The hardware inventory above is available. [The local packaging task](TOUGHBOOK_BROWSER_TEST_TASK.md) is done: a Windows Edge/Chrome test bundle of the same synthetic benchmark is prepared, as described in the handoff's bundle section. It was initially checked on Linux and under Wine, followed by the reviewed personal Windows 11 Edge/Chrome baselines. Under D035, execution on the company Toughbook is blocked pending company authorization. Arlen has completed those personal Windows Edge/Chrome baselines. The first runs recorded 30 Hz / about 30 fps; two reviewed repeats record 60 Hz / about 60 fps through 250k splats at the same 1280x720 canvas, with 250k CPU work still near 9 ms. Chrome kept its version while Edge updated. This supports the display-pacing explanation; uncapped capacity remains unmeasured. The next proposed implementation step is [the small interactive browser demo](INTERACTIVE_BROWSER_DEMO_TASK.md). These results do not qualify the Toughbook or standalone Quest. Preserve the 30 fps browser floor, record actual hardware/OS/browser facts, and keep the Toughbook result pending. The bundle's name or run prefix may mention Toughbook; classify results by the actual test machine. Retain results for every required browser and mark unavailable browsers untested. Compact-format and sort-refresh experiments remain proposed; smaller files or fewer sorts alone do not prove acceptable memory, motion quality or worst-frame latency.

| Target | Requested capability | Current evidence |
| --- | --- | --- |
| iPhone SE Gen 3 | Capture/view/edit | Not tested |
| Named Android reference device | Capture/view/edit | Device not selected; not tested |
| Quest 3 | Capture/view/edit | Not tested |
| Quest 3S | Capture/view/edit | Not tested |
| Quest 2 | View/edit | Not tested |
| Chrome | Browser view/edit | Rendering only: Chrome 157 on the Linux laptop and Chrome 155.0.8059.82 on the personal Windows 11 PC. Windows 30 Hz / 60 Hz baselines are reviewed; view/edit not implemented |
| Firefox | Browser view/edit | Rendering only: Firefox 159 on the same laptop. View/edit not tested |
| Edge | Browser view/edit | Edge 155.0.4283.45 at 30 Hz and 157.0.4341.42 at 60 Hz rendered the personal Windows 11 baselines. View/edit and company Toughbook qualification remain open |
| Brave | Browser view/edit | Rendering only: Brave 1.99.55 (Chromium 157) on the same laptop. View/edit not tested |

The role/capability for each test user still determines who can edit. The table does not grant editing to all viewers.

## Runtime information editing

- Attach and reopen a description and nested data set at an intended area/equipment location.
- Create equipment using a selected template.
- Add a field to one record; confirm unrelated records are unaffected.
- Save a field into a template for future records; confirm existing records are not silently rewritten.
- Verify supported field types and attachment formats after they are chosen.
- Save/reload and verify identity and placement remain correct.
- Verify ordinary editing requires neither Unity nor recompilation.

Selection geometry, relocation/rescan behavior, undo and concurrent-edit rules need design before their acceptance checks can be finalized.

## Desktop, mobile and VR navigation

- Verify WASD and mouse movement in first person.
- Verify arrow-key movement matches the corresponding WASD directions in each required desktop browser.
- Verify browser Q raises and E lowers the viewpoint.
- Verify X restores both normal camera height and a level viewing angle using the selected height reference.
- Verify VR translation on three axes and rotation on three axes; browser height/reset commands must not overwrite tracked headset pose.
- Verify the selected first-/third-person toggle and default behind-avatar view.
- Verify look/orbit around the avatar in third person, including the selected orbit limits and follow/recenter rules.
- On iPhone/Android, verify movement, look, first-/third-person switching and separate camera-height up/down controls.
- Verify mobile height adjustment changes viewpoint height independently of looking up/down, and orbit input does not accidentally edit an attached record.
- Verify generic non-gender avatar scale after a real-world scale method is established.
- Verify predictable mouse cursor/menu behavior when editing.
- Verify agreed touch and controller equivalents when designed.
- Assess VR comfort separately; a desktop third-person camera is not automatically suitable for a headset.

## Production access and roles

- Reject viewing/editing without required authentication.
- Reject viewing/editing without the required company connection.
- Give an authorized viewer read-only access and reject unauthorized writes server-side where applicable.
- Give a designated editor only the scope of rights assigned.
- Drop the required company connection during viewing, editing and cached-content opening; verify the app locks both viewing and editing.
- Test attachment previews, already open panels and cached tour reopening during the lock.
- Restore the connection and confirm authentication and permissions are still valid before unlocking.
- Test interrupted saves, session expiry and role revocation once their behavior is designed.
- Test deployment configuration so demo exemptions do not become production policy.

Connection-loss detection timing, cache implementation and interrupted-save recovery remain open. A working demo is not evidence that production security passes.

## Spreadsheet sync

For Google Sheets, once mappings and authorization are selected, verify both spreadsheet-to-app and app-to-spreadsheet:
- Value changes with correct units and types.
- Mapped record/field creation.
- Mapped deletion with correct scope.
- Local field removal without destruction of unrelated records.
- Sort/move/insert behavior without identity mismatch.
- Formula and protected-cell behavior.
- Concurrent edits under the chosen policy.
- Retry/idempotency without loops or duplicates.
- Partial failure and recovery without silently losing data.
- Network loss/reconnect and permission loss.
- Clear-value, remove-field and delete-record distinctions.

Use synthetic data first. No real company workbook should be used for a destructive synchronization test.

## Google integration and provider approval

- Exercise the selected Drive file/attachment workflow with authorized demo files.
- Verify the chosen Gemini tasks receive only allowed data and actions.
- Enable an approved AI/spreadsheet adapter and verify its declared capabilities.
- Disable it and verify new requests, writes and background integration activity follow the chosen revocation policy.
- Reject an unapproved provider through the service/API path, not only a hidden UI control.
- Verify viewer/editor and file-access restrictions still apply to AI-originated operations.
- Test additional Excel/OpenOffice paths against their declared compatibility scope; a successful file import is not a sync test.
- Test direct Google sharing/access policies separately from application connector controls.

These are planned acceptance checks. Exact roles, Gemini actions and revocation behavior are still to be designed.

## Site changes and partial rescans

- Capture a baseline test room/section with records attached to known locations.
- Change one rack bay/area and capture that section with unchanged reference overlap.
- Register and replace the changed section; inspect old-equipment ghosting, seams, scale, occlusion and any interaction geometry.
- Verify unaffected scan sections, record IDs, field values and spreadsheet mappings remain intact.
- Verify handling of moved/removed/new equipment according to the selected identity policy.
- Test repeat updates and rejection/recovery of a failed or misaligned update.
- Verify fallback guidance when a broader recapture or reconstruction is required.

No partial-rescan method or quality threshold has been proven. The November 10 browser prototype tested only the drawing order of two synthetic overlapping sections (see the handoff).

## Built-in guidance

Have a non-gamer follow the in-app instructions to scan/import, add information, navigate and retrieve stored information. Record assistance needed and points of confusion.

Verify help can be reopened, shows device-appropriate controls, explains permission/connection states in plain language and does not advertise unimplemented workflows as available.

## Cabinet states

- Capture a test cabinet closed and open with unchanged reference views and clear interior/inner-door coverage.
- Switch visual states; inspect alignment, old-door ghosting, missing surfaces and selection/occlusion.
- Verify door records follow the moving part and interior records remain fixed to the correct equipment.
- Verify repeated toggles preserve asset IDs, annotations and spreadsheet mappings.
- Test input equivalents and selected viewer/editor/state-persistence policy.
- Test partial updates and multi-door cases once their scope is defined.

## Capture-assisted inventory

- Compare extracted label fields with independently checked ground truth on representative captures.
- Record missed fields, incorrect values, incorrect asset matches and duplicates; do not infer accuracy from JSON validity.
- Test blurry/obscured labels, similar devices, open/closed passes and repeat rescans.
- Verify evidence image, timestamp, cabinet/rack context and units stay with each candidate field.
- Distinguish nameplate ratings from timestamped displayed readings and derived audit values.
- Verify AI drafts cannot change live spreadsheets before approval, viewers cannot approve, rejection leaves live cells untouched, and approved writes still respect roles/provider/company-connection checks.
- Verify failed/retried writes do not create duplicate rows or silently replace verified values.
- Measure capture/processing latency, thermal/memory behavior and network needs on the actual targets.

AI approval policy is selected. Field scope, acceptance thresholds, real-time expectations and review UI still need design. No field extraction or device test has run.

## Supplied spreadsheet layout families

- Test approved field writes into synthetic facilities-form equipment slots without replacing formulas, dropdown rules, number/date formats or unrelated values.
- Test VA/kVA, A, V, W and battery-capacity fields as distinct typed quantities using the destination's intended units.
- Test rack/RU block placement, occupied spans, categories and literal blank/no-rack/open-rack labels without inferring undocumented meanings.
- Test multi-RU layout changes against the chosen merge/overlap policy.
- Verify a colour used for equipment category is not treated as a universal status/permission marker.
- Native workbook formulas, protection and exact ranges remain unverified; test them after an authorized native copy is available.

## Claude development launcher

- Validate the launcher's Bash syntax.
- On the user's machine, verify it opens Claude Code from the VR-HE folder.
- Verify the actual model/effort control reports MAX before build work; record version and model.
- If the request is unsupported or capped, record that result instead of claiming MAX.
- Local syntax checks do not establish that a real Claude backend honored the setting.

## Evidence format

Each result should name the tested commit, exact device/software configuration, scenario, expected behavior, observed behavior, result and useful logs/screenshots. Label mocked components. Keep private operational data and credentials out of published evidence.
