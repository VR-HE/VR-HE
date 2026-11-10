# First local Unity inspection task

Prepared November 10, 2026. Startup evidence: Claude Code v2.1.321, Opus 5.5, max effort, ~/Projects/VR-HE. Local Unity facts are not yet known.

Paste the following into the existing Claude session. It preserves the session-only model choice while refreshing repository documents.

## Prompt

Continue this VR-HE session using Opus 5.5 with MAX effort.

Check the current folder, Git branch, remote and working tree. If the working tree is clean, run git pull --ff-only. Preserve any existing changes and report conflicts without resetting or stashing them.

Read CLAUDE.md, AGENTS.md, docs/PRODUCT_SPEC.md, docs/DECISIONS.md and docs/HANDOFF.md.

Inspect the local Unity setup using read-only checks:
1. Installed Unity Hub and Unity Editor versions, with their paths.
2. Installed Android and Web build-support modules; distinguish files found from successfully tested builds.
3. Available Unity bridge/MCP tools and the project each connection targets. Preserve The Veil and other existing projects; keep credentials out of reports.

Report observed facts, missing pieces and untested assumptions separately. Recommend a starting Unity template for a small VR-HE prototype targeting browser, phone and Quest, checking current primary documentation for compatibility claims. Treat splat-renderer compatibility as unproven until tested.

Record concise findings in docs/HANDOFF.md and docs/DEVELOPMENT_LOG.md. Commit and push only those documentation changes to the current project branch if permitted by the current repository state. Report the commit or any access failure.

This task inventories the environment and records findings; Unity project creation is the next task.

## Expected handoff

Return the observed Unity versions/paths and module evidence, bridge targets, recommended first template with assumptions, missing setup items, and documentation commit/push result. Do not claim a build or renderer test from installation metadata alone.
