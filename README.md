# VR-HE

A planned Unity work utility for touring ISP hubsites and headends using Gaussian splats, with editable information attached to rooms, racks, rack-unit locations and equipment.

**Current state: requirements, developer documentation and a Claude launcher.** There is no runnable application or Unity project yet. Capture, rendering, authentication and spreadsheet synchronization are not implemented. Device compatibility has not been demonstrated.

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
- [Cabinet inspection](docs/CABINET_STATES.md): virtual open/closed doors and interior information.
- [Gemini-assisted capture](docs/AI_CAPTURE_INVENTORY.md): baseline inventory while recording.
- [Spreadsheet examples](docs/SPREADSHEET_EXAMPLES.md): visual review of the supplied facilities-audit and rack/RU layouts.
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
- Support virtual cabinet open/closed states and information on doors/interiors; prototype aligned local captures or a hybrid movable-door representation.
- Use Gemini to assist baseline equipment/spreadsheet recording during capture. AI-generated entries and updates require designated-editor approval before live spreadsheet writes.
- Provide WASD or arrow-key movement in desktop browsers, with mouse look and first-/third-person views using a generic non-gender humanoid for scale.
- Third-person cameras support looking/orbiting around the avatar, with behind-avatar follow as the default presentation.
- iPhone/Android use familiar mobile FPS/third-person movement and look controls, view switching and a separate camera-height up/down control.
- Browser camera: Q raises the viewpoint, E lowers it and X restores normal camera height and levels the view. The desktop view-toggle key remains open.
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

There are no Unity application build or run commands yet. Google Drive, Sheets and Gemini compatibility is required. The Unity version, rendering approach, backend, credentials and exact integration contracts remain open. Record exact versions, package licenses, setup steps and successful build/device evidence when implementation starts.

Gemini drafts inventory entries/updates for designated-editor approval before live spreadsheet writes. The supplied examples require mappings for both facilities-audit forms and rack/RU diagrams. Gemini's allowed tasks/data scope, spreadsheet mappings and provider-approval roles also need decisions. Early experiments must establish rendering feasibility and partial-update quality across the requested targets.

## Start Claude Code for development

Arlen requires **MAX effort** for Claude build work. From this repository, run:

```bash
bash scripts/start-claude.sh
```

The [launcher](scripts/start-claude.sh) requests MAX for each session. Check the active level in Claude before starting implementation; see [the handoff](docs/HANDOFF.md). This launches the coding assistant, not a Unity application.

## Working together

ChatGPT/Codex access to this repository has been verified as VR-HE. Arlen reported Git 2.43.0 and successful installation of GitHub CLI 2.45.0 on his Linux laptop. His screenshots confirm local VR-HE sign-in, cloning into /home/arlen/Projects/VR-HE, the docs/project-foundation branch and a clean working tree. Claude Code startup/effort and local push access remain to be verified. Use small reviewable changes and record what was planned, implemented and actually tested.

Do not commit real headend scans, operational spreadsheets, credentials or private attachment data. Use synthetic data for the demo. The existing Unity ignore rules are retained; review them when the Unity project directory is chosen.
