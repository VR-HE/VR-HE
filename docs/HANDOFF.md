# Developer and assistant handoff

Updated November 10, 2026.

## Current state

VR-HE/VR-HE is the selected private repository. ChatGPT/Codex is authenticated as VR-HE with read and write permissions. Initial documentation is prepared on docs/project-foundation; check the pull request for whether it has been merged.

The baseline main commit before this documentation change is d731a368d7121f31d248446f7feac04ddb6e6e06. Consult GitHub history for the current head; a document cannot reliably name its own final commit in advance.

There is no Unity project or runnable demo yet. No rendering, capture, backend, sync or security implementation exists. No hardware compatibility has been tested. Arlen's supplied laptop output confirms Git 2.43.0 and successful installation of the gh 2.45.0 Ubuntu package. Arlen supplied a screenshot confirming completed local authorization and account lookup as VR-HE. His subsequent screenshot confirms a successful clone into /home/arlen/Projects/VR-HE, docs/project-foundation tracking origin/docs/project-foundation, and no working-tree changes. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration; local Unity tooling and push access still need verification.

## Read in this order

1. [Shared instructions](../AGENTS.md)
2. [Product specification](PRODUCT_SPEC.md)
3. [Confirmed decisions](DECISIONS.md)
4. [Spreadsheet synchronization](SPREADSHEET_SYNC.md)
5. [Proposed architecture](ARCHITECTURE.md)
6. [Test plan](TEST_PLAN.md)
7. [Integration controls](INTEGRATIONS.md)
8. [Capture updates](CAPTURE_UPDATES.md)
9. [Built-in user guide plan](USER_GUIDE_PLAN.md)
10. [Development log](DEVELOPMENT_LOG.md)
11. [Cabinet inspection states](CABINET_STATES.md)
12. [AI-assisted capture inventory](AI_CAPTURE_INVENTORY.md)
13. [Supplied spreadsheet examples](SPREADSHEET_EXAMPLES.md)

The earlier ISP_Virtual_Tour_Product_Brief.md informed this baseline. The repository specification is now the maintained project source of truth; do not maintain competing copies.

## Next setup work

Local VR-HE sign-in, clone and the displayed Claude session are confirmed by Arlen's screenshots. Claude Code v2.1.321 shows Opus 5.5 with max effort in ~/Projects/VR-HE; the model was selected for this session only. The working branch is docs/project-foundation. Next run the [local Unity inspection task](LOCAL_UNITY_INSPECTION.md) in that existing session, beginning with a clean-tree check and a safe fast-forward pull. He answered Yes to Git credential configuration during login; do not repeat authentication solely to change that answer. Do not assume commands in a cloud workspace ran on his laptop.

Authentication and repository read access are confirmed. Claude's displayed configuration is confirmed. Local Unity versions/modules, bridge target and local push access are the next verification steps. Do not paste passwords, tokens or login codes into chat.

If this documentation branch is still unmerged, read/check out the branch when continuing; do not mistake the starter README on main for the full project.

## MAX effort for Claude build work

Arlen explicitly requires MAX effort. The [launcher](../scripts/start-claude.sh) sets a process-scoped effort request and starts Claude in this repository.

For later sessions:
1. Pull the latest working branch with git pull --ff-only.
2. Check claude --version.
3. Run bash scripts/start-claude.sh.
4. Check the active model/effort control, using /model or /effort, before starting build work.
5. Record the observed version, model and actual effort.

The current Claude Code docs support session launch requests and a process environment setting; they do not accept max as a persisted effortLevel value. The client/model can reduce an unsupported request, so a successful launch alone does not prove MAX.

The November 10 screenshot completes the current startup checkpoint: v2.1.321, Opus 5.5, max effort, correct project folder. Do not repeat this setup unless the session/configuration changes. If a later session shows a lower level, resolve and record the difference.

References: [model/effort configuration](https://code.claude.com/docs/en/model-config), [CLI reference](https://code.claude.com/docs/en/cli-reference).

## Immediate local inspection

Use [the first task prompt](LOCAL_UNITY_INSPECTION.md) to gather installed Unity Editor versions, Android/Web build support and available Unity bridge targets. Record facts separately from recommendations, then select the project template and renderer feasibility experiment. Environment inspection can proceed independently of acquiring native spreadsheets.

## Next mapping work

AI write policy is resolved: Gemini creates drafts; designated editors approve AI-generated entries and updates before live spreadsheet writes. The supplied videos establish facilities-audit and rack/RU mapping targets. Use synthetic examples for the demo and inspect an authorized native workbook/copy before binding real cells. X is resolved: restore both normal camera height and level viewing angle. Q raises and E lowers the viewpoint.

Google Drive, Google Sheets and Gemini compatibility is now required. Do not reopen whether Google Sheets is required. Follow-up decisions are inventory field scope, allowed data/actions, integration-approval roles, workbook organization/mapping and synchronization policies.

Also confirmed: desktop arrow-key movement in addition to WASD, mobile FPS/third-person movement/look/view switching and separate height controls, third-person orbit around the avatar, policy-controlled additional integrations, updateable tours, partial rescanning where feasible, built-in guidance and full VR 6DoF. See the linked design notes. Ask one primary question at a time and record confirmed answers.

## Early implementation work to scope

After the necessary choices are made:
- Select/pin a Unity version and establish the project layout.
- Test renderer feasibility with a small representative scene on the weakest required devices and browser path.
- Build a small synthetic runtime-editing example with durable record identity.
- Prototype Google Sheets synchronization against synthetic audit-form and rack/RU layouts using the confirmed AI approval gate. Preserve formula/validation/format semantics.
- Prove partial-rescan alignment/replacement using a small changed section.
- Design provider approval enforcement and Gemini capabilities before connecting real data.
- Include novice-friendly guidance with the implemented workflows.
- Prototype a cabinet with aligned closed/open appearance and separate door/interior record anchors.
- Prototype Gemini extraction from synthetic/authorized label frames; evaluate transcription and asset matching before live writes.
- Keep production access enforcement as a separate explicit workstream with acceptance evidence.

These are proposed stages, not a promise that every device has a compatible renderer or that capture/training can run on every viewing device.

## Start prompt for a coding assistant

Read AGENTS.md, this handoff, PRODUCT_SPEC.md and DECISIONS.md before editing. Report the actual repository state and current branch. Preserve confirmed requirements and identify open choices. Use verified MAX effort for Claude build work. Continue the assigned small task, record human/AI contributions and test evidence, and leave a concrete handoff. Do not claim unrun device tests, infer shared credentials or silently redefine confirmed Google requirements, X semantics, AI powers or the renderer.

## Current limitations

- Application license and third-party dependencies are undecided.
- No Unity version, renderer, backend or capture processing location is selected.
- No Android reference device or performance/quality acceptance threshold is selected.
- Arrow/WASD movement, Q/E/X reset, mobile movement/look/view/height controls, third-person orbit and VR 6DoF are confirmed. Exact touch/controller layout, camera-height reference, orbit/follow rules, comfort, avatar dimensions and scale verification remain open.
- Gemini drafts and designated editors approve before live writes. Field scope, review UI, Google contracts, additional provider scope and integration-administration roles remain open.
- Spreadsheet videos establish visible layouts only. Exact formulas, validation, protection, merged ranges and cell mappings have not been inspected in native workbooks.
- Cabinet states require a registration/segmentation/visibility prototype; local state persistence and setup/inspection permissions still need design.
- Partial rescanning is a required feasibility target, not a tested feature.
- Data types, attachment formats, conflicts, deletion recovery and detailed permissions need decisions.
- No production integration, real workbook modification or scan upload has occurred.

Keep user-facing explanations plain and concise. Arlen prefers a step-by-step interview and practical instructions he can follow without being an experienced developer.
