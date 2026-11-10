# VR-HE

A planned Unity work utility for touring ISP hubsites and headends using Gaussian splats, with editable information attached to rooms, racks, rack-unit locations and equipment.

**Current state: requirements and developer documentation only.** There is no runnable application or Unity project yet. Capture, rendering, authentication and spreadsheet synchronization are not implemented. Device compatibility has not been demonstrated.

The repository is private. Open-source application code is the intended direction; the application license has not been selected. Unity itself remains subject to its own license.

## Start here

- [Product specification](docs/PRODUCT_SPEC.md): confirmed behavior, proposals and open questions.
- [Decision record](docs/DECISIONS.md): what Arlen has actually chosen.
- [Developer handoff](docs/HANDOFF.md): current state and next steps.
- [Proposed architecture](docs/ARCHITECTURE.md): module boundaries and unresolved choices.
- [Spreadsheet synchronization](docs/SPREADSHEET_SYNC.md): required two-way behavior and mapping questions.
- [Integration controls](docs/INTEGRATIONS.md): Google requirements and approved AI/spreadsheet connections.
- [Capture updates](docs/CAPTURE_UPDATES.md): site changes and the partial-rescan feasibility target.
- [Built-in user guide plan](docs/USER_GUIDE_PLAN.md): scanning, editing, navigation and finding information.
- [Test plan](docs/TEST_PLAN.md): acceptance checks and untested device targets.
- [Development log](docs/DEVELOPMENT_LOG.md): human/AI contributions and validation evidence.
- [Shared contributor instructions](AGENTS.md): applies to developers and coding assistants.
- [Claude entry point](CLAUDE.md): uses the same project instructions.

## Confirmed behavior

- Attach descriptions, structured information and nested data sets to relevant places and equipment.
- Give ordinary users simple runtime editing, including right-click interaction on desktop.
- Use equipment-type templates, with record-local field changes by default.
- Integrate with Google Drive, Google Sheets and Google Gemini. Preserve two-way spreadsheet values and mapped additions/deletions.
- Let authorized company policy enable approved AI/spreadsheet integrations and disable unapproved ones, with extensibility for tools such as ChatGPT, Claude, Excel and OpenOffice.
- Update tours as sites change; target rescanning only changed sections plus alignment overlap where feasible. This requires a prototype.
- Include plain-language in-app guidance for scanning, adding information, navigating and finding stored information.
- Provide familiar WASD/mouse navigation and first-/third-person views, with a generic non-gender humanoid for scale.
- Browser camera: Q raises the viewpoint, E lowers it and X recenters it. X's exact meaning needs clarification; the view-toggle key remains open.
- VR must support full six-degree-of-freedom movement. Touch/controller traversal and comfort settings still need design.

| Access rule | Official production version | Test demo |
| --- | --- | --- |
| Company intranet/VPN | Required | Not required |
| Password access | Required | Not required |
| Company connection drops | Lock viewing and editing, including cached tours/data | No production connection lock |
| Editing | Designated editors; other authorized users view only | Demo permission behavior still to be defined |

## Requested platforms

These are targets, not a compatibility claim.

| Platform | Capture target | Viewing target |
| --- | --- | --- |
| iPhone | SE Gen 3 or newer | SE Gen 3 or newer |
| Android | Equivalent or better; reference devices pending | Equivalent or better; reference devices pending |
| Meta Quest | Quest 3/3S or better | Quest 2 or better |
| Browser | Not requested | Chrome, Firefox, Edge and Brave |

## Build and run

There are no build or run commands yet. Google Drive, Sheets and Gemini compatibility is required. The Unity version, rendering approach, backend, credentials and exact integration contracts remain open. Record exact versions, package licenses, setup steps and successful build/device evidence when implementation starts.

The immediate controls clarification is what X should recenter: view angle, camera height or both. Gemini's allowed tasks/data scope, spreadsheet mappings and provider-approval roles also need decisions. Early experiments must establish rendering feasibility and partial-update quality across the requested targets.

## Working together

ChatGPT/Codex access to this repository has been verified as VR-HE. Arlen reported Git 2.43.0 and successful installation of GitHub CLI 2.45.0 on his Linux laptop. Local VR-HE authentication and repository access still need verification for Claude Code. Use small reviewable changes and record what was planned, implemented and actually tested.

Do not commit real headend scans, operational spreadsheets, credentials or private attachment data. Use synthetic data for the demo. The existing Unity ignore rules are retained; review them when the Unity project directory is chosen.
