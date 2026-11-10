# Development log

Record actual work and evidence. Separate user decisions, AI assistance, mock behavior and tested outcomes. This is a project record, not a claim that assistants share memory or credentials.

## November 10, 2026 — requirements and GitHub foundation

Human contribution:
- Arlen supplied the product purpose, platforms, editing/navigation requirements and production/demo access requirements.
- Arlen selected designated production editors, equipment templates and record-local field changes.
- Arlen added bidirectional spreadsheet values and structural changes as a requirement.
- Arlen created VR-HE/VR-HE and completed GitHub authorization.

AI contribution:
- ChatGPT/Codex assisted requirements discovery and account troubleshooting.
- ChatGPT/Codex organized the previously maintained product brief into the repository specification.
- ChatGPT/Codex prepared the initial README, shared agent instructions, architecture notes, decision record, sync requirements, test plan and developer handoff.
- No Claude Code contribution to this repository has been verified in this session.

Verified repository evidence:
- Authenticated account: VR-HE.
- Repository visibility: private.
- Repository permissions include read and write.
- Baseline main commit: d731a368d7121f31d248446f7feac04ddb6e6e06.
- Baseline root files: README.md and .gitignore.
- The README was GitHub's starter profile template; .gitignore was the Unity template.
- Existing Unity ignore rules are retained; explicit project-local private-data and environment-file exclusions are added.

Implementation status:
- Documentation foundation only.
- No Unity project, application code, rendering/capture integration, backend, spreadsheet adapter, authentication enforcement or device build.
- No operational captures or actual company spreadsheet data were committed.
- No application or dependency license has been selected.

Validation:
- Static documentation validation passed: 11 files were inspected, 21 internal Markdown links resolved, and the existing Unity ignore-rule prefix matched its original Git blob hash.
- Requirement/status review found no remaining pending-account-authorization instructions in the new documentation.
- No Unity build, runtime, headset, phone or browser compatibility test has been performed.
- Publication uses a separate documentation branch and pull request. See GitHub history for the actual commit and integration state.

## November 10, 2026 — Google requirements, site updates and guidance

Human contribution:
- Arlen supplied terminal output showing Git 2.43.0 and successful installation of gh package 2.45.0-1ubuntu0.3 on the Linux laptop.
- Arlen required Google Drive, Sheets and Gemini compatibility and control of approved/unapproved AI and spreadsheet integrations, with ChatGPT/Claude and Excel/OpenOffice as named extensions.
- Arlen required tour updates for site changes, targeting partial rescans where feasible.
- Arlen required in-app instructions for scanning, editing, navigation and accessing information, explained for non-gamers.
- Arlen specified browser Q up, E down, X center and full VR 6DoF.

AI contribution:
- ChatGPT/Codex updated the specification, decisions, contributor instructions, architecture, synchronization notes, acceptance plan and handoff.
- ChatGPT/Codex documented integration-policy boundaries, a proposed partial-update approach and built-in user guidance.
- ChatGPT/Codex checked primary Google API, OpenOffice API, GitHub CLI and SplaTAM research sources. Incremental Gaussian mapping research is not proof of reliable partial updates on the requested hardware.

Open points:
- X center semantics, Gemini functions/data permissions and integration-approval roles.
- Partial-rescan registration/replacement method and quality, plus rendering/device feasibility.
- Local VR-HE authentication, repository checkout and Claude Code access.
- No API credential, real workbook or operational capture has been connected.

Validation:
- Static documentation validation passed: 14 files, 39 resolved internal Markdown links, no table-structure errors, and original Unity ignore rules preserved.
- The prior spreadsheet-platform question was removed from active handoff/specification instructions; Google compatibility is confirmed.
- Application code, runtime integrations and device testing remain absent.

## November 10, 2026 — controls follow-up and local sign-in

Human contribution:
- Arlen required arrow-key desktop browser movement in addition to WASD.
- Arlen required mobile FPS/third-person movement/look, first-/third-person switching and separate camera-height up/down controls.
- Arlen required third-person look/orbit around the avatar.
- Arlen confirmed X restores BOTH normal camera height and a level viewing angle.
- Arlen's terminal screenshot confirms completed GitHub CLI authentication as VR-HE and a local account lookup returning VR-HE. He selected Git credential configuration during login. No authentication code, credential or device identifier is recorded here.

AI contribution:
- ChatGPT/Codex updated requirements, decisions, user-guide/input notes, acceptance checks and handoff.
- Arrow directions are interpreted as equivalents to WASD. The familiar left-movement/right-look mobile layout is a proposal; exact UI and orbit/follow settings remain open.
- ChatGPT/Codex reviewed the screenshot; it did not run commands on the user's laptop.

Validation:
- Documentation validation passed: 14 files, 39 resolved internal Markdown links and no table-structure errors.
- Local repository checkout/access and Claude Code use remain unverified.
- No application code, runtime control testing or physical device tests were performed.

Earlier log entries record the open points at their respective checkpoints; current decisions are in DECISIONS.md.

## Entry template

For each meaningful change, record:
- Date and concrete behavior/problem.
- Human decisions and actual contributors/assistants.
- Files/modules changed and relevant decision IDs.
- Commands or checks run and observed results.
- Untested assumptions, failures, risks and next work.

Use commit and pull-request history for exact revision IDs. Do not claim future tests as completed.
