# Manual Windows authoring sessions — November 11, 2026

## What this establishes

Arlen uploaded telemetry from two uses of the equipment/description demo and says he is pleased with its direction: more modification is needed, but it is the overall right idea. This is positive human feedback on the direction, not acceptance of every feature or of the provisional catalog/RU/deletion defaults.

Both captured Windows sessions ran the 250k synthetic room at a 1280x720 canvas through NVIDIA RTX 5070 Ti / ANGLE / Direct3D 11 / WebGL 2. Focused activity categories average about 60 fps, with successful equipment-creation/save events and no page-console errors. This is partial manual Windows evidence, not completion of the 17-step checklist, minimum-PC qualification or a test of the finished application.

## Provenance and review

- Input: VRHE-demo-results-20261111-105736.zip; 17,439 bytes; SHA-256 `6ec401464aabb63b186b296faa61b8909b10ae29c218c024e02ec25074d48d46`.
- Archive: 11 entries, 61,414 bytes unpacked; all CRCs pass. Seven JSON documents and two JSONL console streams parse.
- Build identifiers agree: `interactive-demo-4f4f9ac2fd78-20261111T144938Z`, source `4f4f9ac2fd786274c276b90f3627c27e0d921fa8`, reported clean source.
- Both client reports show Windows user agents, a 1920x1080 desktop and the RTX 5070 Ti renderer. The Edge launcher additionally records Windows 11 Home 26H2 build 26300.9974, Ryzen 7 7800X3D, 16 logical processors, 31.2 GiB native RAM report and 1920x1080 @ 60 Hz.
- The first session has a reduced Chrome/157 user agent, without a native launcher record. The exact browser product/full version is not proven by that user agent. The second session is tied to the native Edge 157.0.4341.42 launcher record.
- All 17 reported pacing buckets satisfy FPS = frames / seconds and mean interval = seconds / frames. No raw frame arrays, build binaries, screenshots or record exports are included, so this checks aggregate arithmetic and metadata rather than reconstructing frame distributions or inspecting saved text.

## Frame pacing

Focused here means all named activity categories except explicit loading/unfocused categories; it includes panel use and typing. The measured canvas is 1280x720, not the desktop resolution. Edge's native report records 60 Hz, and both sessions show an approximately 60 fps cadence. Uncapped capacity and GPU execution time are unmeasured.

| Captured session | Browser evidence | Snapshot uptime | Focused frames / seconds | Focused mean fps | Longest focused interval | Focused intervals >50 ms |
| --- | --- | --- | --- | --- | --- | --- |
| demo-20261111-104329-cd94cf | Chrome/157 family user agent; product unrecorded | 540.5 s | 31,294 / 521.582 s | 59.998 | 25 ms | 0 |
| demo-20261111-105442-73203f | Edge 157.0.4341.42 | 146.1 s | 8,650 / 144.171 s | 59.998 | 23 ms | 0 |

Each session also reports one >50 ms interval while explicitly unfocused (55 ms / 56 ms). Loading buckets contain 319 ms / 327 ms longest intervals and one >100 ms interval each. These are reported separately, not removed from the archive or described as zero stalls across the entire session. The app's 0.46/0.49 s load metric starts in Unity's Start routine and does not measure full browser/Wasm startup.

The reported percentile values use histogram-bin upper edges over approximately 1 ms timestamps; they are not more precise raw-frame timings. See [the compact metrics](summary.json) for every bucket and CPU/sort averages.

## Recorded actions and limits

| Event counter | First session | Edge session |
| --- | --- | --- |
| Rack records opened | 4 | 4 |
| Rack-note saves | 1 | 0 |
| Equipment added | 2 | 1 |
| Equipment opened | 0 | 2 |
| Equipment saves | 0 | 2 |
| View toggles | 2 | 0 |
| Names added / renamed / replaced | 0 / 0 / 0 | 0 / 0 / 0 |
| Exports | 0 | 0 |
| Save conflicts / storage errors | 0 / 0 | 0 / 0 |

The counters are captured snapshots, not a complete audit of every action. They show successful reported equipment creation and saves, but do not reveal description text, RU assignments or selected dropdown values. Zero name-operation counters do not establish whether the user tried a dropdown; they mean name creation/rename/replacement is not demonstrated by these snapshots.

The archive contains no record JSON export or browser profile. Exact old-note migration, saved values after reload/restart, cross-item text isolation and D041 rename/replacement preservation therefore remain unverified from this upload. Mouse-inversion preferences are not traced. The prior Linux automated results remain separate evidence; they are not Windows assertions.

## Logs and launcher

- Each console stream contains 55 log entries and one expected UnitySplats CPU-sort fallback warning; zero error/pageerror/unhandledrejection entries.
- HTTP responses are 20 x 200, 172 x 204 and two favicon 404s; no other failure response is recorded.
- The supplied Edge launcher record reports ready, profile kept, demo window closed and browser process exited. No corresponding first-session launcher record is included.
- The expected CPU-sort warning is consistent with the existing WebGL path; it is not evidence that missing production features work.

## Next work

Keep the implemented interaction direction and preserve the runnable demo. Ask Arlen for the first specific modification he wants next; the general positive feedback does not select a new feature or approve all prototype defaults. Keep remaining manual workflow checks explicit without claiming this is a full Windows pass.

Company Toughbook testing still requires authorization (D035). Phone/Quest, real captures, production authentication/MFA, backend and spreadsheet synchronization remain separate work. No app code, build, bundle or user data was changed during this review.
