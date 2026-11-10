# Developer and assistant handoff

Updated November 10, 2026.

## Current state

VR-HE/VR-HE is the selected private repository. ChatGPT/Codex is authenticated as VR-HE with read and write permissions. Initial documentation is prepared on docs/project-foundation; check the pull request for whether it has been merged.

The baseline main commit before this documentation change is d731a368d7121f31d248446f7feac04ddb6e6e06. Consult GitHub history for the current head; a document cannot reliably name its own final commit in advance.

There is no Unity project or runnable demo yet. No rendering, capture, backend, sync or security implementation exists. No hardware compatibility has been tested. Arlen's supplied laptop output confirms Git 2.43.0 and successful installation of the gh 2.45.0 Ubuntu package. Local VR-HE authentication/repository access is still unverified.

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

The earlier ISP_Virtual_Tour_Product_Brief.md informed this baseline. The repository specification is now the maintained project source of truth; do not maintain competing copies.

## Next setup work

Guide Arlen through VR-HE sign-in using the installed GitHub CLI on his Linux laptop, then verify local repository access and checkout. Installation is confirmed by user-supplied terminal output; authentication is not. Do not assume commands in a cloud workspace ran on the user's laptop. Preserve his other project's Git configuration.

Use GitHub's ordinary interactive browser sign-in. Verify the intended account, remote and repository access. Do not paste passwords, tokens or login codes into chat. ChatGPT authentication does not authenticate Claude Code.

If this documentation branch is still unmerged, read/check out the branch when continuing; do not mistake the starter README on main for the full project.

## Next primary product question

Clarify what browser X should recenter: viewing angle, camera height, both, or another intended meaning. Q raises and E lowers the viewpoint; those bindings are confirmed.

Google Drive, Google Sheets and Gemini compatibility is now required. Do not reopen whether Google Sheets is required. Follow-up decisions are Gemini functions and allowed data/actions, integration-approval roles, workbook organization/mapping and synchronization policies.

Also confirmed: policy-controlled additional AI/spreadsheet integrations, updateable tours, partial rescanning where feasible, built-in plain-language guidance and full VR 6DoF. See the linked design notes. Ask one primary question at a time and record confirmed answers.

## Early implementation work to scope

After the necessary choices are made:
- Select/pin a Unity version and establish the project layout.
- Test renderer feasibility with a small representative scene on the weakest required devices and browser path.
- Build a small synthetic runtime-editing example with durable record identity.
- Prototype Google Sheets synchronization against synthetic data with the chosen mapping.
- Prove partial-rescan alignment/replacement using a small changed section.
- Design provider approval enforcement and Gemini capabilities before connecting real data.
- Include novice-friendly guidance with the implemented workflows.
- Keep production access enforcement as a separate explicit workstream with acceptance evidence.

These are proposed stages, not a promise that every device has a compatible renderer or that capture/training can run on every viewing device.

## Start prompt for a coding assistant

Read AGENTS.md, this handoff, PRODUCT_SPEC.md and DECISIONS.md before editing. Report the actual repository state and current branch. Preserve confirmed requirements and identify open choices. Continue the assigned small task, record human/AI contributions and test evidence, and leave a concrete handoff. Do not claim unrun device tests, infer shared credentials or silently redefine confirmed Google requirements, X semantics, AI powers or the renderer.

## Current limitations

- Application license and third-party dependencies are undecided.
- No Unity version, renderer, backend or capture processing location is selected.
- No Android reference device or performance/quality acceptance threshold is selected.
- Q/E/X browser bindings and VR 6DoF are confirmed; X meaning, touch/controller traversal, comfort settings, avatar dimensions and scale verification remain open.
- Google API/data contracts, Gemini functions, additional provider scope and approval roles remain open.
- Partial rescanning is a required feasibility target, not a tested feature.
- Data types, attachment formats, conflicts, deletion recovery and detailed permissions need decisions.
- No production integration, real workbook modification or scan upload has occurred.

Keep user-facing explanations plain and concise. Arlen prefers a step-by-step interview and practical instructions he can follow without being an experienced developer.
