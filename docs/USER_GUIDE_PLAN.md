# Built-in guidance and controls

Status: confirmed user-experience requirements and proposed teaching plan, November 10, 2026. No tutorial UI exists yet.

## Purpose

Teach people to use the work utility without assuming they play games or understand Unity, splats, camera rigs or data schemas. Retain familiar FPS/third-person interaction patterns for experienced users.

The instructions must be part of the application. Developer documentation alone does not satisfy this requirement.

## Required workflows to teach

| Task | Plain-language guidance needed |
| --- | --- |
| Scan a site | Start a capture, move the device, cover the area, finish and understand processing/status |
| Update a changed area | Choose the section and capture sufficient surrounding reference area when partial updates work |
| Add information | Select an area/equipment item, open its menu, add a description/record/field and save |
| Navigate a tour | Move, look, adjust browser viewpoint height and switch agreed view modes |
| Find stored information | Select the relevant room/rack/RU/equipment and open its attached information |
| Use spreadsheet/AI connections | Recognize allowed connections, sync status, permissions and the chosen AI capabilities |

Exact screens, UI labels and integration workflows remain to be designed. Describe only capabilities implemented in the current build; explain unavailable actions in plain language.

## Confirmed browser controls

| Input | Intended action | Status |
| --- | --- | --- |
| W/A/S/D | Familiar forward/left/back/right movement | Confirmed; movement frame/collision details still need design |
| Arrow keys | Up/forward, down/back, left/left, right/right movement, matching WASD | Movement support confirmed; mapping interpreted as WASD equivalents |
| Mouse | Look around in first person; orbit/look around the avatar in third person | Confirmed; sensitivity, gesture/button and menu behavior still need design |
| Right-click | Open relevant editing/attachment interaction | Confirmed; selection details still need design |
| Q | Float the camera viewpoint up | Confirmed |
| E | Lower the camera viewpoint | Confirmed |
| X | Restore normal camera height and level viewing angle | Confirmed; define the normal-height reference |
| View-toggle key | Switch first-/third-person presentation | Required feature; key not selected |

Arlen confirmed X does both: restore normal camera height and level the viewing angle. Treat it as a camera reset at the current location, not an unrequested return to a site entrance. Define the height reference for each relevant camera mode.

## Mobile controls and third-person orbit

On iPhone and Android, require familiar mobile FPS/third-person movement and look controls, first-/third-person view switching and a separate camera-height up/down adjustment.

Proposed familiar touch layout:
- Left on-screen movement stick.
- Right-side look/drag input; in third person, look/orbit around the avatar.
- A visible first-/third-person view-mode control.
- Separate camera-height up/down controls, distinct from tilting the viewing angle.

Exact layout, button labels, gestures and accessibility options remain to be designed and tested. Do not assume a player already knows gaming conventions.

Third person defaults to behind-avatar follow but must allow looking/orbiting around the player/avatar. Design horizontal/vertical orbit limits, camera obstruction handling and how follow resumes after orbiting. The exact behavior has not been selected.

The third-person view must retain the requested generic non-gender humanoid for relative scale. Avatar dimensions and scale accuracy still need decisions.

## VR requirement

Support full 6DoF movement: positional movement along three axes and rotation around three axes.

Head tracking must remain consistent with physical movement. Additional virtual traversal, controller inputs, third-person behavior and comfort options need design. Browser Q/E/X semantics do not define a headset-pose reset.

Mobile movement/look, view switching and camera-height controls are required; their exact touch layout and input-specific help still need design. Any VR third-person/orbit implementation must preserve physical head tracking and address comfort.

## Proposed teaching approach

- Offer a short guided practice tour using synthetic information.
- Explain one action at a time with a visible result.
- Label actions as Move, Look around, View height and Open information, rather than relying on gaming jargon.
- Provide contextual prompts beside the task and a Help/Controls entry that can be reopened.
- Show controls for the current input device.
- Offer clear completion/save/sync states and explain permission or connection restrictions.
- Make unfamiliar steps discoverable without requiring a long manual.
- Consider clickable/touch navigation alternatives and remapping as design options; scope is not yet approved.

The practice sequence can cover: enter a tour, look/move, open a rack record, inspect a linked field, add a synthetic note if authorized, and return to the tour. The capture/update guide needs its own device-specific walkthrough.

## Validation

Have a non-gamer attempt the four required workflows using the in-app guidance. Record where assistance was needed. Define acceptable completion effort and accessibility needs with Arlen.

Test help with mouse, touch and VR inputs. Ensure instructions do not request tasks blocked by a user's role or by the production company-connection lock.

See [test plan](TEST_PLAN.md), [product specification](PRODUCT_SPEC.md) and [capture updates](CAPTURE_UPDATES.md).
