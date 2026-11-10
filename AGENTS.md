# Shared project instructions

## Purpose and authority

VR-HE is a Unity work utility for Gaussian splat tours of ISP hubsites/headends and information attached to places and equipment.

Read these files before making a project change:
1. docs/PRODUCT_SPEC.md
2. docs/DECISIONS.md
3. docs/HANDOFF.md
4. The architecture, synchronization or test-plan sections relevant to the task.

Confirmed user decisions take precedence over proposals. Current explicit user instructions take precedence over repository guidance. Record new decisions so that another developer or assistant can continue accurately.

## Working state

This repository currently contains requirements and developer setup only. Do not imply that a Unity app, splat capture/rendering pipeline, backend, spreadsheet integration or security system is implemented. The requested device matrix is not a tested support matrix.

Ask one primary product question at a time. Explain meaningful consequences in plain language, record the answer and resolve important follow-ups before advancing. Continue independent authorized work while a question is pending.

## Preserve requirements

- Unity and open-source application code are requested; no application license or Unity version is selected.
- Production requires the company intranet/VPN and password access.
- Loss of the required company connection must lock both viewing and editing, including downloaded tours and attached data.
- The test demo is exempt from the production VPN/password/connection-lock requirements.
- Only designated production editors may change descriptions, equipment records and attachments.
- New equipment starts from reusable templates; a field change is local to the selected record by default.
- Reusing a field in a template for future equipment is a separate action.
- Spreadsheet integration means two-way values AND mapped structural create/delete changes. A hyperlink or one-time import/export does not satisfy it.
- A local field removal must not accidentally delete a shared spreadsheet column or another record's data.
- Google Drive, Google Sheets and Gemini compatibility is required; do not ask again whether Google Sheets is required.
- The finished product must allow approved and disable unapproved AI/spreadsheet integrations, with extensibility for tools such as ChatGPT, Claude, Excel and OpenOffice. Exact roles/scopes remain open.
- Virtual cabinets need open/closed inspection states with door-mounted and interior records. The proposed capture workflow uses closed/open local passes and clear inner-door/interior views; prove state registration/visibility.
- Gemini assists baseline equipment/spreadsheet recording during capture by creating source-linked drafts. Arlen selected option 1: designated-editor approval is required before AI-generated entries or updates reach the live spreadsheet. Manual editing retains its existing role/sync rules.
- Support template-aware mappings for the supplied facilities audit and rack/RU diagram examples. Preserve formulas, validation, units and layout; videos do not establish exact native cell metadata.
- Support site changes and target partial rescanning where feasible. Prove alignment, old-geometry removal and metadata preservation before claiming this works.
- Include plain-language in-app guidance for scanning, editing, navigation and finding attached information, usable by non-gamers.
- Desktop browsers support arrow-key movement as well as WASD; use up/down/left/right as forward/back/left/right equivalents unless the user changes that mapping.
- Browser Q raises and E lowers the camera; X restores both normal camera height and a level viewing angle. The first-/third-person toggle is a separate binding.
- iPhone/Android require familiar mobile FPS/third-person movement/look controls, view switching and a separate camera-height up/down control.
- Third-person view requires looking/orbiting around the avatar, not only a fixed behind-avatar camera. Preserve VR 6DoF when designing any VR camera behavior.
- VR must support full 6DoF; browser camera commands do not authorize overriding tracked headset pose.

## Claude build effort

Arlen requires MAX effort for Claude implementation/build work.

- Start through scripts/start-claude.sh or an equivalent explicit MAX launch.
- Verify the selected model, installed Claude Code version and active effort before build work; record the evidence in the development log.
- Do not equate an instruction in a prompt or this file with an actual client/model setting.
- If the client, model or policy lowers the requested effort, report it and resolve the capability/configuration issue before claiming MAX is active.
- This requirement does not authorize extra agent delegation, broader data access or permission bypass.

## Implementation guidance

Separate visual capture/rendering, durable asset data, runtime editing, synchronization and access policy. Read docs/INTEGRATIONS.md, docs/CAPTURE_UPDATES.md, docs/USER_GUIDE_PLAN.md, docs/CABINET_STATES.md and docs/AI_CAPTURE_INVENTORY.md and docs/SPREADSHEET_EXAMPLES.md when working in those areas. Keep ordinary editing usable without Unity, code edits or recompilation.

Stable IDs, interaction geometry and versioned schemas are proposed directions requiring concrete designs. Do not silently promote an unapproved renderer, provider, data model, deletion policy or conflict strategy into a user decision.

Validate the weakest required devices and browser path early. Identify capture, reconstruction/training and viewing as separate capabilities. A successful desktop render is not evidence of Quest/mobile/browser support.

## Evidence, changes and handoff

- Use small reviewable commits; check the branch and existing changes before editing.
- Use separate branches/worktrees if concurrent tasks are explicitly assigned.
- Record meaningful changes, human decisions and actual AI contributions in docs/DEVELOPMENT_LOG.md.
- Label planned, implemented, mocked and physically tested behavior separately.
- Run checks appropriate to the change; report results and limitations without inventing device tests.
- Keep docs/HANDOFF.md and relevant decision/specification documents current.
- Add useful code comments about intent, data contracts and extension points; avoid comments that merely repeat code.
- Do not invent metrics, API capabilities, licensing entitlements or verification.
- Do not request another confirmation for routine reversible work already authorized.

## Data and credentials

Use synthetic fixtures in source control. Do not commit operational site captures, production workbooks, credentials, private attachments or personal data without an appropriate explicit storage decision.

Keep secrets out of source, logs and chat. Use the authenticated VR-HE project connection for this repository. Authentication in one assistant does not authenticate a different application or the user's local Git tools.

## Cross-assistant entry points

CLAUDE.md points here. Keep one shared set of instructions rather than divergent copies. docs/PRODUCT_SPEC.md is the canonical maintained requirements document in this repository.
