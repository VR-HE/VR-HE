# Gemini-assisted inventory during capture

Status: desired capability and proposed design, November 10, 2026. No live Gemini or spreadsheet integration exists.

## Requested outcome

While a person records the Gaussian tour, Gemini assists with much of the baseline equipment information/spreadsheet recording.

Google documents video understanding and structured responses. These are building blocks, not demonstrated headend transcription accuracy or proof of continuous real-time performance on the requested phones/Quest devices.

## Proposed workflow

1. Associate capture with a site/room/rack/cabinet context.
2. Select readable source frames or close-up images while recording continues.
3. Process candidate labels/visible information asynchronously through an approved Gemini integration.
4. Produce typed candidate fields with asset/location context, source image/crop, capture time and processing status.
5. Apply the chosen review/write policy before synchronizing to Google Sheets.
6. Retry/reconcile safely without duplicate records.

Selected close-up frames are a proposed implementation; continuous live video analysis is not a selected requirement or proven path. Define acceptable lag and what can complete after recording.

## Candidate fields

Examples for the field-scope discussion:
- Equipment type and visible asset/panel identifier.
- Manufacturer, model and serial.
- Explicitly visible nameplate voltage/current/power ratings with units and AC/DC context.
- Visible component labels and separately timestamped displayed readings.

Do not infer an installation year, maximum historical current, service rating or live load from appearance/model guesses. A nameplate rating and a transient screen reading are different data.

Unknown/unreadable fields should remain unknown and be easy to correct. A zero is a value, not a substitute for missing data. Schema-valid output does not establish that a number or serial is correct.

If confidence indicators are used, they need empirical calibration; model self-reported confidence is not a verified probability.

## Evidence and identity

Link each candidate to its supporting source and context. Do not use manufacturer/model text alone to distinguish identical equipment.

Closed/open cabinet passes, repeated video frames and partial rescans require duplicate handling. Distinguish outer-door, inner-door and fixed interior information. A hidden/unseen device is not an automatic deletion.

Do not overwrite a verified record merely because a new frame is blurred or differently labeled. Follow the confirmed record-local field/template and spreadsheet structural-change rules.

## Review and write authority — decision pending

Recommendation: draft candidate rows/fields during capture and have a designated editor confirm them before writes to the live spreadsheet.

Arlen has not yet chosen draft-review versus direct writing. Exact allowed fields/actions, correction/history, automation limits and sheet permissions remain open. Do not treat this recommendation as a user-selected mandatory approval workflow.

All integration activity must respect provider approval, application roles and production company-network/password requirements. Define capture/job behavior on connection loss. No real company data or credentials are authorized by this design note alone.

## Prototype evidence

Use representative synthetic/authorized labels with independently checked ground truth. Measure field accuracy, missing fields, incorrect asset matches, duplicate rate, correction effort, latency and capture impact.

Test small text, glare, motion blur, obscured labels, similar devices and inconsistent units. Set acceptance criteria with Arlen. No percentage of work saved or error rate has been established.

## Primary references

- [Gemini video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google Sheets batch updates](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate)

See [integration policy](INTEGRATIONS.md), [spreadsheet sync](SPREADSHEET_SYNC.md), [cabinet states](CABINET_STATES.md) and [test plan](TEST_PLAN.md).
