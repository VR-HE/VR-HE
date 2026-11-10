# Developer and assistant handoff

Updated November 10, 2026.

## Current state

VR-HE/VR-HE is the selected private repository. ChatGPT/Codex is authenticated as VR-HE with read and write permissions. Initial documentation is prepared on docs/project-foundation; check the pull request for whether it has been merged.

The baseline main commit before this documentation change is d731a368d7121f31d248446f7feac04ddb6e6e06. Consult GitHub history for the current head; a document cannot reliably name its own final commit in advance.

There is no Unity project or runnable demo yet. No rendering, capture, backend, sync or security implementation exists. No hardware compatibility has been tested. Arlen's supplied laptop output confirms Git 2.43.0 and successful installation of the gh 2.45.0 Ubuntu package. Arlen supplied a screenshot confirming completed local authorization and account lookup as VR-HE. His subsequent screenshot confirms a successful clone into /home/arlen/Projects/VR-HE, docs/project-foundation tracking origin/docs/project-foundation, and no working-tree changes. Arlen's screenshot shows Claude Code v2.1.321, Opus 5.5 with max effort, and ~/Projects/VR-HE. This confirms the displayed session configuration. Claude Code's November 10 local inspection recorded the installed Unity tooling below; no Unity project was created or changed.

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

Local VR-HE sign-in, clone, the Claude session configuration and the local Unity inventory are complete. The working branch is docs/project-foundation. Next, Arlen approves or changes the recommended Unity version and template below; then run the project-creation task from a clean tree after a fast-forward pull. He answered Yes to Git credential configuration during login; do not repeat authentication solely to change that answer. Do not assume commands in a cloud workspace ran on his laptop.

Authentication and repository read access are confirmed. Claude Code pushed the inspection's documentation commit from the laptop: if that commit is on origin/docs/project-foundation, local push access works. Local commits use the repository-local Git identity VR-HE with the account's GitHub noreply address, as Arlen chose on November 10. Do not paste passwords, tokens or login codes into chat.

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

The November 10 screenshot completes the current startup checkpoint: v2.1.321, Opus 5.5, max effort, correct project folder. The inspection session confirmed it locally: the process was started as claude --effort max, with CLAUDE_CODE_EFFORT_LEVEL=max, from the 2.1.321 binary. Claude Code then updated itself on disk to 2.1.322, and Opus 5.5 was selected for that session only. At the next start, select Opus 5.5 again and re-check version and effort. If a session shows a lower level, resolve and record the difference.

References: [model/effort configuration](https://code.claude.com/docs/en/model-config), [CLI reference](https://code.claude.com/docs/en/cli-reference).

## Local Unity inspection — November 10 findings

Claude Code completed [the inspection task](LOCAL_UNITY_INSPECTION.md) with read-only checks. Installed files and Hub/CLI metadata are installation evidence only. No Editor was launched, nothing was built, and no device, browser or splat renderer was tested.

Verified on Arlen's laptop:
- Unity Hub 3.22.6 (apt package unityhub, /usr/bin/unityhub) and Unity CLI 1.0.0-beta.13 (~/.local/bin/unity).
- Editors are installed at ~/Unity/Hub/Editor/VERSION/Editor/Unity:

| Editor | Hub label | Android: SDK, NDK r27c, OpenJDK 17 | Web | Newer patch listed |
| --- | --- | --- | --- | --- |
| 6000.0.84f1 | Unity 6.0 | Files present | Not installed | 6000.0.85f2 |
| 6000.3.15f1 | Unity 6.3 LTS | Files present | Files present | 6000.3.28f1 |
| 6000.6.2f1 | Unity 6.6 | Not installed | Files present | 6000.6.8f1 |
| 6000.6.4f1 | Unity 6.6 | Files present | Not installed | 6000.6.8f1 |

- 6000.3.15f1 is the only installed editor with both Android and Web support. No editor has iOS Build Support.
- No Android or Quest device was attached to adb. The disk had 24 GB free (95% used); the 6000.3.15f1 install alone uses 27 GB.

Bridges and existing projects:
- Claude Code has no MCP servers configured for the user, VR-HE or any other project; Claude Desktop has none. The installed Unity plugin for Claude Code (unity@unity-agent-plugin 0.1.9-beta) provides skills only and drives editors through the unity CLI.
- unity status reports one running Editor: The Veil (6000.6.4f1, /home/arlen/Desktop/The Veil (Unity)/The Veil), Pipeline state ready. A Unity AI Assistant MCP relay from The Veil's packages is attached to the same Editor; its MCP client port 9002 listens on all network interfaces. At inspection time another Claude Code session was working in The Veil's folder.
- VR-HE has no Unity project, so it has no bridge target yet. Fourteen existing Unity projects were found outside this repository; none was modified.
- Never send unity command or MCP requests to The Veil's Editor. Open VR-HE's own project in its own Editor and pass its full path with --project-path on every Editor command.

Recommendation, pending Arlen's approval:
- Create the first prototype with the installed Unity 6.3 LTS editor (6000.3.15f1) and its bundled URP blank 3D template (com.unity.template.urp-blank, labeled 3D URP in its metadata). The template includes URP and the Input System.
- Add OpenXR, OpenXR Meta and the XR Interaction Toolkit when the Quest slice starts, through Unity 6.3's Meta Quest build profile. The cached 6.3 VR template's versions (OpenXR 1.17.1, OpenXR Meta 2.5.1, XR Interaction Toolkit 3.5.1) are the reference set.
- Reasons: no download is needed on a nearly full disk. Unity supports 6.3 LTS until December 2027; 6.0 LTS was supported through October 2026, and Update releases such as 6.6 are supported only until the next release. A plain URP project keeps browser and phone builds free of the VR template's XR, AR and hand-tracking packages and its VR-only rig.
- Unity's guidance is mixed: its support page prefers Update releases for new productions, while its 6.3 LTS announcement recommends 6.3 for them. If Arlen wants to start with Quest, the cached 6.3 VR template (10.0.0) is the alternative.

Untested assumptions and risks:
- Browser: Unity 6.3 labels WebGPU experimental; Unity 6.6 says it is out of experimental release. Neither enables WebGPU automatically. The aras-p/UnityGaussianSplatting README names D3D12, Metal and Vulkan as the only known-working graphics APIs, says mobile/web are not tested and says WebGPU "might work someday". Treat the browser path as the highest-risk target. If 6.3's experimental WebGPU blocks it, retest on a newer release before changing the version decision.
- Phone and Quest in one project: Unity 6.3's Meta Quest build profile shares Android Player settings and can override Player, Graphics and Quality settings. The docs do not say XR plug-in settings can differ per profile, so test an Android phone profile without XR beside the Quest profile.
- Quest 2: Unity 6.3 lists Quest 2, 3, 3S and Pro for development, but the splat README reports only Quest 3 and Quest Pro among Quest headsets.
- iPhone: native builds need iOS Build Support plus a Mac with Xcode, or Unity Build Automation. No Mac is known to be available.
- The splat candidate is MIT-licensed, and its author plans no significant further development (README, November 2026). It remains a candidate, not a selection.

Before creating the project:
- Get Arlen's approval of the version and template.
- Choose the project folder inside this repository; the Hub's default new-project folder is elsewhere. The existing Unity ignore rules are anchored to the repository root (for example `/[Ll]ibrary/`), so create the Unity project at the root or put a copy of those rules in the project folder.
- Decide whether VR-HE includes the Unity AI Assistant (pre-release) and Unity CLI Pipeline (experimental) packages. The Hub's saved preferences and recent project manifests suggest it adds both to new projects. Claude needs the Pipeline package to drive the VR-HE Editor through the unity CLI.
- Free disk space before installing another editor or making Android/Web builds.

Sources: [Unity 6 support](https://unity.com/releases/unity-6/support), [Unity 6.3 WebGPU limitations](https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/webgl/develop/graphics/web-gpu/limitations), [What's new in Unity 6.6](https://docs.unity.com/en-us/engine/6000.6/manual/whats-new/unity66), [Unity 6.3 Meta Quest packages and templates](https://docs.unity.com/en-us/engine/6000.3/manual/xr/configuring-project-for/meta-quest-develop/packages), [Unity 6.3 build-profile overrides](https://docs.unity.com/en-us/engine/6000.3/manual/building-and-publishing/build-settings/build-profiles-override-settings), [Unity 6.3 iOS setup](https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/iphone/getting-started/ios-environment-setup), [UnityGaussianSplatting README](https://github.com/aras-p/UnityGaussianSplatting).

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
- No Unity version, renderer, backend or capture processing location is selected. Unity 6.3 LTS with the URP blank 3D template is recommended, pending Arlen's approval.
- No Android reference device or performance/quality acceptance threshold is selected.
- Arrow/WASD movement, Q/E/X reset, mobile movement/look/view/height controls, third-person orbit and VR 6DoF are confirmed. Exact touch/controller layout, camera-height reference, orbit/follow rules, comfort, avatar dimensions and scale verification remain open.
- Gemini drafts and designated editors approve before live writes. Field scope, review UI, Google contracts, additional provider scope and integration-administration roles remain open.
- Spreadsheet videos establish visible layouts only. Exact formulas, validation, protection, merged ranges and cell mappings have not been inspected in native workbooks.
- Cabinet states require a registration/segmentation/visibility prototype; local state persistence and setup/inspection permissions still need design.
- Partial rescanning is a required feasibility target, not a tested feature.
- Data types, attachment formats, conflicts, deletion recovery and detailed permissions need decisions.
- No production integration, real workbook modification or scan upload has occurred.

Keep user-facing explanations plain and concise. Arlen prefers a step-by-step interview and practical instructions he can follow without being an experienced developer.
