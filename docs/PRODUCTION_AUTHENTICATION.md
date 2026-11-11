# Production authentication: Google Authenticator compatibility

Status: confirmed requirement D040, November 11, 2026; implementation/design work pending. No account, authenticator secret, QR code, production identity service or live Google integration was created during this update.

## Required behavior

Production sign-in must combine company intranet/VPN access, the user's password and authenticator-app verification compatible with Google Authenticator. The existing designated-editor/viewer roles and company-connection-loss lock continue to apply. Authenticator verification does not grant editing rights or bypass a lost company connection. The test demo remains exempt.

Provide ordinary in-app enrollment and verification that work with Google Authenticator on the user's phone. Use a compatible time-based one-time-password (TOTP) profile through an appropriate authentication service/identity provider. The vendor, hosting, exact enrollment/recovery process and session/challenge frequency remain open; this requirement does not select Google Workspace login or a specific backend.

## Proposed implementation boundaries

- Enroll an individual account through a compatible setup QR/manual-key flow, and confirm a generated code before completing enrollment. Validate codes at the trusted authentication service, not solely in distributed Unity/browser code.
- Keep TOTP secrets out of Git, client builds, equipment/spreadsheet records, tour packages, results ZIPs and ordinary logs. Protect secret storage and transport in the chosen service. Define limited clock skew, attempt throttling and replay prevention before implementation.
- Plan company-approved enrollment, lost-phone recovery, authenticator replacement/revocation and session handling. Recovery must not become an unexamined password-only bypass. Exact recovery permissions and steps require a later decision.
- Google Authenticator can generate a code while the phone is offline. VR-HE still needs the required company-network/service connection to validate sign-in and serve protected data. No public-internet dependency for generating a code should be confused with permission for offline tour access.
- Standards-compatible TOTP apps may interoperate, subject to explicit company policy. Do not claim other authenticator vendors tested or imply that every app/provider is approved.

## Planned verification

Verify actual enrollment and sign-in using Google Authenticator, correct/incorrect/expired/reused codes, permitted clock skew, attempts, replacement/recovery and session expiration. Test that a valid code still cannot open data without the required company connection or permissions. Verify demo/production separation. None of these tests has run.

## Primary sources checked November 11

- [Google: verification codes with Google Authenticator](https://support.google.com/accounts/answer/1066447) documents support for sites/apps offering authenticator verification, code generation without internet/mobile service, and use without a Google account.
- [RFC 6238: TOTP](https://datatracker.ietf.org/doc/html/rfc6238) documents the shared-secret, time-based algorithm and validation considerations. It does not select a production identity provider or certify an implementation.
