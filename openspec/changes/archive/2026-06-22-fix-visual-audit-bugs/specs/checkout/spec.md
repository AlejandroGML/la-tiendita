# Delta for checkout

> **Capability**: checkout (frontend dark-mode legibility of `/checkout` page)
> **Source**: `openspec/specs/checkout/spec.md` (backend checkout flows — no frontend dark-mode requirements exist)
> **Driver**: C3 (checkout dark mode unreadable)

## ADDED Requirements

### Requirement: Checkout Page is Legible in Dark Mode

The checkout page (`/checkout`) MUST render all text, backgrounds, borders, and dividers with explicit dark-mode variants (`dark:` Tailwind classes or `var(--color-*)` tokens) so that every element meets WCAG AA contrast in dark mode. No element SHALL be invisible or near-invisible (e.g., light text on light background, dark text on dark background).

#### Scenario: Section titles legible in dark mode

- GIVEN `html.dark-theme` is active
- WHEN the checkout page renders the section headings "Dirección de Envío" and "Resumen del Pedido"
- THEN the headings use light text on a dark card background (e.g. `text-gray-900 dark:text-gray-100`)

#### Scenario: Form inputs legible in dark mode

- GIVEN dark mode is active
- WHEN the shipping-address inputs render
- THEN input fields have a dark background and light foreground (no white-on-white)

#### Scenario: Error messages visible in dark mode

- GIVEN the checkout form has a validation error (e.g., empty shipping address)
- AND dark mode is active
- WHEN the error is displayed
- THEN the error text uses a light red shade (e.g. `text-red-400`) readable against the dark background

#### Scenario: Item list divider and totals legible

- GIVEN dark mode is active
- WHEN the order summary list renders
- THEN item dividers, quantity labels ("Cantidad: 2"), product names, and the "Total" amount all use dark-mode-appropriate colors

### Requirement: Checkout Maintains Light Mode Appearance (No Regression)

The dark-mode fixes MUST NOT change the checkout page appearance in light mode. All elements SHALL look identical to the pre-change light-mode rendering.

#### Scenario: Light mode unaffected by dark-mode additions

- GIVEN `html.dark-theme` is NOT active (light mode)
- WHEN the checkout page renders after the change
- THEN the page appearance matches the previous light-mode rendering exactly (same colors, same contrast)
- AND the only new code is `dark:*` variant classes that are inert when dark mode is off
