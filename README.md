# VR-HE

A planned Unity work utility for touring ISP hubsites and headends using Gaussian splats, with editable information attached to rooms, racks, rack-unit locations and equipment.

> **ON HOLD from November 11, 2026.** Development is paused until Arlen explicitly resumes it. His company already uses NetBox, and its coverage needs evaluating before he decides whether VR-HE continues. See [the pause checkpoint and restart steps](docs/HANDOFF.md#on-hold--pause-checkpoint-november-11-2026).

**Current state: requirements, developer documentation, a rendering-only browser prototype and a first interactive browser demo prototype.** There is no VR-HE application yet. A separate Unity measurement project, [the browser splat-rendering prototype](prototypes/browser-splat-rendering/README.md), rendered synthetic Gaussian splats in Chrome, Firefox and Brave on one Linux laptop; [the handoff](docs/HANDOFF.md) has the results and the untested platforms. The same project holds [the interactive demo](prototypes/browser-splat-rendering/README.md#interactive-browser-demo-prototype) (branch proto/interactive-browser-demo): walking, first/third-person views, rack selection and editable descriptions saved as local demo data. It was checked in Chrome and Brave on the Linux laptop. The equipment/description extension now has [partial manual Windows evidence](prototypes/browser-splat-rendering/TestResults/windows-manual-20261111/README.md): about 60 fps at a 1280x720 canvas, reported equipment creation/saves and no page errors. Full manual workflow verification remains pending. Capture, authentication, a backend and spreadsheet synchronization are not implemented. Phone/Quest and minimum-Toughbook compatibility remain unverified; Edge/Chrome rendering has now been tested on one personal Windows PC. The prepared bundle completed Edge/Chrome baselines on Arlen's personal Windows 11 PC; the reviewed 30 Hz and 60 Hz runs strongly support display pacing, with about 60 fps through 250k splats at a 1280x720 canvas. Uncapped capacity remains unmeasured. Execution on the company Toughbook still requires company authorization and is deferred (D035).

The repository is private. Open-source application code is the intended direction; the application license has not been selected. Unity itself remains subject to its own license.

## Start here

- [Product specification](docs/PRODUCT_SPEC.md): confirmed behavior, proposals and open questions.
- [Decision record](docs/DECISIONS.md): what Arlen has actually chosen.
- [Developer handoff](docs/HANDOFF.md): the pause checkpoint, restart steps and current state.
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

There are no VR-HE application build or run commands yet. Setup, build and test commands for the browser prototype and the interactive demo are in [its README](prototypes/browser-splat-rendering/README.md). Unity 6.3 LTS 6000.3.15f1 with the URP blank template is approved for the initial prototype only (D031); the long-term Unity version and renderer remain provisional. Google Drive, Sheets and Gemini compatibility is required. The backend, credentials and exact integration contracts remain open. Record exact versions, package licenses, setup steps and successful build/device evidence as implementation continues.

Gemini drafts inventory entries/updates for designated-editor approval before live spreadsheet writes. The supplied examples require mappings for both facilities-audit forms and rack/RU diagrams. Gemini's allowed tasks/data scope, spreadsheet mappings and provider-approval roles also need decisions. Early experiments must establish rendering feasibility and partial-update quality across the requested targets.

## Start Claude Code for development

Arlen requires **MAX effort** for Claude build work. From this repository, run:

```bash
bash scripts/start-claude.sh
```

The [launcher](scripts/start-claude.sh) requests MAX for each session. Check the active level in Claude before starting implementation; see [the handoff](docs/HANDOFF.md). The [local Unity inspection](docs/LOCAL_UNITY_INSPECTION.md) is complete; its findings are in the handoff. This launches the coding assistant, not a Unity application.

## Working together

ChatGPT/Codex access to this repository has been verified as VR-HE. Arlen reported Git 2.43.0 and successful installation of GitHub CLI 2.45.0 on his Linux laptop. His screenshots confirm local VR-HE sign-in, cloning into /home/arlen/Projects/VR-HE, the docs/project-foundation branch and a clean working tree. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration. Claude's November 10 inspection verified the installed Unity tooling: Unity Hub 3.22.6 and Editors 6000.0.84f1, 6000.3.15f1 (6.3 LTS), 6000.6.2f1 and 6000.6.4f1. Only 6000.3.15f1 has both Android and Web support files, and no Editor has iOS support. Installed modules are not tested functionality; see the handoff for what has actually been built and run. Local push access is verified: the inspection commit ff1e070 reached origin/docs/project-foundation from the laptop. Use small reviewable changes and record what was planned, implemented and actually tested.

Do not commit real headend scans, operational spreadsheets, credentials or private attachment data. Use synthetic data for the demo. The root Unity ignore rules are anchored to the repository root, so each Unity project folder carries its own scoped .gitignore (see [the browser prototype](prototypes/browser-splat-rendering/.gitignore)).
