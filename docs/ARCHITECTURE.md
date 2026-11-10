# Proposed architecture

Status: design notes, November 10, 2026. These are proposed boundaries, not implemented modules or approved technology selections.

## System responsibilities

| Area | Responsibility | Open choice |
| --- | --- | --- |
| Capture/import | Acquire imagery and associated pose/calibration information, or import an existing capture | Integrated capture scope and APIs |
| Reconstruction | Produce splats and any supporting geometry | Device, workstation or approved private server |
| Site updates | Replace changed sections in a versioned tour | Partitioning, registration and old-geometry retirement |
| Tour viewing | Load visual assets, navigation and view modes | Renderer, streaming, budgets and browser path |
| Asset data | Store places, equipment, fields, templates and attachments | Schema, persistence and backend |
| Interaction/editing | Select an area or object and edit its linked information at runtime | Proxy geometry, anchors and input equivalents |
| Spreadsheet sync | Google Sheets two-way values/structural changes and additional approved adapters | Mapping, latency, conflicts and additional adapter scope |
| Provider access | Google Drive/Gemini integration and approved AI/spreadsheet connections | Gemini functions, API paths, company approval roles and scopes |
| In-app guidance | Teach capture, editing, navigation and data retrieval | Guided walkthrough and contextual help design |
| Access/session policy | Enforce production network, password and role requirements | Hosting, identity provider and connectivity detection |

The captured appearance and durable equipment records should be independent. A rescan should not inherently replace equipment identity or delete annotations. The actual rescan-registration strategy is still open.

## Candidate data contracts

The following concepts need a documented schema before implementation:

- Site and spatial area identifiers.
- Rack identity, RU position/range and equipment identity.
- Attachment/child-data-set identity and its relationship to its parent.
- Equipment-type template and per-record field definitions/values.
- Tour/scan version, coordinate frame, scale and annotation placement.
- Revision information for conflict detection and recovery.
- Spreadsheet mapping identities independent of row order and cell address.

Names and row positions should not be the sole identity. Moving a row, renaming equipment or changing a scan should not silently link data to a different item.

Equipment spanning RUs, front/rear views, cross-links and moved equipment remain design questions.

## Runtime editing

One logical edit action should work across supported inputs. Desktop begins with right-click; touch and VR equivalents remain to be chosen.

Editing descriptions, fields, nested information and equipment records should not require Unity or recompilation. Input adapters should feed shared editing commands rather than duplicating business rules on each platform.

A splat is a visual representation. Do not assume it supplies clean selectable object boundaries, accurate collision geometry, readable nameplates or measurement accuracy. Test suitable interaction geometry and annotation-placement methods.

## Updates, integrations and input boundaries

See [capture updates](CAPTURE_UPDATES.md) for proposed replaceable tour sections, overlap-based registration and handling of removed equipment. Preserve durable IDs for unaffected records; do not automatically equate a newly visible device with an existing inventory record.

See [integrations](INTEGRATIONS.md) for required Google compatibility and policy-controlled provider adapters. Enforcement belongs at app/service data boundaries as well as the user interface. Direct Workspace access also needs matching Google authorization/sharing policy.

Desktop arrow keys supplement WASD movement. Browser Q/E move camera height; X restores normal height and levels the view. Mobile needs movement/look, first-/third-person switching and separate height adjustment. Third-person camera control must support looking/orbiting around the avatar with behind-avatar follow as the default. VR must preserve full 6DoF tracked pose. The input adapters must not treat browser camera repositioning as an instruction to overwrite the headset's physical pose.

Build [plain-language guidance](USER_GUIDE_PLAN.md) into user flows. Unity/backend/renderer details belong in developer notes unless they help the person complete a task.

## Cabinet states and capture-assisted inventory

Cabinet inspection needs a separate appearance/interaction state layer, door-local versus interior anchors, and correctly retired/hidden closed-door geometry. A hybrid 3D door and captured interior is a candidate, not a selected renderer feature.

Gemini-assisted inventory can consume selected evidence frames asynchronously while capture continues. Keep capture/pose context, source evidence, candidate extraction, designated-editor approval and spreadsheet synchronization as separate responsibilities. No automatic detection accuracy or real-time latency is established.

See [cabinet states](CABINET_STATES.md) and [AI capture inventory](AI_CAPTURE_INVENTORY.md).

## Existing spreadsheet templates

The supplied examples require both field-oriented facilities forms and spatial rack/RU layouts. Maintain explicit template/slot/range mappings alongside stable record IDs; do not derive database identity from visible colour or cell address alone.

Gemini proposals must pass the confirmed designated-editor approval gate before live writes. Native workbook metadata is required to identify formulas, validations, protection and merge/layout rules. See [spreadsheet examples](SPREADSHEET_EXAMPLES.md).

## Production access policy

Production must require the company network/VPN and password access. Authorized viewers and designated editors have different rights.

When the required company connection is lost, the app must lock both viewing and editing, including opening cached tours and attachments. Restoring a connection alone must not bypass expired authentication or lost permissions.

Detection method, detection delay, server enforcement, session expiry, interrupted saves and cache handling need a concrete implementation. Public internet availability is a different condition from reachability of the required company service.

Demo exemptions need an explicit configuration boundary. A demo build must not be treated as evidence that production access enforcement works.

## Rendering feasibility

No renderer, graphics backend, splat format or fallback has been selected.

Use a representative small scene to establish performance and visual quality on iPhone SE Gen 3, Quest 2 and the required browsers. Add Android reference hardware and Quest capture experiments once requirements and available devices are confirmed.

Record exact engine/package versions, artifact size, frame timing, peak memory, loading behavior and device/browser versions. Set performance and quality acceptance thresholds with Arlen instead of inventing them.

## Decisions still required

- Unity version, render pipeline, package licenses and project layout.
- One renderer versus platform-specific adapters or a different approved fallback.
- Capture versus import for the first demonstrator.
- Reconstruction location, processing hardware and acceptable wait.
- Google integration contracts, workbook structure and additional spreadsheet adapter scope.
- Exact capture-assisted inventory fields, additional Gemini data/actions and who may change integration approval policy.
- Partial-rescan partitioning, registration, replacement and fallback criteria.
- Storage, company hosting, authentication and role administration.
- Offline interruption/save recovery, conflict resolution and deletion semantics.
- Normal camera-height reference, mobile touch layout, third-person orbit/follow limits, VR locomotion comfort and headset presentation.

Check current primary documentation when selecting dependencies. No backend or production security recommendation has been validated by this documentation change.
