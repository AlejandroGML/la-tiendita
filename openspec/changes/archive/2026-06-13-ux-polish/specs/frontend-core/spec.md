# Delta for frontend-core

## ADDED Requirements

### Requirement: Gender Navigation Tabs in Header

The HeaderComponent MUST render a row of gender filter tabs (Mujer/Hombre/Kids/Unisex) below the main navigation bar. Each tab MUST navigate to `/productos?gender={value}` where value maps to the backend's `target_gender` values (Ladies, Men, Kids, Unisex). The active tab SHOULD highlight based on the current `gender` query parameter in the URL.

#### Scenario: Gender tab renders and navigates
- GIVEN the header component is initialized
- WHEN user clicks "Mujer" tab
- THEN router navigates to `/productos?gender=Ladies`

#### Scenario: Active tab detection
- GIVEN current URL is `/productos?gender=Men`
- WHEN header renders
- THEN "Hombre" tab is visually active

### Requirement: Landing Page Routes

The Angular router MUST include two new lazy-loaded routes: `/nuevos` and `/ofertas`. Each SHALL load a lightweight wrapper component that renders `ProductListComponent` with preset filter parameters. SEO meta tags (Title, Meta) SHALL be updated on init.

#### Scenario: /nuevos route resolves
- GIVEN user navigates to `/nuevos`
- WHEN the route activates
- THEN `ProductListComponent` renders with `order_by=created_at` preset

#### Scenario: /ofertas route resolves
- GIVEN user navigates to `/ofertas`
- WHEN the route activates
- THEN `ProductListComponent` renders with `has_promotion=true` preset

### Requirement: UX Polish i18n Keys

The system MUST add approximately 15 new translation keys across all three locale files (es.json, en.json, sv.json) covering: badge labels (bestseller, nuevo), gender tab labels, landing page titles, SEO alt text, and sizing guide headers.

#### Scenario: All new keys resolve in each language
- GIVEN language is set to Swedish
- WHEN any new UI element renders (badge, tab, landing page)
- THEN the Swedish translation is displayed
- AND no missing key fallback to English is visible
