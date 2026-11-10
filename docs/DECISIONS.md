# Decision record

Updated November 10, 2026. Confirmed means chosen by Arlen, not implemented.

| ID | Status | Decision | Consequence |
| --- | --- | --- | --- |
| D001 | Confirmed | Build a work utility for touring ISP hubsites/headends using Gaussian splats | Places and equipment need durable linked information |
| D002 | Confirmed | Use Unity and open-source application code | Select compatible application/dependency licenses; Unity itself is proprietary |
| D003 | Confirmed | Production requires intranet/VPN and password access | Authentication and company-network enforcement are production requirements |
| D004 | Confirmed | Production company-connection loss locks viewing and editing, including cached tours/data | An already downloaded tour must not bypass the app's access lock |
| D005 | Confirmed | Test demo requires neither VPN nor password | Keep demo exemptions distinct from production policy |
| D006 | Confirmed | Production editing is for designated editors; other authorized users view only | Login alone does not grant editing rights |
| D007 | Confirmed | Start equipment records from reusable equipment-type templates | Editors must be able to customize fields at runtime |
| D008 | Confirmed | A field addition is local to the selected record by default | No silent retroactive change to every equipment record |
| D009 | Confirmed | Provide a separate way to reuse a field in a template for future equipment | Template reuse is distinct from editing a record |
| D010 | Confirmed | Link all supported data-set categories to an ordinary external spreadsheet | Synchronization is a core capability, not just a link |
| D011 | Confirmed | Synchronize values and mapped additions/deletions in both directions | Define mapping, conflict and deletion semantics before production writes |
| D012 | Confirmed | Use VR-HE/VR-HE with detailed developer notes and transparent human/AI process records | Keep specification, change history and test evidence with source |
| D013 | Confirmed | Provide WASD/mouse first person, generic non-gender humanoid third person and view switching | Behind-avatar follow is the default; orbit behavior is in D024; precise bindings/scale/VR comfort remain open |
| D014 | Confirmed targets | Capture on iPhone SE Gen 3+, equivalent Android+, Quest 3/3S+; view on those phones, Quest 2+, Chrome/Firefox/Edge/Brave | Prove compatibility with representative devices before claiming support |
| D015 | Confirmed | Require Google Drive, Google Sheets and Google Gemini compatibility | Define integration contracts and permissions; Google Sheets is no longer an optional provider choice |
| D016 | Confirmed | Enable approved and disable unapproved AI/spreadsheet integrations in the finished app; extend to tools such as ChatGPT, Claude, Excel and OpenOffice | Policy enforcement and provider adapters are needed; exact roles, scopes and release sequence remain open |
| D017 | Confirmed | Update splat tours to reflect physical site changes | Define versioned updates and preservation/remapping of attached records |
| D018 | Confirmed feasibility target | Rescan only changed site sections where possible | Prove alignment, replacement of old geometry and sufficient reference overlap; no compatibility/quality guarantee yet |
| D019 | Confirmed | Build plain-language guidance into scanning, adding information, navigation and information retrieval | Use familiar FPS/third-person patterns without assuming gaming knowledge |
| D020 | Confirmed | Browser Q raises viewpoint, E lowers it, X restores normal camera height AND levels viewing angle | Define the normal-height reference; X is distinct from the view toggle |
| D021 | Confirmed | Headset version supports full 6DoF movement | Preserve positional/rotational head tracking; decide additional locomotion/comfort controls |
| D022 | Confirmed | Desktop browser supports up/down/left/right arrow movement in addition to WASD | Default mapping matches forward/back/left/right WASD directions |
| D023 | Confirmed | iPhone/Android support familiar mobile FPS/third-person controls, view switching and separate camera-height up/down adjustment | Exact touch layout/gestures remain to be designed for non-gamers |
| D024 | Confirmed | Third-person view supports looking/orbiting around the player/avatar | Default follow remains behind; orbit limits, collision and recenter/follow behavior need design |
| D025 | Confirmed development requirement | Claude implementation/build sessions must use MAX effort | Launch explicitly and verify actual client/model effort; do not silently claim a lower level is MAX |
| D026 | Confirmed feasibility target | Users can open/close virtual cabinet doors and inspect door-mounted panels and interior information | Prove rendering/selection and attachment behavior; no automatic articulation claim |
| D027 | User-proposed capture workflow | Record the same cabinet area closed and open, including inner-door/interior views | Start with local state passes and common references; more views may be needed |
| D028 | Confirmed desired capability | Gemini assists baseline equipment/spreadsheet recording during capture | Field scope, accuracy, review and live-write authority remain open |

D004 does not request automatic deletion of downloaded content. D006 does not establish detailed administrator, site-specific or delete/recovery privileges. D009 does not approve bulk changes to existing records.

## Proposed directions

| Proposal | Reason | Decision still needed |
| --- | --- | --- |
| Separate visual tours from durable asset records | Preserve identity through rescans and visual updates | Exact schema and registration strategy |
| Stable record/field/mapping IDs | Avoid incorrect links after names or row positions change | Representation in the spreadsheet |
| Shared logical editing commands with input adapters | Consistent behavior across mouse, touch and VR | Exact touch and controller interactions |
| Explicit demo/production configuration boundary | Prevent demo exemptions from leaking into production | Deployment and enforcement design |
| Small feasibility scene on weakest targets | Expose rendering constraints early | Scene, renderer candidates and acceptance thresholds |

These proposals are not commitments to a particular package or backend.

## Next unresolved primary question

For the requested capture-assisted baseline inventory, should Gemini create drafts for designated-editor review or write directly to the live spreadsheet?

X is resolved: both normal camera height and level viewing angle.

Google Drive, Sheets and Gemini compatibility is confirmed. Subsequent decisions include exact inventory fields, Gemini data/actions, integration-approval roles, workbook scope, mapping, conflicts, latency, formulas and delete/clear/archive behavior. Excel/OpenOffice compatibility needs concrete adapter and release scope; it does not replace the Google requirement.
