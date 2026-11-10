# Spreadsheet synchronization

Status: required behavior and open design, November 10, 2026. No provider, adapter or real workbook has been selected or connected.

## Required behavior

All supported data-set categories must be able to link to a common ordinary spreadsheet that remains usable in its normal application.

Both directions must support:
- Value changes.
- Mapped additions of fields, cells or records.
- Mapped deletions.

A hyperlink, read-only dashboard or one-time import/export is insufficient. The exact workbook/tab/row/column representation remains open.

## Preserve local edits

A new field belongs to the selected equipment record by default. Template reuse for future equipment is a separate user action.

| Operation | Required distinction |
| --- | --- |
| Clear a value | The field/record can still exist |
| Remove a field from one record | Do not delete other records' values or a shared column by accident |
| Delete an equipment record | Define scope, recovery and corresponding mapped spreadsheet operation |
| Delete a shared field/column | Determine affected records explicitly; this is broader than a local edit |
| Save a field into a template | Affects future equipment setup; does not silently rewrite existing records |

These distinctions preserve confirmed requirements. Exact delete/archive/recovery rules must still be decided with Arlen.

## Proposed synchronization contract

Use durable identifiers for records, fields and mappings; do not rely solely on row number, display name or cell address.

Candidate metadata includes origin, revision, operation ID and last applied revision. Their representation is undecided. Avoid feedback loops, duplicate application and silent loss when a write fails or a client reconnects.

Reconcile schema changes with existing records. The spreadsheet needs a usable representation of sparse, per-record custom fields without treating every local field change as a global schema edit.

Define how to handle:
- Row sorting, insertion, movement, deletion and renamed tabs.
- Adding or removing a mapped field from either side.
- Changes made in both applications before synchronization.
- Formulas, calculated values, protected cells and units.
- Empty values versus absent fields and deleted records.
- Partial failures, interrupted writes, retries and failed permissions.
- Mapping repair and recovery of accidental deletions.
- Attachment references and nested data sets.

Do not choose last-write-wins, conflict rejection, manual review or automatic merge without recording that decision.

## Access policy

Production sync must respect company-network/VPN, password and designated-editor requirements. Spreadsheet permissions and application roles need to agree. A spreadsheet edit must not automatically grant app editing rights.

Define what background sync may do after a client loses the required company connection. The confirmed client behavior remains locked viewing/editing. Do not silently queue user edits through that lock.

No production credentials or workbook contents belong in the source repository. Start with synthetic demo fixtures and a mock adapter when implementation reaches this module.

## First question and follow-ups

First select the required provider/storage: Microsoft 365 Excel, Google Sheets, or a network Excel file.

Then decide workbook scope, schema/mapping, structural-operation meanings, update latency, conflict ownership, formula ownership and recovery.

These choices affect implementation. Do not represent direct editing of a network file and a hosted spreadsheet API as interchangeable integrations.

## Primary documentation starting points

- [Google Sheets batch updates](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)
- [Microsoft Graph Excel APIs](https://learn.microsoft.com/en-us/graph/excel-concept-overview)

Recheck current capabilities, authorization, limitations and deployment compatibility when the provider is selected. These references do not establish that synchronization has been implemented.
