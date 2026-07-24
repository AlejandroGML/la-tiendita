# Change: retro-gdpr-compliance (Archived 2026-07-25)

## Intent

Implement full GDPR compliance for TiendaVirtual: granular cookie consent, marketing opt-in at registration, session expiration warning, account self-deletion, data export (portability Art. 20), and newsletter unsubscribe.

## Scope

- **auth**: marketing_consent + terms_accepted fields on registration, consent_at timestamps, session expiration service
- **backend-core**: DELETE /profile, GET /profile/export, newsletter unsubscribe/status endpoints
- **frontend-core**: cookie consent granular modal, legal pages (privacy + terms) trilingual ES/EN/SV
- **Migration 0016**: added columns to users and newsletter_subscribers

## Implementation

This change was implemented directly without formal SDD proposal/spec/design phases. Documentation was created retroactively to sync specs with the actual implementation.

## Commits

- `feat(gdpr): add consent fields to user and newsletter models` (b784ffdb)
- `feat(gdpr): implement account export, deletion and newsletter GDPR` (6a8529a5)
- `feat(gdpr): add i18n keys for GDPR, cookies, session and auth` (ef8e8c51)
- `feat(gdpr): implement granular cookie consent with preferences modal` (8f2cc832)
- `feat(gdpr): add session expiration monitoring with auto-refresh` (0e4286d1)
- `feat(gdpr): add terms and marketing consent to registration` (04e40c55)
- `feat(gdpr): add data export and account deletion to profile page` (842627b2)
- `feat(legal): multilingual privacy policy and terms pages (es/en/sv)` (90e60a09)

## Specs Synced

| Domain | Action |
|--------|--------|
| auth | Updated: R1 (registration accepts consent fields), added R18-R22 |
