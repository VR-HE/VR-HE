# Site changes and partial scan updates

Status: required update workflow and feasibility target, November 10, 2026. No capture/reconstruction/update pipeline has been selected or tested.

## Confirmed request

Keep the virtual hubsite/headend current as physical equipment and rooms change. Where feasible, rescan only changed portions instead of repeating a whole-site scan.

Partial rescanning is a target to prove, not a guarantee that every change or device supports a tiny isolated recapture. A changed region normally needs sufficient unchanged reference information to line up with the existing site.

## Proposed approach

Store the site as replaceable sections, such as rooms or rack bays, in a shared coordinate frame. Exact partitioning is undecided.

Keep scan assets separate from equipment/place identity, descriptions, fields, attachments and spreadsheet mappings.

Candidate workflow:
1. Select the area that changed.
2. Follow capture guidance for the change plus unchanged reference overlap.
3. Reconstruct and align the replacement section to the existing site.
4. Compare alignment, scale, visual seams and coverage.
5. Replace/retire the old visual section; update supporting interaction/collision data as needed.
6. Preserve unaffected asset records and explicitly reconcile moved, removed or new equipment.
7. Publish a consistent site version; provide recovery if the update fails.

Preview, publishing rights, rollback/history retention and quality thresholds still need decisions. These steps are proposed design, not an implemented user flow.

## Why appending another scan is insufficient

Appending new splats may leave old equipment visible, create double surfaces or misalign rack positions. The update must define which old appearance is retired and where the new section belongs.

Physical replacement of a device does not prove it has the old device's identity. Keep unaffected record IDs stable, and use deliberate remapping or new records for changed assets under the chosen inventory policy.

Text/nameplate readability, attachments and live equipment values remain separate data concerns. A new splat does not automatically update a model number or spreadsheet row.

## Evidence and limits

[SplaTAM](https://spla-tam.github.io/) demonstrates online tracking/mapping and expansion of a Gaussian representation from RGB-D observations. This supports incremental mapping as a research direction.

It does not demonstrate VR-HE's desired maintenance workflow, exact phone/Quest capture support, section replacement after later site changes, or preservation of business records. Those are separate engineering tasks. SplaTAM is a research reference, not a selected dependency or device-compatibility claim.

Inferring a section-based update architecture is a design proposal based on these building blocks. It must be validated with the eventual renderer, reconstruction system and capture devices.

Browser rendering evidence so far (November 10; synthetic sections; UnitySplats over WebGL 2): two overlapping sections drew in the correct depth order only when merged into one asset and renderer. As separate renderers they were ordered as whole objects, and the wrong section showed in the overlap. Showing and hiding sections through the merged asset's active ranges worked without reloading. This tested drawing order only, not registration, capture or seam quality. See [the handoff](HANDOFF.md).

## Cabinet appearance states and inventory

Cabinet closed/open passes need common coordinates and enough reference views. Update the changed cabinet states together with their local capture/record mappings; unrelated rooms do not inherently need recapture.

Door-mounted labels/records and fixed interior records must remain attached to their correct parts. A closed-state pass cannot establish that hidden interior equipment was removed.

See [cabinet states](CABINET_STATES.md) and [capture-assisted inventory](AI_CAPTURE_INVENTORY.md) for state coverage and duplicate/identity handling.

## Prototype to run

Use a small synthetic/authorized scene. Change one rack bay, capture it with overlap, then attempt replacement while retaining surrounding scan data and attached records.

Inspect:
- Registration and scale stability.
- Old-equipment ghosting and seam quality.
- Repetitive racks, reflective doors, limited viewpoints and changed lighting.
- Supporting selection/collision geometry.
- Durable equipment IDs, annotation positions and spreadsheet mappings.
- Repeat updates, failed updates and recovery.
- Work/load time and memory on the weakest viewing targets.

Define acceptable error/quality and rescan scope with Arlen. If reliable registration or clean replacement fails, explain the need for wider reference capture or broader reconstruction. Reduced capture effort does not necessarily mean all processing can remain local to one section.

See [test plan](TEST_PLAN.md) and [built-in guidance](USER_GUIDE_PLAN.md). No complete headend rescan has been ruled out for cases where the selected method cannot safely align a partial update.
