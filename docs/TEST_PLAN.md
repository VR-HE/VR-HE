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

Once provider and mappings are selected, verify both spreadsheet-to-app and app-to-spreadsheet:
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

## Evidence format

Each result should name the tested commit, exact device/software configuration, scenario, expected behavior, observed behavior, result and useful logs/screenshots. Label mocked components. Keep private operational data and credentials out of published evidence.
