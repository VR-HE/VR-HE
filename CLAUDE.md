# Claude Code entry point

Read and follow [AGENTS.md](AGENTS.md), then [docs/HANDOFF.md](docs/HANDOFF.md).

**Build work requires MAX effort.** Use [the project launcher](scripts/start-claude.sh), then verify the active model/effort before implementation. The launch request is not proof the backend accepted MAX.

The shared specification is [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md). Confirmed decisions are in [docs/DECISIONS.md](docs/DECISIONS.md). Record actual work and validation in [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md).

Current state: requirements, developer setup and a rendering-only browser prototype (branch proto/browser-splat-rendering); no VR-HE application and no tested phone/Quest or minimum-Toughbook support. ChatGPT/Codex repository access is verified. Arlen's screenshot confirms local VR-HE sign-in, repository clone on docs/project-foundation and a clean working tree. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration. Claude's November 10 inspection verified the installed Unity tooling; installed tools are not tested functionality. Local push access is verified by commit ff1e070 on origin/docs/project-foundation. The prepared bundle completed Edge/Chrome baselines on Arlen's personal Windows 11 PC; the reviewed 30 Hz and 60 Hz runs strongly support display pacing, with about 60 fps through 250k splats at a 1280x720 canvas. Uncapped capacity remains unmeasured. Execution on the company Toughbook still requires company authorization and is deferred (D035).

Google Drive, Sheets and Gemini compatibility, controlled additional integrations, updateable tours, built-in guidance, browser Q/E/X and VR 6DoF are confirmed requirements. X now restores both normal height and level angle. Arrow movement, mobile movement/look/view/height controls and third-person orbit are required. Partial-rescan feasibility still needs validation; read the updated handoff.

Cabinet open/closed inspection states and Gemini-assisted baseline inventory during capture are requested. Read the new design notes and preserve the confirmed draft-then-designated-editor-approval policy for AI-generated live spreadsheet writes. Read SPREADSHEET_EXAMPLES.md in docs for the supplied video layouts and native-workbook evidence gaps.

The [local Unity inspection](docs/LOCAL_UNITY_INSPECTION.md) is complete. Unity 6.3 LTS 6000.3.15f1 with the URP blank template is approved for the initial prototype only (D031). Browser Gaussian-splat rendering is the first milestone (D032); read the handoff's results and next step before continuing. Never send Unity CLI or MCP commands to The Veil's Editor, and pass VR-HE's explicit project path to every Editor operation.

Use the same repository and shared requirements. Do not assume this file grants credentials, tool access or permission to broaden the project scope.
