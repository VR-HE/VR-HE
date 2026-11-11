# Equipment, descriptions and names: Linux real-browser checks, November 11, 2026

Generated from the raw `verify.json` files of `Tools/verify_interactive_demo.py` (raw results stay ignored under `TestResults/raw/interactive-demo/`). Development laptop: Linux Mint 22.3, Intel Core i7-13620H, NVIDIA RTX 4060 Laptop GPU, 1920x1200 at 60 Hz. Each run used a fresh throwaway browser profile, extracted the final Windows bundle `VRHE-Interactive-Demo-20261111-4f4f9ac.zip` and served it with the bundle's own `tools/demo_server.py`. Linux only: this is not Windows evidence.

Parts: `all` runs the earlier demo checks, the mouse Y-inversion checks (stage 1 of [the task](../../../../docs/EQUIPMENT_DESCRIPTIONS_TASK.md)) and the equipment, description and name checks (stage 2), with reload, browser restart, export and reset. `migration` starts from the delivered 294f4b2 bundle, which writes format 1 rack notes, then opens the same profile with this build. EditMode tests (47 of 47) and the design are described in [the prototype README](../../README.md#equipment-descriptions-and-names-branch-protoequipment-descriptions).

Brave's interface leaves less room in the same 1400x960 window, so the page reduces its canvas to 1220x686 and labels it, as designed; the two checks that expect 1280x720 fail there and nothing else does.

| Run | Part | Browser | Target | Canvas | Checks |
| --- | --- | --- | --- | --- | --- |
| verify-20261111-095121-chrome | all | Google Chrome 157.0.8103.50 | bundle interactive-demo-4f4f9ac2fd78-20261111T144938Z | 1280x720 | 124 passed, 0 failed |
| verify-20261111-095457-brave | all | Brave 1.99.55 (Chromium 157.0.8103.39) | bundle interactive-demo-4f4f9ac2fd78-20261111T144938Z | 1220x686 | 122 passed, 2 failed |
| verify-20261111-095835-chrome | migration | Google Chrome 157.0.8103.50 | bundle interactive-demo-4f4f9ac2fd78-20261111T144938Z | - | 9 passed, 0 failed |
| verify-20261111-100052-brave | migration | Brave 1.99.55 | bundle interactive-demo-4f4f9ac2fd78-20261111T144938Z | - | 9 passed, 0 failed |

## Frame pacing by activity

Frame intervals measured inside the page while the automated input ran. fps = frames / seconds. Percentiles are upper edges of 0.5 ms histogram bins over timestamps with about 1 ms browser resolution, so 60 Hz frames show as 16-17 ms samples and a 17.5 ms median; Max is the raw longest interval. CPU = Unity main-thread work per frame; sort = UnitySplats' CPU sort. The `panel.equipment` and `panel.names` rows were measured while typing in the equipment editor, typing in the Description names panel and with that panel open. The browser paces frames to the 60 Hz display (no cap is set), so these are not uncapped capacity, and no pass threshold is implied.

### Google Chrome 157.0.8103.50, canvas 1280x720 (verify-20261111-095121-chrome)

| Activity | Frames | fps | Mean ms | p95 ms | p99 ms | Max ms | >50 ms | CPU mean ms | Sort mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first.idle (3 s) | 180 | 60.0 | 16.67 | 17.5 | 18.5 | 23.0 | 0 | 10.32 | 9.53 |
| first.moving (W held 2.5 s, sliding along a rack) | 162 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 8.20 | 7.41 |
| first.height (Q held 1 s) | 72 | 60.1 | 16.65 | 17.5 | 18.5 | 18.0 | 0 | 8.04 | 7.18 |
| first.looking (drag) | 106 | 60.0 | 16.66 | 17.5 | 18.5 | 18.0 | 0 | 8.55 | 7.56 |
| third.orbiting (drag) | 136 | 60.0 | 16.65 | 17.5 | 18.5 | 18.0 | 0 | 12.54 | 11.74 |
| third.moving (W held 2 s) | 132 | 60.0 | 16.67 | 18.0 | 18.5 | 18.0 | 0 | 10.54 | 9.66 |
| panel.typing | 119 | 59.0 | 16.95 | 20.0 | 28.0 | 36.0 | 0 | 8.39 | 7.44 |
| panel.help open (2 s) | 120 | 60.0 | 16.67 | 17.5 | 17.5 | 18.0 | 0 | 10.43 | 9.69 |
| panel.equipment typing | 98 | 59.4 | 16.83 | 18.5 | 42.5 | 42.0 | 0 | 8.95 | 8.05 |
| panel.names typing | 39 | 59.9 | 16.69 | 18.0 | 18.5 | 18.0 | 0 | 8.54 | 7.69 |
| panel.names open (2 s) | 121 | 60.0 | 16.67 | 18.5 | 18.5 | 19.0 | 0 | 8.31 | 7.55 |

### Brave 1.99.55 (Chromium 157.0.8103.39), canvas 1220x686 (verify-20261111-095457-brave)

| Activity | Frames | fps | Mean ms | p95 ms | p99 ms | Max ms | >50 ms | CPU mean ms | Sort mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first.idle (3 s) | 180 | 60.0 | 16.66 | 18.5 | 23.5 | 25.0 | 0 | 8.53 | 7.80 |
| first.moving (W held 2.5 s, sliding along a rack) | 162 | 60.0 | 16.67 | 18.5 | 18.5 | 18.0 | 0 | 8.64 | 7.69 |
| first.height (Q held 1 s) | 72 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 8.29 | 7.37 |
| first.looking (drag) | 106 | 60.0 | 16.67 | 17.5 | 18.5 | 18.0 | 0 | 8.27 | 7.41 |
| third.orbiting (drag) | 136 | 59.6 | 16.79 | 18.5 | 19.5 | 36.0 | 0 | 9.88 | 8.98 |
| third.moving (W held 2 s) | 133 | 60.0 | 16.66 | 18.0 | 19.5 | 20.0 | 0 | 10.27 | 9.39 |
| panel.typing | 119 | 59.5 | 16.81 | 18.5 | 26.5 | 44.0 | 0 | 8.65 | 7.76 |
| panel.help open (2 s) | 120 | 60.0 | 16.67 | 17.5 | 18.5 | 19.0 | 0 | 8.47 | 7.65 |
| panel.equipment typing | 95 | 60.0 | 16.66 | 18.5 | 19.5 | 19.0 | 0 | 8.34 | 7.51 |
| panel.names typing | 38 | 59.9 | 16.68 | 18.5 | 18.5 | 18.0 | 0 | 8.47 | 7.63 |
| panel.names open (2 s) | 120 | 60.0 | 16.68 | 18.5 | 25.5 | 32.0 | 0 | 8.76 | 7.86 |

## Checks (Google Chrome 157.0.8103.50, verify-20261111-095121-chrome)

Trusted keyboard and mouse events from the Chrome DevTools Protocol, so Unity receives the same events as from a person. Native drop-down lists are set by script, because the protocol cannot drive their pop-up; every other click and key is a real input event. Pointer-lock motion under synthetic events is a best-effort check; a manual check is still needed.

| Result | Check | Detail |
| --- | --- | --- |
| PASS | page ready with LOCAL DEMO DATA badge |  |
| PASS | canvas renders at 1280x720 | {'width': 1280, 'height': 720, 'cssWidth': 1280, 'cssHeight': 720} |
| PASS | HUD shows canvas pixels and fps | 1280x720 px / 41 fps |
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
| PASS | D steps right | 0.78 m |
| PASS | A steps left | -0.78 m |
| PASS | Up arrow moves forward | 0.78 m |
| PASS | Down arrow moves back | -0.78 m |
| PASS | Right arrow steps right like D, without turning | 0.78 m, yaw change 0.0 deg |
| PASS | Left arrow steps left like A, without turning | -0.78 m, yaw change 0.0 deg |
| PASS | racks stop the walker (proxy collision) | walked 2.11 m, feet [1.45, 0.02, -0.73] |
| PASS | Q raises the camera | +0.60 m, eye 2.20 m |
| PASS | E lowers the camera | -0.60 m |
| PASS | drag right/down turns right and looks down (0.15 deg/px) | yaw 24.0, pitch 9.0 |
| PASS | a drag does not select |  |
| PASS | X restores normal height and a level view (first person) | before offset -0.60, pitch 9.0; after offset 0.000, pitch 0.000, eye 1.600 |
| PASS | Rack A1 is straight ahead from the front aisle | {'visible': True, 'unityX': 631.6578979492188, 'unityY': 52.646270751953125, 'clientX': 669.6578979492188, 'clientY': 716.4006042480469} |
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
| PASS | movement works again after closing the panel | 0.80 m in 0.6 s |
| PASS | Rack B1 is straight ahead from the back aisle | {'visible': True, 'unityX': 697.1633911132812, 'unityY': 63.573890686035156, 'clientX': 735.1633911132812, 'clientY': 705.4729843139648} |
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
| PASS | a rack panel shows its equipment list (empty) and the Add equipment form | 0 items, 42 RU |
| PASS | RU 43 in a 42 RU rack: flagged while typing, refused by the store, nothing written | Invalid: Rack units must be whole numbers from 1 to 42 (this rack's size in the prototype). Nothing was saved. |
| PASS | Add equipment opens the new item with exactly one empty, unnamed description | Synthetic switch SW-01 RU 40-40, 1 description(s) |
| PASS | equipment and description identities are their own prefixed UUIDs, linked to the rack | eq-5b744004-a0b4-4bcd-9eb1-7d5dffe645e6 / dsc-64e66511-53e2-4052-b116-1a4543bfac25 |
| PASS | typing W A S D Q E X in an equipment description moves nothing | moved 0.00000 m |
| PASS | letters typed while a name list has focus open no panel and move nothing | panel equipment |
| PASS | Add description focuses the new text box and scrolls it into view above the Save row | top 506 bottom 581 footer 617 hit TEXTAREA |
| PASS | Remove works on an empty description and is unavailable for one with text | 4 -> 3 |
| PASS | after Ctrl+Enter the caret stays where it was, so typing carries on in the same description | [2, 'TEXTAREA', 24, 24] -> [2, 'TEXTAREA', 24, 24] |
| PASS | Ctrl+Enter saves the item: one unnamed and two named descriptions, first ID kept | Saved: Saved Synthetic switch SW-01 (version 2). 2 new description(s) added to this item only. (09:52:32) |
| PASS | the item's back link returns to its rack, which lists it |  |
| PASS | a rack unit already in use is flagged while typing (front/rear is not recorded) | Shares rack units with Synthetic switch SW-01 (RU 40). Two items can share units only when one is mounted at the front and one at the rea... |
| PASS | a 2U device is one record covering RU 20-21 | RU 20-21 |
| PASS | the same name holds different text on each item (choosing a name copies nothing) |  |
| PASS | saving the server left the switch unchanged (record-local) |  |
| PASS | rack A4 lists both devices, top of the rack first |  |
| PASS | Add name puts the name in the shared list and changes no equipment record | Added 'Serail no' to the description names. No equipment record changed. |
| PASS | 'New name...' in a description adds the name and chooses it for that description only | Added "Firmware version" to the description names. It is chosen for this description only; press Save to keep it on this item. |
| PASS | a shortcut with unsaved changes asks first; Keep editing returns to the description in use | asked True; top 536 bottom 611 footer 617 hit TEXTAREA |
| PASS | router saved with a misspelt name, Serial number and the new name | Saved Synthetic router RT-01 (version 2). 2 new description(s) added to this item only. (09:52:47) |
| PASS | the Equipment list shows each rack's items; Open opens the item and selects its rack | listed 2 |
| PASS | switch saved with a fourth description under the misspelt name |  |
| PASS | Rename fixes the spelling everywhere: same descriptions, same text, same item versions | Renamed 'Serail no' to 'Serial no.'. 2 description(s) on 2 equipment item(s) now show the new name; their text is unchanged. |
| PASS | Remove can't be confirmed until a replacement is chosen (button disabled) |  |
| PASS | the store itself refuses removal without a valid replacement and writes nothing | Invalid; Invalid; Invalid; Invalid |
| PASS | Replace moves every description from 'Serial no.' to 'Serial number', keeping IDs, order and text | Replaced 'Serial no.' with 'Serial number' on 2 description(s) across 2 equipment item(s); every description kept its text. 'Serial no.' ... |
| PASS | where an item already had 'Serial number', both descriptions are kept and the page says so | Synthetic switch SW-01 in Rack A4, Synthetic router RT-01 in Rack B2 already had a description named 'Serial number'. Both descriptions a... |
| PASS | the replaced name leaves the list and stays recorded as replaced, with what moved |  |
| PASS | with browser storage full, the replacement is refused and nothing changes | filled 13 keys / 5236768 chars; The browser refused to save (QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the va... |
| PASS | after space is freed the same replacement succeeds and keeps the text | Replaced 'Asset no.' with 'Asset tag' on 1 description(s) across 1 equipment item(s); every description kept its text. ' |
| PASS | page reload keeps Rack A1's saved text |  |
| PASS | page reload keeps Rack B1's saved text |  |
| PASS | a page reload keeps every equipment item, its RU range and each description's ID, name and text |  |
| PASS | a page reload keeps the name list: replaced names retired, the new name active |  |
| PASS | export is labelled local demo data with schema |  |
| PASS | export carries both edits and untouched seeds |  |
| PASS | browser download contains the same JSON | ~/Projects/VR-HE/prototypes/browser-splat-rendering/TestResults/raw/interactive-demo/verify-20261111-095121-chrome/downloads/vrhe-demo-re... |
| PASS | export copy reached the local results folder |  |
| PASS | export (format 2) carries every equipment item with its descriptions and name labels |  |
| PASS | export keeps replaced names inspectable and says no spreadsheet column is touched |  |
| PASS | V switches to third person behind the avatar | view third, camera 2.60 m / 2.60 m |
| PASS | drag orbits the camera around the avatar without turning it | orbit 45.0 deg, body 179.8->179.8 |
| PASS | mouse wheel zooms out | 2.60 -> 3.65 m |
| PASS | X in third person: normal height, level view, back behind the avatar | offset 0.000, pitch 0.000, yaw 179.8/179.8 |
| PASS | third-person movement walks the avatar |  |
| PASS | V returns to first person |  |
| PASS | M captures the mouse (pointer lock) and shows the crosshair | locked=True |
| PASS | captured mouse motion turns the view (synthetic events; manual check still needed) | -30.0 deg |
| PASS | Esc releases the mouse |  |
| PASS | captured mouse moving down looks down with inversion off (synthetic events) | yaw 0.0, pitch 12.0 |
| PASS | Invert mouse Y-axis is off by default in a new profile |  |
| PASS | Help > Settings checkbox turns inversion on (real click) |  |
| PASS | inversion choice is saved in this browser profile | {'lookSpeed': 1, 'invertMouseY': True} |
| PASS | inverted drag: same turn, vertical reversed (first person) | normal yaw 18.0 pitch 9.0; inverted yaw 18.0 pitch -9.0 |
| PASS | inverted captured mouse: moving down looks up (synthetic events; manual check still needed) | yaw 0.0, pitch -12.0 |
| PASS | with inversion on, pointing and clicking still pick the rack under the pointer | hovered rec-ae2ab7c1, selected rec-ae2ab7c1 |
| PASS | with inversion on, Q raises, E lowers and X restores height and a level view | Q +0.37 m, E to -0.35 m, X from pitch -9.0 to 0.000 |
| PASS | inverted third-person orbit: same horizontal orbit, vertical reversed | yaw 15.0, pitch -9.0 |
| PASS | with inversion on, the mouse wheel still zooms out | 3.65 -> 4.70 m |
| PASS | with inversion on, W does nothing while Help is open |  |
| PASS | inversion still on after a page reload (checkbox, page state, stored preference) | {'lookSpeed': 1, 'invertMouseY': True} |
| PASS | after a page reload, a drag down still looks up (inverted) | yaw 18.0, pitch -9.0 |
| PASS | closing the browser stops the demo server by itself | exit 0 |
| PASS | inversion still on after closing and restarting the browser (checkbox, page state, stored preference) | {'lookSpeed': 1, 'invertMouseY': True} |
| PASS | after closing and restarting the browser, a drag down still looks up (inverted) | yaw 18.0, pitch -9.0 |
| PASS | unticking the checkbox turns inversion off |  |
| PASS | inversion off again: a drag down looks down, and off is saved | yaw 18.0, pitch 9.0, stored {'lookSpeed': 1, 'invertMouseY': False} |
| PASS | an older stored preference without the inversion field loads as normal look, keeping look speed | invert False, speed 1.5 |
| PASS | an unreadable stored preference loads the defaults and the demo still starts | invert False, speed 1, error '' |
| PASS | closing and restarting the browser keeps every equipment item, its RU range and each description's ID, name and text |  |
| PASS | closing and restarting the browser keeps the name list: replaced names retired, the new name active |  |
| PASS | browser relaunch with the same profile keeps Rack A1's text |  |
| PASS | browser relaunch with the same profile keeps Rack B1's text |  |
| PASS | an unedited rack still shows its original text |  |
| PASS | Reset demo data starts over: no rack notes, no equipment, only the starter names | 0 items, 6 names |

Brave 1.99.55 (Chromium 157.0.8103.39) (verify-20261111-095457-brave) ran the same checks: 122 passed, 2 failed: canvas renders at 1280x720; HUD shows canvas pixels and fps

## Carry-over checks (Google Chrome 157.0.8103.50, verify-20261111-095835-chrome)

The delivered 294f4b2 bundle saved format 1 rack notes in a real browser profile; this build then opened the same profile; finally the 294f4b2 build ran on it again.

| Result | Check | Detail |
| --- | --- | --- |
| PASS | first demo build uses the version 1 key |  |
| PASS | first demo build saved version 1 rack notes (A3 once, B4 twice) plus an unknown record |  |
| PASS | this build opens the profile without writing anything |  |
| PASS | first-demo rack notes are carried over as rack notes with their versions | A3 v1, B4 v2 |
| PASS | Saved data panel explains the carry-over and the kept copy | Carried over 3 rack notes from the earlier demo version (vrhe.demo.records.v1.site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a). That copy is ke... |
| PASS | export before any save holds the carried notes, the unknown record and the raw version 1 copy |  |
| PASS | the first save writes format 2 with every carried note (unknown included); version 1 untouched |  |
| PASS | after a reload this build still shows the carried note and the new equipment |  |
| PASS | the first demo build still finds its own saved notes afterwards |  |

## Carry-over checks (Brave 1.99.55, verify-20261111-100052-brave)

The delivered 294f4b2 bundle saved format 1 rack notes in a real browser profile; this build then opened the same profile; finally the 294f4b2 build ran on it again.

| Result | Check | Detail |
| --- | --- | --- |
| PASS | first demo build uses the version 1 key |  |
| PASS | first demo build saved version 1 rack notes (A3 once, B4 twice) plus an unknown record |  |
| PASS | this build opens the profile without writing anything |  |
| PASS | first-demo rack notes are carried over as rack notes with their versions | A3 v1, B4 v2 |
| PASS | Saved data panel explains the carry-over and the kept copy | Carried over 3 rack notes from the earlier demo version (vrhe.demo.records.v1.site-bfaaec37-26c3-4ca9-99f2-b1fb9de68f5a). That copy is ke... |
| PASS | export before any save holds the carried notes, the unknown record and the raw version 1 copy |  |
| PASS | the first save writes format 2 with every carried note (unknown included); version 1 untouched |  |
| PASS | after a reload this build still shows the carried note and the new equipment |  |
| PASS | the first demo build still finds its own saved notes afterwards |  |
