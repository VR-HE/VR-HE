# Cabinet inspection states

Status: requested capability and proposed capture/design, November 10, 2026. No runtime implementation exists.

## Requested behavior

Users can set a virtual cabinet door to opened or closed and inspect information on door-mounted panels and inside the cabinet, including breakers, fuses and other equipment.

Arlen suggested two recording sets at the same location. A sensible starting workflow uses closed/open passes of the cabinet area, not two entire-site captures. Clear multi-view coverage may require extra images/passes.

## Proposed capture workflow

1. Associate the capture with the intended room, rack/cabinet and stable record identity.
2. Capture the closed exterior and visible door-mounted panels.
3. Capture the open state, interior equipment and inner door face.
4. Keep unchanged surrounding reference features in both passes for alignment.
5. Reconstruct/register the local appearance states and inspect coverage.

Use the approved site capture workflow and accessible source material. A closed exterior alone does not supply unseen interior detail. Do not present guessed/generated internals as recorded equipment.

Two passes are a starting point, not an accuracy guarantee. Multi-door cabinets and independently operated leaves may need additional views and per-door separation.

## Candidate implementation approaches

| Approach | Behavior | Prototype requirement |
| --- | --- | --- |
| Aligned appearance variants | Show the corresponding closed/open local scan assets | Correct replacement/masking, occlusion, selection and shared coordinates |
| Hybrid cabinet | Move a separate 3D door while rendering captured cabinet/interior appearance | Door isolation/model, hinge, inner/outer surfaces, alignment and artifact control |

Smooth animation is a possible extension; the requested minimum is usable open/closed states with correct information access. The renderer and exact approach are not selected.

Rendering evidence so far: in the November 10 browser test, overlapping splat sections drawn by separate renderers were misordered in every browser, while one merged asset with per-section active ranges rendered and switched correctly. For aligned appearance variants this suggests, but does not prove, merging each cabinet's states into one asset with each state in its own range. See [the handoff](HANDOFF.md).

Unity documents ordinary GameObject animation and door open/close states. Applying that to a reconstructed cabinet still requires a working representation:
[Unity animation overview](https://docs.unity.com/en-us/engine/6000.0/manual/animation-section/animation-mecanim/animation-overview).

## Records and interaction

Keep the cabinet body, each door/face and interior equipment distinguishable. Door-mounted records should follow the correct moving part; fixed breaker/fuse records should remain at their interior locations.

Preserve stable IDs and spreadsheet mappings across state changes. Captures in both states must not duplicate the same equipment inventory.

Open/close is an inspection action. Its per-viewer/shared/persisted behavior, setup permissions and detailed access scope still need decisions. Record editing remains subject to the existing designated-editor policy.

Show discoverable Open door/Close door actions and input equivalents. State-dependent geometry must not leave an old closed door obscuring the interior or keep invisible controls selectable incorrectly.

## Site updates and AI assistance

Partial rescans need to update the affected cabinet states and mappings consistently. Equipment hidden behind a closed door is not evidence that it was removed.

Gemini can be tasked with extracting candidate labels from the appropriate captured surfaces; that does not automatically identify every breaker/fuse or bypass designated-editor approval of AI-generated spreadsheet changes. See [AI capture inventory](AI_CAPTURE_INVENTORY.md).

## Validation and open choices

Prototype one cabinet with clear ground truth. Check alignment, seams, old-geometry ghosting, selection, record anchors, repeated toggles, input accessibility and weak-device performance.

Decide per-door granularity, animation, inspection-state persistence, setup roles and the minimum accepted capture quality. See [test plan](TEST_PLAN.md) and [capture updates](CAPTURE_UPDATES.md).
