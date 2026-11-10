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

This repository starts with documentation only. Do not imply that a Unity app, splat capture/rendering pipeline, backend, spreadsheet integration or security system is implemented. The requested device matrix is not a tested support matrix.

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

## Implementation guidance

Separate visual capture/rendering, durable asset data, runtime editing, synchronization and access policy. Keep ordinary editing usable without Unity, code edits or recompilation.

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
