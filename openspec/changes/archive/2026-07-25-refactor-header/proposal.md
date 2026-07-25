# Proposal: Refactor Header — God Node Decomposition

## Intent

Header is the #1 god node in the frontend dependency graph: 35 edges, betweenness 0.094, 785 total lines (336 TS + 454 HTML), 9 injected services, 7 distinct responsibilities in a single component with zero sub-components. This makes it untestable, hard to modify, and a bottleneck for parallel development.

## Scope

### In Scope
- Extract 8 focused sub-components from Header
- Create CategoryService (replaces raw HttpClient category loading)
- Refactor Header as thin orchestrator (~100 lines)
- Add unit tests for each sub-component (none exist today)
- Preserve all existing functionality and visual output

### Out of Scope
- Backend API changes
- Visual redesign or UX changes
- Changes to consumers of `<app-header>` (used in app layout)
- SearchBarComponent extraction (already exists in shared)

## Capabilities

### New Capabilities
- `header-decomposition`: Extracted sub-components (MegaMenu, Navigation, CartBadge, WishlistBadge, UserMenu, LanguageSwitcher, CurrencySwitcher, ThemeToggle, MobileMenu) + CategoryService

### Modified Capabilities
- `frontend-core`: Header component transitions from monolith to orchestrator; external contract (`<app-header>` selector, template API) unchanged

## Approach

1. **CategoryService** — extract `loadCategories()` from Header into injectable service with caching
2. **Sub-components** (each standalone, independently testable):
   - `MegaMenuComponent` — category dropdown, hover logic, promo panel, category groups
   - `NavigationComponent` — quick links (Ofertas/Nuevo/Popular) + gender tabs
   - `CartBadgeComponent` — cart counter, subscribes to CartService
   - `WishlistBadgeComponent` — wishlist counter, subscribes to WishlistService
   - `UserMenuComponent` — auth dropdown, login/logout, user info
   - `LanguageSwitcherComponent` — language selector (es/en/sv)
   - `CurrencySwitcherComponent` — currency selector (SEK/EUR/USD)
   - `ThemeToggleComponent` — dark/light toggle
   - `MobileMenuComponent` — hamburger menu with all mobile nav
3. **Header orchestrator** — compose sub-components in template, retain only layout structure
4. **Tests** — unit tests per sub-component with mocked services

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/app/layout/header/` | Modified | Header.ts reduced to ~100 lines orchestrator |
| `frontend/src/app/layout/header/components/` | New | 8 sub-component directories |
| `frontend/src/app/core/services/category.service.ts` | New | Category loading + caching |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Hover timeout logic breaks across component boundary | Medium | Port exact setTimeout/clearTimeout pattern; test with fake timers |
| SVG icon system not reusable in sub-components | Low | Move SVGS map + svg()/svgRaw() to shared utility or pass via @Input |
| Mobile menu state sync with parent | Low | MobileMenu owns its own open/close state via @Input binding |
| Change detection overhead from 9 sub-components | Low | Each sub-component uses OnPush; only re-renders on its own inputs |

## Rollback Plan

Revert the PR. Header.ts and header.html return to monolith. No backend or consumer changes means zero external impact.

## Dependencies

- None. Pure frontend refactor.

## Success Criteria

- [ ] Header TS reduced from 336 lines to < 150 lines
- [ ] Header graph edges reduced from 35 to < 15
- [ ] Header injects < 4 services (down from 9)
- [ ] All 8 sub-components have unit tests
- [ ] `ng build` succeeds with zero errors
- [ ] All existing functionality preserved (mega menu, badges, auth, i18n, currency, theme, mobile nav, gender tabs)
- [ ] Zero breaking changes to `<app-header>` consumers
