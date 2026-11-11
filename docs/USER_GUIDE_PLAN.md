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
| Inspect a cabinet | Open/close its virtual door and find door-mounted or interior records |
| Capture inventory with Gemini | Capture readable labels, follow extraction status and handle uncertain candidate entries for designated-editor review before live spreadsheet writes |

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

## Mouse preference and equipment descriptions — November 11 additions

Teach Help > Settings > Invert mouse Y-axis as an optional saved preference for looking/orbiting; explain that Q/E still change height and X still restores normal height and a level view. The checkbox is built into the proto/equipment-descriptions demo and checked in Chrome and Brave on Linux; Windows is untested.

The next equipment editor should distinguish a rack from the many devices it can contain and show each item's occupied RU range. New equipment starts with one unnamed description. Teach Add Description, leaving a note unnamed or choosing/creating a reusable description name, and managing the dropdown names. Explain that reusing a name does not share the equipment text. Catalog-name maintenance and deleting an item's description are different actions. Teach Rename for spelling corrections and Choose replacement name for retiring/standardizing a name. No valid replacement means removal is unavailable. Existing equipment descriptions keep their text under the corrected/replacement name; show affected references and explain any collision without discarding values (D041).

The proto/equipment-descriptions demo's in-app help now teaches these steps in plain language: selecting and opening a rack, the rack note (whole rack, not one device), equipment in a rack (RU numbering from the bottom, 1U and 2U examples, overlap warnings), descriptions of one item (one unnamed to start, Add description, names never copy text, only empty descriptions can be removed), description names (add, Rename, Remove with a required replacement and what happens to clashes), saving and reopening (including the carry-over of earlier rack descriptions as rack notes) and what is saved where. It is prototype wording on synthetic data; whether non-gamers find it clear has not been tested with people.

For the official version, add plain-language Google Authenticator enrollment, verification and approved recovery guidance once the authentication design is selected. Preserve the network/password requirements and demo exemption; do not imply a code permits offline access. See [production authentication](PRODUCTION_AUTHENTICATION.md).

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

## Cabinet and AI capture guidance

Teach the closed/open local capture passes with clear interior/inner-door coverage. In the viewer, use plain Open door, Close door and Open information actions with mouse, touch and VR equivalents. See [cabinet states](CABINET_STATES.md).

For inventory assistance, explain what was read from a source image, what needs correction, which equipment it belongs to and whether it is still a draft or has synchronized. A designated editor must approve AI-generated entries/updates before live spreadsheet writes. Teach how to inspect evidence, correct/reject a proposal and recognize draft/approved/synchronized states. Do not imply a successful AI response is verified equipment data.

## Validation

Have a non-gamer attempt the four required workflows using the in-app guidance. Record where assistance was needed. Define acceptable completion effort and accessibility needs with Arlen.

Test help with mouse, touch and VR inputs. Ensure instructions do not request tasks blocked by a user's role or by the production company-connection lock.

See [test plan](TEST_PLAN.md), [product specification](PRODUCT_SPEC.md) and [capture updates](CAPTURE_UPDATES.md).
