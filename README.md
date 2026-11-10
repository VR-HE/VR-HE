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
- [Test plan](docs/TEST_PLAN.md): acceptance checks and untested device targets.
- [Development log](docs/DEVELOPMENT_LOG.md): human/AI contributions and validation evidence.
- [Shared contributor instructions](AGENTS.md): applies to developers and coding assistants.
- [Claude entry point](CLAUDE.md): uses the same project instructions.

## Confirmed behavior

- Attach descriptions, structured information and nested data sets to relevant places and equipment.
- Give ordinary users simple runtime editing, including right-click interaction on desktop.
- Use equipment-type templates, with record-local field changes by default.
- Link data to an ordinary external spreadsheet with two-way value updates and mapped additions/deletions.
- Provide familiar WASD/mouse navigation and first-/third-person views, with a generic non-gender humanoid for scale. Touch and VR behavior still need design.

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

There are no build or run commands yet. The Unity version, rendering approach, backend and spreadsheet provider remain open. Record exact versions, package licenses, setup steps and successful build/device evidence when implementation starts.

The next product-design question is which spreadsheet platform the application must synchronize with. An early rendering experiment must also establish a feasible path across the weakest requested devices and browser targets.

## Working together

ChatGPT/Codex access to this repository has been verified as VR-HE. Claude Code requires its own local Git/GitHub setup; that setup is not yet verified. Use small reviewable changes and record what was planned, implemented and actually tested.

Do not commit real headend scans, operational spreadsheets, credentials or private attachment data. Use synthetic data for the demo. The existing Unity ignore rules are retained; review them when the Unity project directory is chosen.
