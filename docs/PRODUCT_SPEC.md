# VR-HE — Product Specification

Status: requirements baseline 0.9; requirements interview continues. Documentation only.
Updated: November 10, 2026.
Owner/requester: Arlen.
Purpose: a work utility for virtually touring ISP hubsites and headends and maintaining information attached to places and equipment.

This records requested behavior, proposed design ideas, and unresolved decisions separately. Requested platform support is a target for implementation and testing, not a claim that compatibility has already been demonstrated.

## Requested requirements

| Area | User requirement |
| --- | --- |
| Visual environment | Gaussian splat representation of real ISP hubsites and headends |
| Site information | Attach descriptions and data sets to rooms, racks, RU locations/ranges, equipment, and other relevant areas |
| Nested information | Add further sub-data sets and equipment information flexibly in the running app |
| Ordinary-user editing | Simple mouse right-click interaction, designed for people who are not technically confident |
| First-person movement | Familiar WASD and mouse controls on keyboard/mouse platforms |
| Third-person view | Behind-the-avatar view with a generic non-gender humanoid to communicate relative size and scale |
| View switching | Familiar first-/third-person toggle; exact key and per-platform behavior remain to be selected |
| Engine | Unity |
| Source availability | Open-source application code; exact license remains to be chosen |
| Developer extensibility | Modular structure and useful script/code documentation so another developer/team can extend the application |
| Capture devices | iPhone SE, third generation, or newer; comparable or better Android devices; Quest 3/3S or better |
| Viewing devices | iPhone SE, third generation, or newer; comparable or better Android devices; Quest 2 or better |
| Browsers | Chrome, Firefox, Edge, and Brave |
| Product character | Practical workplace tool; navigation conventions should feel familiar without adding game-like objectives |
| Production access | Mandatory intranet/VPN access and mandatory password access |
| Test-demo access | Neither intranet/VPN access nor password access is required |
| Production connection loss | Lock downloaded tours and attached data until the required company-network/VPN connection is restored |
| Production editing permissions | Designated editors may change descriptions, equipment records and attachments; other authorized users have view-only access |
| Equipment record setup | Reusable equipment-type templates with fields editors can customize in the app |
| Field-change scope | Record-local by default, with a separate option to reuse the field in a template for future equipment |
| Shared spreadsheet | All data-set categories can link to a common ordinary spreadsheet with two-way value and mapped structural create/delete synchronization |
| Development tracking | Use GitHub repository VR-HE/VR-HE; access is verified; include detailed developer handoff and transparent human/AI process records |

The user's latest requirements supersede earlier suggested architecture where they conflict. In particular, the earlier proposal of a PlayCanvas browser viewer is not an accepted replacement for the requested Unity application.

## Product model to develop

The application combines:
1. A captured visual environment for navigation and recognition.
2. Persistent records identifying actual places, equipment and associated data.
3. In-app tools for creating, editing, finding and sharing those records.

Proposed record organization: site, room/area, rack, RU position or range, equipment, and attached/nested information. The exact hierarchy, cross-links, front/rear rack representation, and handling of equipment spanning several RUs are still open.

Descriptions and nested information are requested, and reusable templates with editor-customizable fields are now confirmed. Specific field data types and attachment formats, including photos, documents, tables and links, still need selection. Do not silently treat every example as a mandatory first-release feature.

A splat should not be assumed to supply equipment identity, clean object boundaries, collision geometry, readable nameplate text, physical measurements, or live telemetry automatically.

## Proposed architecture principles — not yet approved implementation choices

- Keep equipment/place records separate from the captured appearance.
- Use stable identifiers so changing a name, moving equipment or updating a scan does not inherently destroy its history.
- Provide selectable areas/objects using suitable interaction geometry and anchors. The exact combination of splat depth, proxy meshes, volumes and manual placement requires a prototype.
- Ordinary editing should save at runtime without opening Unity, editing code or recompiling.
- Use a documented, versioned data format. Database, file package and backend technology are not selected.
- Separate capture, reconstruction/training, viewing, record editing and synchronization modules.
- Share one logical editing action across input methods. Candidate equivalents are right-click on desktop, a touch action on phones, and ray selection plus a controller action in VR.
- Mouse-look and menus need predictable cursor handling. A candidate is to pause mouse-look while a context menu is open and return after closing it.
- Choose an actual documented camera-toggle binding instead of assuming every FPS uses the same key.
- Keep first-/third-person presentation distinct from the user's real headset pose; the VR interpretation needs a separate comfort decision.
- Give developers extension points and data-schema notes. End users should not have to use these developer mechanisms.
- Preserve original photographs for text/detail that the splat does not reliably reproduce. Whether photo hotspots are a required first-release feature is still to be confirmed.

## Device and rendering questions to validate early

| Target | Requested role | Validation needed |
| --- | --- | --- |
| iPhone SE Gen 3 | Capture and view | Capture quality, supported APIs, memory, thermal behavior, navigation and editing UI |
| Android equivalent or better | Capture and view | Replace the vague equivalence with named reference devices and minimum OS/RAM/GPU/camera/API requirements |
| Quest 3/3S | Capture and view | Camera permissions, image/pose calibration and timestamps, available depth source and actual capture quality |
| Quest 2 | View | Actual standalone rendering and editing performance; do not imply Quest 2 supports the requested Quest capture API |
| Chrome / Firefox / Edge | Browser view | Compatible renderer, navigation, persistence, memory limits, file access and input handling |
| Brave | Browser view | Explicit testing; do not infer full support solely from its Chromium foundation |
| Desktop native application | Unconfirmed additional target | User specified keyboard/mouse controls and browsers, but did not explicitly require a native Windows/Linux/macOS release |

Unity's current web documentation lists desktop Chrome, Firefox and Edge, plus Safari, and defines browser requirements. That does not establish that any particular Gaussian splat renderer will work in them.

Treat aras-p/UnityGaussianSplatting as a candidate/reference, not a proven solution for this device matrix. Recheck its current platform support, graphics-backend requirements, maintenance status and license before selecting any dependency. No renderer has been selected or tested for VR-HE.

Early rendering work should therefore test the weakest required devices and browser path using a representative small headend scene before building a large editing system around a specific renderer.

Unity application code can be open source. Unity's engine and editor themselves are licensed proprietary software; an open-source application does not change that. Confirm an appropriate Unity license for the eventual organization and deployment. No licensing entitlement or price has been determined in this interview.

## Question 1 — resolved: production access and connection loss

Confirmed by Arlen:
- The official production version must require intranet/VPN access.
- The official production version must require password access.
- The test demo we are building does not require intranet/VPN access.
- The test demo does not require password access.
- If the required company-network/VPN connection drops in the official version, lock previously downloaded tours and attached data until the connection is restored. Arlen selected option 1.

| Access requirement | Official production version | Test demo |
| --- | --- | --- |
| Company intranet/VPN access | Required | Not required |
| Password-authenticated access | Required | Not required |
| Lock on loss of required company connection | Required, including downloaded tour/data access | Not required |

Exact hosting, VPN integration, authentication provider and account model are not yet selected. Do not equate loss of public internet with loss of the company intranet; these are separate connectivity conditions.

Confirmed behavior: the official version must lock both viewing and editing of tours and their attached data when the required company connection is lost. Previously downloaded content must not bypass that lock. Access remains locked until the required connection is restored, subject to the mandatory password-access requirement.

The test-demo exemption remains unchanged: it does not require the company intranet/VPN or password access, and does not inherit the production connection-loss lock.

Technical details to settle during implementation include connection-loss detection, session expiry, and interrupted-save recovery. No automatic deletion or wiping of cached data has been requested. These details do not reopen the selected access policy.

Proposed implementation consequence: separate demo and production configurations so demo access exemptions cannot accidentally become production behavior. Production acceptance checks must cover connection loss while viewing, editing, and opening previously downloaded content.

Question 1 outcome: production/demo access and the production connection-loss lock are confirmed.

## Question 2 — resolved: designated editors and viewers

Arlen selected option 1.

Confirmed behavior for the official version:
- Only designated editors may change descriptions, equipment records and attachments.
- Other authorized users have view-only access.
- Signing in does not automatically grant editing rights.

Account administration, assignment of editor rights, site-specific permissions, capture permissions and detailed delete/recovery rights remain to be specified. A mandatory review/approval workflow has not been selected.

Current interview status: Questions 1–3 are resolved. Shared-spreadsheet synchronization is required; platform and mapping decisions remain open. Access to VR-HE/VR-HE is verified; local Claude Code setup remains unverified.

## Question 3 — resolved: reusable templates and local field changes

Arlen selected option 1.

Confirmed behavior:
- New equipment records start from reusable equipment-type templates.
- Designated editors can customize the fields in the app.
- Records can include the previously requested descriptions and nested information.

Example starter fields, not yet approved: manufacturer, model, serial number and installation date for a UPS. The exact starter templates, field data types and attachment formats still need selection.

### Follow-up 3a — resolved: field changes are local by default

Arlen selected option 1, with an additional shared-spreadsheet requirement recorded below.

Confirmed behavior:
- Adding a field changes only the selected equipment record by default.
- Editors have a separate option to save the field in a reusable template for future equipment.
- A record-local addition must not automatically modify every existing equipment record.
- Field definitions and each equipment record's field values remain distinct.
- When linked to a spreadsheet, the selected record's mapped field/value must synchronize without silently broadening that edit to unrelated records.

Question 3 outcome: template-based record setup and record-local field changes with optional future-template reuse are confirmed.

## Question 4 — spreadsheet integration required; spreadsheet platform pending

Arlen requires all data sets to have the ability to point to a common, ordinary spreadsheet outside the virtual environment.

Confirmed functional requirements:
- Two-way updates: edits in the ordinary spreadsheet update the corresponding virtual data sets, and edits in the virtual environment update the corresponding spreadsheet data.
- Support mapped additions and deletions as well as value changes, including the relevant cells and fields on the other side.
- The ordinary spreadsheet remains usable in its normal spreadsheet application.
- All supported data-set categories must be capable of linking; the exact workbook organization and mapping are not yet selected.
- A one-time export/import or a mere hyperlink is insufficient for this requirement.

Proposed implementation approach:
- Use one managed synchronization path with stable equipment, data-set and field identifiers, rather than identifying records solely by row number or cell address.
- Make updates and creates/deletes bidirectional and prevent feedback loops or duplicate application.
- Distinguish clearing a value, removing one record's field, deleting an equipment row and removing a shared field definition/column.
- Respect the confirmed local-edit default. Removing a field from one equipment record must not remove a shared column and other equipment's data as an accidental side effect.
- Define handling of simultaneous edits, formula/protected cells, failed writes, structural changes, undo/recovery and synchronization status.
- Preserve the production intranet/VPN, password and editor-role requirements. Spreadsheet access permissions and background sync must be reconciled with those requirements.
- Keep mock/synthetic spreadsheet data available for the demo. No actual business workbook has been selected or modified.

Unresolved design questions:
1. Which spreadsheet platform/storage is required: Microsoft 365 Excel in OneDrive/SharePoint, Google Sheets, or an Excel file on a company network location?
2. Whether one workbook is shared across all sites, one per site, or another organization.
3. Exact row/column/tab representation of rooms, racks, RUs, equipment, nested data and attachments.
4. Sync latency target, formula ownership, conflict resolution, and the meanings of delete versus clear/archive.

The next product-design question is spreadsheet platform. Repository access is verified; local Claude Code/Git setup remains a separate setup task.

## GitHub and developer handoff — confirmed process requirement

Arlen requires development in the VR-HE GitHub repository with detailed developer notes and transparent records of human decisions, AI assistance, test evidence and limitations.

Verified November 10, 2026:
- Intended account and authenticated connection: VR-HE.
- Repository: https://github.com/VR-HE/VR-HE
- Visibility: private.
- Read and write permissions are available to this project's connection.
- Existing main branch contains a starter README and Unity .gitignore.
- Initial documentation is prepared on docs/project-foundation for review; consult the repository's pull requests for integration status.
- No Unity application, capture system, renderer, spreadsheet adapter or production security implementation exists yet.
- Claude Code's local Git/GitHub authentication has not been verified.

Canonical project records:
- This file is the maintained requirements specification in the repository.
- docs/DECISIONS.md separates confirmed decisions from proposals.
- docs/DEVELOPMENT_LOG.md records actual work and evidence.
- docs/HANDOFF.md tells the next developer or assistant where to continue.
- AGENTS.md supplies shared project instructions; CLAUDE.md points to those same instructions.
- Future product changes should update these repository documents together with implementation.
- The earlier ISP_Virtual_Tour_Product_Brief.md is a discovery record; it must not silently become a competing specification.

Use the same repository for ChatGPT/Codex and Claude Code, with separate working branches when concurrent tasks are explicitly assigned. Connecting ChatGPT does not establish authentication on the computer running Claude Code. No password, token or login code should be pasted into chat.

Keep operational scans, real company spreadsheets, credentials and personal data outside the source repository unless an appropriate storage decision has been made. Demo fixtures should be synthetic.

## Remaining interview topics

Ask one primary question at a time, discuss its consequences, and record confirmed answers before advancing.

- Users and collaboration: individual use, shared company library, simultaneous guided visits, and expected viewer/editor counts.
- Data location and distribution: local packages, company servers/VPN, approved cloud services, access control, and supported update paths.
- Editing ownership: who can create/change/delete records, revision history, undo, recovery and simultaneous edit conflicts.
- Data content: notes, files, photos, structured fields, tables, nested records, the required two-way spreadsheet integration, and other inventory-system integrations.
- Asset relationships: equipment spanning RUs, front/rear access, ports/cables, links between racks/sites, and moved/decommissioned equipment.
- Capture workflow: integrated capture versus importing existing scans; who captures; how much guidance is needed.
- Reconstruction: on-device versus PC/private-server processing; acceptable wait time and hardware availability.
- Site scale: typical room/rack counts, site count, total storage and expected network bandwidth.
- Fidelity: required readability, supported movement area, acceptable holes/artifacts, scale accuracy and measurement expectations.
- Rescanning: scan versions, historical visits, registration to previous scans and preserving equipment attachments.
- Controls: first-/third-person behavior, avatar dimensions, remapping, accessibility, touch equivalents and VR comfort.
- Release scope: what must ship first, device priorities, acceptance tests and what may be deferred.
- Deployment and licensing: application license, dependency compatibility for workplace use, installation, updates and maintenance ownership.

This is a discovery agenda, not a confirmed feature backlog. Avoid presenting it as work already approved for implementation.

## Background references from requirements discovery

- Unity 6.6 browser compatibility: https://docs.unity.com/en-us/engine/6000.6/manual/platform-specific/webgl/intro/browsercompatibility
- UnityGaussianSplatting platform limits and maintenance status: https://github.com/aras-p/UnityGaussianSplatting/blob/main/readme.md
- Unity source-code licensing: https://unity.com/products/source-code
- Meta Quest passthrough camera prerequisites: https://developers.meta.com/vr/documentation/unity/unity-pca-overview/
- iPhone SE third-generation specifications: https://support.apple.com/en-us/111866

- Creating a GitHub repository, including prefilled form URLs: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- Switching GitHub accounts: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/switching-between-accounts
- GitHub CLI authentication: https://docs.github.com/en/github-cli/github-cli/authenticating-with-github-cli
- Google Sheets batch updates: https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate
- Microsoft Graph Excel APIs: https://learn.microsoft.com/en-us/graph/excel-concept-overview
- ChatGPT plugins and app connections: https://learn.chatgpt.com/docs/plugins
- Claude Code workflows: https://code.claude.com/docs/en/common-workflows

Related earlier artifact: Headend_Gaussian_Splat_Project_Prompts.md. It is a preliminary prompt guide; this repository specification takes precedence where requirements differ. References are starting points for verification, not evidence that VR-HE has implemented or tested their capabilities.
