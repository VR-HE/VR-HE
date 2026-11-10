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
| Mouse | Look around | Confirmed; sensitivity/menu behavior still needs design |
| Right-click | Open relevant editing/attachment interaction | Confirmed; selection details still need design |
| Q | Float the camera viewpoint up | Confirmed |
| E | Lower the camera viewpoint | Confirmed |
| X | Return to center view | Binding confirmed; meaning needs clarification |
| View-toggle key | Switch first-/third-person presentation | Required feature; key not selected |

Clarify X: restore level viewing angle, normal camera height, both, or another intended center. Do not silently implement a teleport to the entrance or to an object.

The third-person view must retain the requested generic non-gender humanoid for relative scale. Avatar dimensions, scale accuracy and camera behavior still need decisions.

## VR requirement

Support full 6DoF movement: positional movement along three axes and rotation around three axes.

Head tracking must remain consistent with physical movement. Additional virtual traversal, controller inputs, third-person behavior and comfort options need design. Browser Q/E/X semantics do not define a headset-pose reset.

Touch equivalents for mobile and input-specific help also need design.

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
