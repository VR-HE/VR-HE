# Interactive browser demo: Linux real-browser checks, November 11, 2026

Generated from the raw `verify.json` files of `Tools/verify_interactive_demo.py` (raw results stay ignored under `TestResults/raw/interactive-demo/`). Development laptop: Linux Mint 22.3, Intel Core i7-13620H, NVIDIA RTX 4060 Laptop GPU, 1920x1200 at 60 Hz. Each run used a fresh throwaway browser profile, extracted the final Windows bundle ZIP and served it with the bundle's own `tools/demo_server.py`. Linux only: this is not Windows evidence.

| Run | Browser | Target | Canvas | Checks |
| --- | --- | --- | --- | --- |
| verify-20261111-011350-chrome | Google Chrome 157.0.8103.50 | bundle interactive-demo-294f4b21e6b1-20261111T061111Z | 1280x720 | 69 passed, 0 failed |
| verify-20261111-011612-brave | Brave 1.99.55 (Chromium 157.0.8103.39) | bundle interactive-demo-294f4b21e6b1-20261111T061111Z | 1220x686 | 67 passed, 2 failed |

## Frame pacing by activity

Frame intervals measured inside the page while the automated input ran. fps = frames / seconds. Percentiles are upper edges of 0.5 ms histogram bins over timestamps with about 1 ms browser resolution, so 60 Hz frames show as 16-17 ms samples and a 17.5 ms median; Max is the raw longest interval. CPU = Unity main-thread work per frame; sort = UnitySplats' CPU sort. The browser paces frames to the 60 Hz display (no cap is set), so these are not uncapped capacity, and no pass threshold is implied.

### Google Chrome 157.0.8103.50, canvas 1280x720 (verify-20261111-011350-chrome)

| Activity | Frames | fps | Mean ms | p95 ms | p99 ms | Max ms | >50 ms | CPU mean ms | Sort mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first.idle (3 s) | 180 | 60.0 | 16.67 | 18.0 | 18.5 | 18.0 | 0 | 8.01 | 7.13 |
| first.moving (W held 2.5 s, sliding along a rack) | 163 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 8.30 | 7.25 |
| first.height (Q held 1 s) | 72 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 8.32 | 7.39 |
| first.looking (drag) | 106 | 60.0 | 16.67 | 18.5 | 18.5 | 18.0 | 0 | 8.42 | 7.42 |
| third.orbiting (drag) | 136 | 60.0 | 16.67 | 18.5 | 18.5 | 18.0 | 0 | 8.30 | 7.30 |
| third.moving (W held 2 s) | 132 | 60.0 | 16.67 | 18.5 | 18.5 | 18.0 | 0 | 8.36 | 7.29 |
| panel.typing | 116 | 59.5 | 16.81 | 18.5 | 18.5 | 34.0 | 0 | 8.16 | 7.09 |
| panel.help open (2 s) | 120 | 60.0 | 16.67 | 18.0 | 18.5 | 18.0 | 0 | 8.45 | 7.57 |

### Brave 1.99.55 (Chromium 157.0.8103.39), canvas 1220x686 (verify-20261111-011612-brave)

| Activity | Frames | fps | Mean ms | p95 ms | p99 ms | Max ms | >50 ms | CPU mean ms | Sort mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first.idle (3 s) | 180 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 9.39 | 8.47 |
| first.moving (W held 2.5 s, sliding along a rack) | 162 | 60.0 | 16.66 | 17.5 | 18.5 | 21.0 | 0 | 8.38 | 7.35 |
| first.height (Q held 1 s) | 72 | 60.0 | 16.67 | 18.0 | 18.5 | 18.0 | 0 | 8.42 | 7.43 |
| first.looking (drag) | 106 | 60.0 | 16.66 | 17.5 | 18.5 | 18.0 | 0 | 8.67 | 7.58 |
| third.orbiting (drag) | 136 | 60.0 | 16.66 | 17.5 | 18.5 | 18.0 | 0 | 9.03 | 8.04 |
| third.moving (W held 2 s) | 132 | 60.0 | 16.67 | 18.5 | 20.5 | 30.0 | 0 | 9.58 | 8.48 |
| panel.typing | 117 | 59.5 | 16.82 | 18.0 | 19.5 | 42.0 | 0 | 8.73 | 7.63 |
| panel.help open (2 s) | 120 | 60.0 | 16.66 | 17.5 | 18.5 | 28.0 | 0 | 9.70 | 8.80 |

## Checks (Google Chrome 157.0.8103.50, verify-20261111-011350-chrome)

Trusted keyboard and mouse events from the Chrome DevTools Protocol, so Unity receives the same events as from a person. Pointer-lock motion under synthetic events is a best-effort check; a manual check is still needed.

| Result | Check | Detail |
| --- | --- | --- |
| PASS | page ready with LOCAL DEMO DATA badge |  |
| PASS | canvas renders at 1280x720 | {'width': 1280, 'height': 720, 'cssWidth': 1280, 'cssHeight': 720} |
| PASS | HUD shows canvas pixels and fps | 1280x720 px / 43 fps |
| PASS | served data/site.json is the committed site definition |  |
| PASS | site.json IDs unchanged in the running build |  |
| PASS | build-info.json is served and labelled |  |
| PASS | nothing covers the 3D view once ready (clicks reach the canvas) | clear |
| PASS | loading and error overlays are gone once ready |  |
| PASS | input gate closed while the view lacks focus |  |
| PASS | keys ignored while the view lacks focus |  |
| PASS | first click focuses the view without selecting | gate=True selected='' |
| PASS | W moves forward (about 1.3 m/s) | 0.78 m in 0.6 s |
| PASS | S moves back | -0.78 m |
| PASS | Shift doubles the speed (about 2.6 m/s) | 1.56 m vs 0.78 m |
| PASS | D steps right | 0.80 m |
| PASS | A steps left | -0.78 m |
| PASS | Up arrow moves forward | 0.78 m |
| PASS | Down arrow moves back | -0.78 m |
| PASS | Right arrow steps right like D, without turning | 0.78 m, yaw change 0.0 deg |
| PASS | Left arrow steps left like A, without turning | -0.78 m, yaw change 0.0 deg |
| PASS | racks stop the walker (proxy collision) | walked 2.13 m, feet [1.45, 0.02, -0.71] |
| PASS | Q raises the camera | +0.60 m, eye 2.20 m |
| PASS | E lowers the camera | -0.60 m |
| PASS | drag right/down turns right and looks down (0.15 deg/px) | yaw 24.0, pitch 9.0 |
| PASS | a drag does not select |  |
| PASS | X restores normal height and a level view (first person) | before offset -0.60, pitch 9.0; after offset 0.000, pitch 0.000, eye 1.600 |
| PASS | Rack A1 is straight ahead from the front aisle | {'visible': True, 'unityX': 631.243896484375, 'unityY': 53.177581787109375, 'clientX': 669.243896484375, 'clientY': 715.8692932128906} |
| PASS | hovering A1 highlights it (white outline) | rec-9040bad6-d264-4969-b923-a7df2cba2e93 |
| PASS | click selects A1 (cyan outline, label) | selected=rec-9040bad6-d264-4969-b923-a7df2cba2e93 tag=True |
| PASS | right-click opens A1's record with name and stable ID | rec-9040bad6-d264-4969-b923-a7df2cba2e93 / ['anc-836007b1-09cd-41f9-82e8-52da9a18fe75'] |
| PASS | record shows original demo text before any edit |  |
| PASS | panel open closes the input gate | gate=False typing=True |
| PASS | typing W A S D Q E X V in the description moves nothing | moved 0.00000 m, view first->first |
| PASS | typed text arrived in the editor |  |
| PASS | Ctrl+Enter saves A1 (version 1) | {'status': 'Saved', 'message': 'Saved in this browser profile (revision 1).', 'recordId': 'rec-9040bad6-d264-4969-b923-a7df2cba2e93', 're... |
| PASS | storage holds A1's text under its recordId only | keys ['rec-9040bad6-d264-4969-b923-a7df2cba2e93'] |
| PASS | Esc closes the panel and returns focus to the view | unity-canvas gate=True |
| PASS | movement works again after closing the panel | 0.78 m in 0.6 s |
| PASS | Rack B1 is straight ahead from the back aisle | {'visible': True, 'unityX': 677.4411010742188, 'unityY': 62.73150634765625, 'clientX': 715.4411010742188, 'clientY': 706.3153686523438} |
| PASS | hovering B1 highlights it |  |
| PASS | click selects B1 (a second, different item) |  |
| PASS | Enter opens the selected record (B1) |  |
| PASS | B1 still has its own original text |  |
| PASS | Save button saves B1 |  |
| PASS | reopening A1 shows A1's saved text, not B1's |  |
| PASS | Esc with unsaved text asks before discarding |  |
| PASS | Esc on the question keeps editing |  |
| PASS | discarding closes without saving |  |
| PASS | Equipment list 'Show' selects B3 and turns the view toward it | projected x 640 of 1280 |
| PASS | page reload keeps Rack A1's saved text |  |
| PASS | page reload keeps Rack B1's saved text |  |
| PASS | export is labelled local demo data with schema |  |
| PASS | export carries both edits and untouched seeds |  |
| PASS | browser download contains the same JSON | ~/Projects/VR-HE/prototypes/browser-splat-rendering/TestResults/raw/interactive-demo/verify-20261111-011350-chrome/downloads/vrhe-demo-re... |
| PASS | export copy reached the local results folder |  |
| PASS | V switches to third person behind the avatar | view third, camera 2.60 m / 2.60 m |
| PASS | drag orbits the camera around the avatar without turning it | orbit 45.0 deg, body 179.5->179.5 |
| PASS | mouse wheel zooms out | 2.60 -> 3.65 m |
| PASS | X in third person: normal height, level view, back behind the avatar | offset 0.000, pitch 0.000, yaw 179.5/179.5 |
| PASS | third-person movement walks the avatar |  |
| PASS | V returns to first person |  |
| PASS | M captures the mouse (pointer lock) and shows the crosshair | locked=True |
| PASS | captured mouse motion turns the view (synthetic events; manual check still needed) | 15.0 deg |
| PASS | Esc releases the mouse |  |
| PASS | closing the browser stops the demo server by itself | exit 0 |
| PASS | browser relaunch with the same profile keeps Rack A1's text |  |
| PASS | browser relaunch with the same profile keeps Rack B1's text |  |
| PASS | an unedited rack still shows its original text |  |
| PASS | Reset demo data removes the saved edits |  |

Brave 1.99.55 (Chromium 157.0.8103.39) (verify-20261111-011612-brave) ran the same checks: 67 passed, 2 failed: canvas renders at 1280x720; HUD shows canvas pixels and fps

In the same 1400x960 window Brave's browser interface leaves less room for the page, so the page reduced the canvas to 1220x686 and the HUD labelled it "reduced to fit": the designed fallback, not a rendering fault. Brave's frame pacing above was measured at that size. Every other check passed, including relaunch with the same profile.

Superseded: the first ZIP (build interactive-demo-9f58af7a3697-20261111T055223Z) passed the earlier version of this check list in Chrome (69 of 69) and Brave (67 of 69, the same canvas size). That list tested Left/Right arrows as turning, which contradicts D022: they must step sideways like A/D. The mapping was fixed in e16aaa0, the checks were changed to match, and the old ZIP was deleted before delivery; the runs above are of the fixed build.
