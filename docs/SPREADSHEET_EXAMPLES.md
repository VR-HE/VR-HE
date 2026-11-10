# Supplied spreadsheet examples and mapping implications

Status: visual review and proposed adapter design, November 10, 2026. No native workbook was opened or modified.

## Evidence scope

Arlen supplied two screen videos as examples of Google Drive/Sheets interfaces the product should support:
- IMG_3850.mp4: approximately 72 seconds, showing a facilities-audit form.
- IMG_3851.mp4: approximately 36 seconds, showing rack-elevation/RU diagrams.

Sampled frames cover the clips' visible progression, with selected frames inspected at original resolution. This is not a transcription of every cell or narration.

No actual site/rack identities, model/serial values, contacts, workbook URLs, screenshots or operational values are reproduced here. Use synthetic fixtures in source control.

## What is visibly present

| Facilities audit | Rack/RU diagrams |
| --- | --- |
| Bilingual English/French labels | Multiple site-related worksheet tabs |
| Architecture/space and cabinet-count fields | Repeated rack columns with RU numbering |
| Main electrical entrance, generator and transfer-switch sections | Equipment blocks spanning multiple RU rows |
| Repeated UPS, -48V plant/battery and HVAC sections | Colour legend for equipment categories |
| Fire-suppression and maintenance/contact sections | Power/network/RF and other labelled equipment categories |
| Manufacturer/model/serial and installation/replacement date fields | Blank and no-rack labels; an open-rack label also appears |
| Unit-labelled capacity/load/voltage/current/battery fields | Rack labels and equipment labels are distinct |
| Dropdown controls and differently coloured cells | Coloured blocks communicate layout/category information |
| Displayed totals/percentages and an error result | Mostly a spatial inventory presentation, not a conventional row table |

The precise formula definitions, validation lists, protection, conditional-format rules, actual merged ranges, native date types/locales and cell mappings cannot be established from the videos. Multi-row visual blocks may involve merged ranges; inspect the native workbook to confirm.

The earlier supplied instructions say gray cells are editable. Treat that as template guidance, then verify allowed destinations and native rules. Colour alone is not an authorization mechanism.

## Proposed mapping approach

Support separate template adapters that share stable asset/field identity:

| Record/context | Audit-form destination | Rack/RU destination |
| --- | --- | --- |
| Site/room | Relevant facilities section | Correct site tab/rack group |
| Equipment identity/type | Appropriate equipment slot and fields | Correct rack block/label |
| Manufacturer/model/serial | Named equipment fields | Optional linked record/detail, if the layout supports it |
| Rack position and occupied RU range | Relevant cabinet/rack field if defined | Rack identity plus RU start/end |
| Rating or displayed reading | Correct quantity field and units | Linked equipment data rather than arbitrary block text |
| Review/verification status | App review state and explicit approved destinations | App review state; preserve the sheet's category legend |

Do not assume every audit field has a rack-diagram equivalent, or that an unused equipment slot represents an installed asset.

Define whether approved information updates one or several workbook views of the same equipment. That cross-workbook mapping has not been selected.

## What capture-assisted Gemini can propose

- Readable manufacturer/model/serial and visible asset labels.
- Explicit nameplate ratings with units and AC/DC context.
- Visible component labels and timestamped display readings.
- Candidate rack/equipment matching when capture context is known, subject to verification.

The scan alone does not establish installation/replacement history, historical maximum phase loads, runtime tests, grounding verification, arc-flash-study completion, maintenance contacts or unseen equipment.

Do not replace a missing input with zero, convert a manufacturing date to an installation date, treat nameplate capacity as live load, or infer AC service measurements from a DC screen. Preserve the source and uncertainty.

## Preserve workbook behavior

The native Google Sheets cell model separates entered values/formulas, computed values, formats and validation. Inspect these before designing writes:
[Google Sheets cell data](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/cells).

Candidate adapter requirements:
- Target configured editable input cells/ranges.
- Preserve formulas and let the workbook calculate derived results.
- Preserve dropdown validation and destination number/date formatting.
- Keep quantities such as VA/kVA, W, A, V and Ah distinct.
- Preserve repeated-block and rack/RU layout semantics.
- Respect protection, permissions and conflict/retry rules.
- Preview structural changes that could alter a form or occupied RU span.
- Avoid treating all red/green cells as universal status indicators; the rack sheet explicitly uses colour for category.
- Clarify blank, no-rack and open-rack meanings with the workbook owner before mapping them to one inventory state.

These are design requirements to implement/test, not verified behavior.

## Confirmed AI write gate

Arlen selected option 1: Gemini creates draft entries/updates during capture, and designated editors approve before live spreadsheet writes.

A proposed review panel shows current/proposed values, units, location, source evidence and destination. Correction/rejection should leave live data unchanged until an authorized approved operation is applied. Exact review/batch/conflict UI remains open.

This does not add a separate approval gate to ordinary manual editing already permitted by the product's role and synchronization rules.

## Next implementation evidence

Use synthetic copies of both layout families for the demo. Before real cell binding, inspect an authorized native Sheet or .xlsx copy to obtain formulas, ranges, slot identities, types, validation, protection and any merged ranges.

The videos are enough to guide adapter design but are not an executable mapping specification. No real workbook access or write occurred in this review.

See [spreadsheet sync](SPREADSHEET_SYNC.md), [AI capture inventory](AI_CAPTURE_INVENTORY.md), [test plan](TEST_PLAN.md) and [developer handoff](HANDOFF.md).
