# Local task: interactive browser demo

Status: implemented as a prototype on branch proto/interactive-browser-demo, November 11, 2026. Checked in Chrome and Brave on the Linux development laptop; the Windows demo bundle is untested until Arlen runs it. Results, the bundle and the next user test are in [the handoff](HANDOFF.md#interactive-browser-demo--november-11). This is not a final production engine/renderer decision.

## Goal and scope

Turn the tested synthetic room into a small work-utility prototype: move around, inspect a rack, edit its description and reopen the saved record. Follow [AGENTS.md](../AGENTS.md), [the specification](PRODUCT_SPEC.md), [decisions](DECISIONS.md), [the handoff](HANDOFF.md) and [the reviewed browser results](../prototypes/browser-splat-rendering/TestResults/windows-personal-20261110/README.md).

Continue on the Linux development laptop with verified Opus 5.5 / MAX effort. Check branch, tree, remote and disk headroom before work. Start a separate prototype branch from the current proto/browser-splat-rendering head; preserve local changes. Reuse the installed Unity 6.3 LTS / URP project and pinned UnitySplats candidate provisionally. Prefer an isolated new scene and source folder in the existing project over duplicating its Library on the nearly full disk. Keep the original benchmark, fixtures and build entry point available for comparisons.

No new editor, production integration or operational capture is needed. Every Editor operation must name the explicit VR-HE project path; keep The Veil and its bridge untouched.

## Behavior to implement

1. Load the existing small synthetic room, initially at the measured 250k scale, with a stable spawn point and simple proxy floor/wall geometry. The splat itself is not collision or selection geometry.
2. Support WASD and arrows plus mouse look. Q raises and E lowers the camera; X restores both the configured normal camera height and level viewing angle. Input must pause appropriately while editing text or using menus.
3. Add first-/third-person switching, a generic non-gender placeholder avatar for scale, behind-avatar follow and look/orbit around the avatar. Choose configurable prototype defaults for the toggle key, height and orbit behavior; document them as implementation choices rather than new user decisions. Physical scale accuracy is not yet demonstrated.
4. Place at least two selectable synthetic racks/equipment items using aligned proxy colliders/anchors. Right-clicking the selected item opens a clear record panel; provide an obvious inspection button/help route for non-gamers.
5. Show a name, stable identifier and editable description. Save at runtime and reopen the same record. Editing one item must leave the other unchanged; keep the record and identifier separate from splat array indexes or display names.
6. Persist demo records across a normal browser/page restart and provide simple JSON export for inspection/backup. A small versioned local schema/store is a provisional prototype implementation, not the final backend or two-way spreadsheet adapter. Clearly label the data as local demo data.
7. Include plain-language help for focus/mouse capture, movement, camera height/reset, view switching, selection, saving and reopening. Display actual canvas resolution and an unobtrusive FPS indicator without imposing the browser's 30 fps floor as a rendering cap.

## Packaging and verification

Build a separate interactive WebGL output and launch path; do not overwrite the benchmark package. Keep persistence testable: the benchmark's fresh disposable profiles are unsuitable for checking data across relaunches. Use an explicit persistent demo profile or a documented normal-profile flow and stable local origin, without changing or deleting unrelated user profiles. Explain how to stop the local demo server.

Verify on available real Linux browsers: controls, pointer/menu transitions, editable text without movement, selection of both items, stable IDs, save/reload/relaunch and export. Check view orbit and X reset. Add focused tests for durable record identity/persistence where useful; actual browser verification is still required. Report measured frame pacing during movement and panel use, not only an idle average.

Prepare a transferable Windows demo bundle with prerequisite handling and clear launch/results instructions. Label Windows interaction behavior untested until Arlen runs this new build; the earlier benchmark runs do not validate it.

Commit source/scripts/documentation and retain useful developer comments about intent, coordinates, record contracts, input adapters and extension points. Keep builds, generated fixtures, profiles and raw results ignored. Update the handoff and development log with observed behavior, limitations, exact build path and the next user test.

## Boundaries

Production authentication/VPN enforcement, Google Drive/Sheets/Gemini, live sync, capture/training, cabinet state registration, partial rescanning and phone/Quest interaction are not part of this small slice. Preserve their requirements and clear extension points; do not claim them implemented. Company Toughbook execution remains deferred under D035. Do not contact anyone or connect real company data.
