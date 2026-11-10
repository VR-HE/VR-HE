# Test and acceptance plan

Status: planned checks, November 10, 2026. No application tests or device builds have run.

## Current foundation

The initial change contains documentation and ignore-rule updates. Validate internal document links, required requirement coverage, consistency of implementation-status labels and preservation of the existing Unity ignore rules. Runtime tests are not applicable to this documentation-only foundation.

## Rendering feasibility

Use a representative small synthetic or appropriately authorized scene. Record exact Unity/package versions, graphics backend, device/OS/browser versions, scene size, load time, frame timing, memory and visible artifacts.

Set acceptance thresholds with Arlen. Do not invent an FPS, memory, scale or image-quality target and present it as agreed.

| Target | Requested capability | Current evidence |
| --- | --- | --- |
| iPhone SE Gen 3 | Capture/view/edit | Not tested |
| Named Android reference device | Capture/view/edit | Device not selected; not tested |
| Quest 3 | Capture/view/edit | Not tested |
| Quest 3S | Capture/view/edit | Not tested |
| Quest 2 | View/edit | Not tested |
| Chrome | Browser view/edit | Not tested |
| Firefox | Browser view/edit | Not tested |
| Edge | Browser view/edit | Not tested |
| Brave | Browser view/edit | Not tested |

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
- Verify browser Q raises and E lowers the viewpoint.
- After clarification, verify X restores exactly the agreed camera state at the agreed location.
- Verify VR translation on three axes and rotation on three axes; browser height/reset commands must not overwrite tracked headset pose.
- Verify the selected first-/third-person toggle and behind-avatar view.
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

No partial-rescan method or quality threshold has been proven.

## Built-in guidance

Have a non-gamer follow the in-app instructions to scan/import, add information, navigate and retrieve stored information. Record assistance needed and points of confusion.

Verify help can be reopened, shows device-appropriate controls, explains permission/connection states in plain language and does not advertise unimplemented workflows as available.

## Evidence format

Each result should name the tested commit, exact device/software configuration, scenario, expected behavior, observed behavior, result and useful logs/screenshots. Label mocked components. Keep private operational data and credentials out of published evidence.
