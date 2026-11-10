# Integrations and approval controls

Status: confirmed requirements and proposed design, November 10, 2026. No live integration exists.

## Confirmed requirements

- Compatibility with Google Drive, Google Sheets and Google Gemini.
- Ability in the finished product to open access through approved AI/spreadsheet tools and close access through unapproved ones.
- Extensibility for tools such as ChatGPT, Claude, Excel, OpenOffice and others.
- Existing production intranet/VPN, password and designated-editor requirements still apply.
- Spreadsheet synchronization still includes two-way values and mapped additions/deletions.

Required compatibility is not an instruction to connect credentials, upload site data or grant every provider access now. Exact Google workflows, Gemini capabilities, approval roles and release scope remain open.

## Separate capabilities

| Integration | Required direction | Still to define |
| --- | --- | --- |
| Google Drive | Compatible file/storage and linked-information workflows | Files, shared drives, scan/attachment storage, permissions and retention |
| Google Sheets | Two-way values and mapped structural changes | Workbook layout, sparse fields, formulas, conflicts and recovery |
| Google Gemini | Assist baseline equipment/spreadsheet recording while capture proceeds | Product/API, field scope, draft-review/direct-write policy, allowed inputs and deployment |
| Additional AI tools | Enable approved and disable unapproved integrations | Named adapters, supported tasks, data scopes and identity |
| Additional spreadsheet apps | Approved compatibility, including Excel/OpenOffice paths | Hosted API versus file/desktop automation, format fidelity and sync behavior |

A consumer chat subscription or installed desktop app is not a verified API integration contract. Choose and test the exact interfaces before claiming compatibility.

## Proposed boundaries

Use independent adapters behind company policy and authorization checks. Define both directions where needed:
- Application sends permitted information to an approved provider.
- An approved external client accesses permitted application information or actions.

Candidate policy settings include enabled/disabled provider, approved service/account/endpoint, data scope, allowed operations and the role allowed to change policy. None of these permission details has been selected yet.

Enforce restrictions at service/API and job-execution boundaries, not only by hiding a menu. Preserve normal viewer/editor and company-connection checks for integration-driven access.

Disabling an integration needs explicit handling for new requests, queued jobs, cached responses and credentials. Decide revocation timing and treatment of in-flight work before implementation.

Controls in this app govern its own data paths. Direct Google Drive/Sheets sharing and access outside the app require appropriate Google account/Workspace policy too. Revocation does not retrieve copies already exported to another system.

## Google implementation candidates

The Drive API exposes cloud file/storage integration. The Sheets API exposes spreadsheet reads/writes and structural batch requests. Developer metadata is one candidate for tracking mappings, alongside ordinary stable-ID fields; select the mapping deliberately.

Gemini can be integrated through a supported API/SDK. Keep service credentials out of distributed browser/headset/mobile builds where they would be exposed; use an appropriate authenticated service or supported client authorization design.

Company intranet/VPN access to this app and approved access to Google cloud services are separate network concerns. Hosting, approved routes and account policies remain to be chosen.

## Additional spreadsheet compatibility

Do not treat an .xlsx/.ods import as proof of native two-way synchronization. Define each adapter's support for:
- Values/types and formatting where needed.
- Row/column/record/field additions and deletions.
- Formula ownership and protected data.
- Stable identity through sorting and movement.
- Simultaneous changes, failed writes and recovery.
- Offline or locked-file behavior.
- Provider approval and access permissions.

Excel and OpenOffice use different interfaces and deployment assumptions. The additional-adapter release order and supported formats/versions still need decisions.

## Capture role and next decision

Arlen now requests baseline equipment/spreadsheet recording assistance during capture. See [AI capture inventory](AI_CAPTURE_INVENTORY.md) for evidence links, uncertain values, duplicate handling and the proposed workflow.

The next decision is whether candidate entries require designated-editor review before live writes or may be written directly under defined permissions. Draft-first review is recommended, not yet selected. Exact fields, permitted data/actions, company approval roles and audit evidence still need decisions. Do not assume AI may modify equipment records or spreadsheets without the applicable editor permissions.

## Primary references checked

- [Google Drive API](https://developers.google.com/workspace/drive/api/guides/about-sdk)
- [Google Sheets API](https://developers.google.com/workspace/sheets/api/guides/concepts)
- [Sheets batch updates](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)
- [Sheets developer metadata](https://developers.google.com/workspace/sheets/api/guides/metadata)
- [Google API authorization](https://developers.google.com/identity/protocols/oauth2)
- [Google Gen AI SDK](https://googleapis.github.io/js-genai/release_docs/)
- [Apache OpenOffice API](https://www.openoffice.org/api/)
- [Microsoft Graph Excel APIs](https://learn.microsoft.com/en-us/graph/excel-concept-overview)

These sources document building blocks. They do not show that VR-HE implements or has tested any integration.
