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

This repository contains requirements, developer setup and a rendering-only browser prototype with results on one Linux laptop and one personal Windows 11 PC (Edge/Chrome; reviewed 30 Hz and 60 Hz baselines). A first interactive browser demo prototype (branch proto/interactive-browser-demo) is checked in Chrome and Brave on the Linux laptop only; its Windows bundle is untested. The full VR-HE application, capture pipeline, backend, spreadsheet integration and security system are not implemented. Consult docs/HANDOFF.md for tested conditions; the requested device matrix is not a tested support matrix.

Ask one primary product question at a time. Explain meaningful consequences in plain language, record the answer and resolve important follow-ups before advancing. Continue independent authorized work while a question is pending.

## Preserve requirements

- Unity and open-source application code are requested; no application license is selected. Unity 6.3 LTS 6000.3.15f1 with the plain URP template is approved for the initial prototype only; the long-term Unity version and renderer remain provisional (D031).
- Production requires the company intranet/VPN, password access and authenticator-app verification compatible with Google Authenticator (D040). The demo remains exempt; production MFA is not implemented. See docs/PRODUCTION_AUTHENTICATION.md.
- Loss of the required company connection must lock both viewing and editing, including downloaded tours and attached data.
- The test demo is exempt from the production VPN/password/connection-lock requirements.
- Only designated production editors may change descriptions, equipment records and attachments.
- New equipment starts from reusable templates; a field change is local to the selected record by default.
- Reusing a field in a template for future equipment is a separate action.
- Multiple equipment records may belong to one rack; each rack-mounted item records the RU or RU range it occupies (D037). The first demo has rack records only, not equipment authoring.
- Each new equipment record starts with one unnamed description. Add Description may add more descriptions to that item, with optional names selected from a reusable label dropdown (D038/D039).
- Authorized editors may add, rename and remove description-label choices. A label choice is not another item's description value. Removing an in-use label and effects on existing descriptions/sheet mappings remain an open decision; do not silently erase saved values.
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
- Mouse Y inversion is an optional saved preference for first-person look and third-person orbit (D036); height/reset, horizontal look and VR head tracking keep their meanings.
- Browser Q raises and E lowers the camera; X restores both normal camera height and a level viewing angle. The first-/third-person toggle is a separate binding.
- iPhone/Android require familiar mobile FPS/third-person movement/look controls, view switching and a separate camera-height up/down control.
- Third-person view requires looking/orbiting around the avatar, not only a fixed behind-avatar camera. Preserve VR 6DoF when designing any VR camera behavior.
- VR must support full 6DoF; browser camera commands do not authorize overriding tracked headset pose.
- The browser reference PC is Arlen's Panasonic Toughbook FZ-55 work laptop: i5-8365U (4 cores / 8 logical processors), 32 GB RAM and Intel UHD Graphics 620, identified in his November 10 Task Manager photos (D033). Exact OS/browser versions, browser graphics backend and performance remain unverified; see docs/TEST_PLAN.md.
- Company authorization is required before running this benchmark on Arlen's work Toughbook; that authorization has not been provided. His personal Windows 11 VR gaming PC has completed the initial Edge/Chrome baselines; see the reviewed results in docs/HANDOFF.md. Keep the Toughbook as the minimum browser reference and leave its qualification pending (D035).
- Arlen's minimum frame rates are 30 fps for the browser and 60 fps for VR headsets (D034). Report application-rendered fps separately from headset display Hz and synthesized/reprojected frames. The initial 72 fps / 72 Hz Quest engineering target is a recommendation, not a replacement for his floor; see docs/TEST_PLAN.md.

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
