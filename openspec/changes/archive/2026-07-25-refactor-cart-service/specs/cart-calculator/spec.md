# cart-calculator Specification

## Purpose

Pure, dependency-free functions for derived cart data. Centralizes calculations currently duplicated across consumers (cart-badge, mobile-menu, cart component). Zero Angular DI, zero side effects, zero I/O — trivially testable.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | `calculateTotalItems(items)` returns summed quantities | MUST |
| R2 | Empty / null / undefined input returns `0` | MUST |
| R3 | Pure module (no side effects) | MUST |
| R4 | Accepts `readonly CartItem[]` | MUST |
| R5 | Future pure functions (subtotal, savings) MAY be added | MAY |

### Requirement: calculateTotalItems

The system MUST export a pure function `calculateTotalItems(items: readonly CartItem[] | null | undefined): number` that returns the sum of `quantity` across all items. The function MUST be safe to call with `[]`, `null`, or `undefined` — in those cases it MUST return `0`. It MUST NOT mutate the input array. Missing or non-numeric `quantity` SHALL be treated as `0`.

#### Scenario: Sums multiple items

- GIVEN `items = [{ quantity: 2 }, { quantity: 3 }, { quantity: 1 }]`
- WHEN `calculateTotalItems(items)` is called
- THEN it returns `6`

#### Scenario: Empty array returns 0

- GIVEN `items = []`
- WHEN `calculateTotalItems(items)` is called
- THEN it returns `0`

#### Scenario: Null input returns 0

- GIVEN `items = null`
- WHEN `calculateTotalItems(items)` is called
- THEN it returns `0`

#### Scenario: Undefined input returns 0

- GIVEN `items = undefined`
- WHEN `calculateTotalItems(items)` is called
- THEN it returns `0`

#### Scenario: Malformed quantity treated as 0

- GIVEN `items = [{ quantity: 2 }, { quantity: undefined as any }, { quantity: 4 }]`
- WHEN `calculateTotalItems(items)` is called
- THEN it returns `6`

#### Scenario: Pure — does not mutate input

- GIVEN `items = [{ quantity: 1 }, { quantity: 2 }]`
- WHEN `calculateTotalItems(items)` is called
- THEN `items` is unchanged (length and order preserved)
