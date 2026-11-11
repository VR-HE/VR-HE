# NetBox comparison notes for a future restart

Status: public-documentation comparison recorded November 11, 2026. This is not an evaluation of the company's installation, an integration design or permission to resume development.

Arlen paused VR-HE after an engineer reported that the company already uses NetBox. The documented inventory overlap is substantial. The company's version, enabled plugins, populated records and workflows remain unknown.

## What the documentation supports

| Area | NetBox documentation | Consequence for a possible restart |
| --- | --- | --- |
| Sites, racks and equipment | Racks belong to sites/locations. Devices have rack positions, heights and faces; multiple devices can occupy a rack. Device types supply default components. | Much of VR-HE's inventory/RU work overlaps an existing product; compare actual company workflows before duplicating it. |
| Broader network records | Core features include IP address management, network/power/console cabling, power distribution and circuits/providers. | These are substantial capabilities beyond the current synthetic VR-HE prototype. |
| Additional data | Typed custom fields and choice sets are documented. A custom field is assigned to object types; it is not automatically the same as a record-local description or VR-HE label catalog. | Map D007-D011 and D038-D041 explicitly rather than assuming equivalent behavior. |
| Data preservation | Deleting a custom field removes its stored data from affected objects, potentially through a background job. | Do not map VR-HE name replacement to custom-field deletion. Prove that every affected description/value survives D041 operations. |
| Access and integration | Object-based permissions, LDAP/SSO and a read/write REST API are documented. | Company VPN, Google Authenticator-compatible MFA, editor roles and permitted API access still require deployment-specific review. An API alone is not the requested two-way spreadsheet synchronization. |
| Visual touring | Core features list SVG rack elevations. The documentation reviewed does not establish Gaussian-splat recording, tracked Quest tours, cabinet scan states or partial rescanning. | Check installed extensions and third-party options before claiming a feature is absent. These capture/VR functions are also unimplemented in VR-HE. |

Google Drive/Sheets/Gemini workflows, approval of AI drafts, synchronized structural edits, attachments and integration-provider controls still need a requirement-by-requirement comparison. Do not assume either product already satisfies the complete requested workflow.

A future VR-HE viewer backed by NetBox is one possible option. No backend, migration, data mapping, access permission or product direction has been approved. Other options include using the company's existing system, extending it, or leaving VR-HE paused.

## Primary sources reviewed

These links pin the documentation reviewed to v4.7.5; recheck against the company's actual version if work resumes.

- [Core scope and features](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/introduction.md)
- [Racks](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/models/dcim/rack.md)
- [Devices and rack-unit placement](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/models/dcim/device.md)
- [Custom fields, choice sets and deletion behavior](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/customization/custom-fields.md)
- [Authentication and object permissions](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/features/authentication-permissions.md)
- [REST API operations](https://github.com/netbox-community/netbox/blob/v4.7.5/docs/integrations/rest-api.md)

ChatGPT/Codex read public documentation through the GitHub connection. No company NetBox instance or company system was accessed. Public product documentation is evidence of documented functionality, not verification that it is enabled, correctly configured or suitable for Arlen's employer.
