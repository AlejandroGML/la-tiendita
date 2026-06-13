# Delta for gender-tabs

## ADDED Requirements

### Requirement: Gender Filter Tabs in Header

The system MUST render gender filter tabs (Mujer, Hombre, Kids, Unisex) in the header navigation. Each tab click MUST navigate to `/productos?gender={value}`. The active tab SHOULD be visually highlighted based on the current `gender` query parameter.

#### Scenario: Gender tab click navigates with query param
- GIVEN the header is rendered on the home page
- WHEN user clicks "Mujer" tab
- THEN the browser navigates to `/productos?gender=Ladies`
- AND the product catalog loads filtered by `target_gender=Ladies`

#### Scenario: Active tab highlights on filtered catalog page
- GIVEN the user is on `/productos?gender=Men`
- WHEN the header renders gender tabs
- THEN "Hombre" tab shows active/highlighted state

#### Scenario: No active tab when no gender filter
- GIVEN the user is on `/productos` without `gender` query param
- WHEN the header renders gender tabs
- THEN no gender tab is highlighted as active

#### Scenario: Gender tabs use i18n labels
- GIVEN the app language is set to English
- WHEN the header renders gender tabs
- THEN tab labels show "Women", "Men", "Kids", "Unisex" (from translation keys)
