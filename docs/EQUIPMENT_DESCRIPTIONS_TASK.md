# Next local task: mouse option build and rack equipment authoring

Status: queued after Arlen's November 11 hands-on feedback. D036-D039 are confirmed requirements; the Y-inversion checkbox/bridge change is source-only pending a local build. Equipment/RU authoring, multiple descriptions and the label catalog are not implemented.

Read [AGENTS.md](../AGENTS.md), [specification](PRODUCT_SPEC.md), [decisions](DECISIONS.md), [handoff](HANDOFF.md), [architecture](ARCHITECTURE.md) and [spreadsheet rules](SPREADSHEET_SYNC.md). Continue in the VR-HE repository with verified Claude MAX effort, checking the branch, clean tree, remote and disk headroom first. Preserve local work. Use the existing Unity project provisionally and explicit project paths; keep The Veil, the benchmark and its original bundle untouched.

## First deliverable: rebuild the mouse option

- Pull the current proto/interactive-browser-demo source safely. The shared page bridge now offers Help > Settings > Invert mouse Y-axis, normal by default, saved alongside sensitivity in this demo browser profile.
- Build a new labelled interactive output and Windows ZIP; do not relabel the existing 294f4b2 ZIP as updated. Keep its benchmark evidence and record data.
- Test normal/inverted drag and captured mouse in first and third person, preference persistence across reload/restart, unchanged horizontal look/wheel/picking and Q/E/X, and no movement while a panel/text field is active.
- The cloud review checked JavaScript syntax and isolated preference/frame functions only. It did not load Unity or produce a new build. Chromium could not start under the review workspace's socket restrictions. Run the actual browser checks locally before claiming runtime verification.

## Next authoring slice

Use a separate reviewable prototype branch, with source/schema comments and synthetic data. Continue independent authoring work while the in-use label removal question is open; do not silently choose destructive behavior.

1. Keep rack identity separate from equipment identity. Add/edit multiple equipment records under each rack, each with stable IDs and occupied RU start/end. A multi-RU server is one item, not duplicate records per U. Make the rack/equipment hierarchy discoverable from a panel/list as well as selection in the tour.
2. Expose RU range editing with clear bounds and potential-overlap messages. Document prototype numbering/capacity assumptions; front/rear co-occupancy and real-world dimensional accuracy are not yet decisions or demonstrated features. The scan remains a picture: records/proxies describe inventory without pretending to move the captured physical server.
3. Start new equipment with exactly one empty, unnamed description. Add Description creates another description for the selected item. Each description needs durable identity separate from its text, display order and optional label reference.
4. Provide a reusable label dropdown with a discoverable create/edit/remove-label route. Choosing a label must not copy another item's text. A new label is not a bulk record/template edit. Decide/document provisional catalog scope and storage boundaries as implementation proposals.
5. Preserve values during rename/removal. Removing a description from one item, removing a dropdown choice and removing a mapped shared spreadsheet field are different operations. Ask Arlen's unresolved in-use-label question before implementing destructive existing-value behavior; implement the independent features first.
6. Version the store/export and migrate the delivered single-description rack records without dropping IDs, edits, unknown records or recovery copies. Rack-level notes must not be silently recast as an equipment item's description. Keep legacy exports inspectable and existing saved demo data recoverable.
7. Keep the data model ready for explicit Google Sheets/Drive mappings without a live adapter. A label rename is not automatically a spreadsheet column rename, and a local field removal is not automatically a shared column delete.
8. Extend plain-language help. Verify two devices in one rack (including a multi-RU item), distinct values under a reused label, an unnamed note plus several named notes, record-local changes, reload/restart/export and safe old-data migration. Measure frame pacing while using the new panels.

Keep production roles and the Google Authenticator addition in the design; do not add production login/MFA or live company/Google connections to this demo task. See [production authentication](PRODUCTION_AUTHENTICATION.md). Commit source/docs, keep builds/raw data ignored, and report the exact new local ZIP path, tested behavior and Windows instructions.
