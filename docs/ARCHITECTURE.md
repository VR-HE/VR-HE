# Proposed architecture

Status: design notes, November 10, 2026. These are proposed boundaries, not implemented modules or approved technology selections.

## System responsibilities

| Area | Responsibility | Open choice |
| --- | --- | --- |
| Capture/import | Acquire imagery and associated pose/calibration information, or import an existing capture | Integrated capture scope and APIs |
| Reconstruction | Produce splats and any supporting geometry | Device, workstation or approved private server |
| Tour viewing | Load visual assets, navigation and view modes | Renderer, streaming, budgets and browser path |
| Asset data | Store places, equipment, fields, templates and attachments | Schema, persistence and backend |
| Interaction/editing | Select an area or object and edit its linked information at runtime | Proxy geometry, anchors and input equivalents |
| Spreadsheet sync | Map records and apply bidirectional values and structural changes | Provider, mapping, latency and conflict policy |
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
- Spreadsheet provider and workbook structure.
- Storage, company hosting, authentication and role administration.
- Offline interruption/save recovery, conflict resolution and deletion semantics.
- VR locomotion comfort and interpretation of third-person view.

Check current primary documentation when selecting dependencies. No backend or production security recommendation has been validated by this documentation change.
