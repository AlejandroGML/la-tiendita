# Tasks: Refactor Header — God Node Decomposition

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~950 (sum of 6 phases) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation: CategoryService, svg-icons, hover-delay directive | PR 1 | Base = main; ~120 lines, 3 new files |
| 2 | Leaf + badge components: ThemeToggle, LangSwitch, CurrSwitch, CartBadge, WishlistBadge, UserMenu | PR 2 | Base = main; ~380 lines, 9 new files |
| 3 | Complex components: MegaMenu, Navigation | PR 3 | Base = main; ~250 lines, 5 new files |
| 4 | MobileMenu + Header orchestrator refactor | PR 4 | Base = main; ~300 lines, 2 new + 3 modified |
| 5 | Cleanup: remove dead code, tests for all sub-components | PR 5 | Base = main; ~-100 net, tests added |

## Phase 1: Foundation

- [x] 1.1 Create `frontend/src/app/core/services/category.service.ts` with `BehaviorSubject`-based cache and `load()` method
- [x] 1.2 Create `frontend/src/app/shared/utils/svg-icons.ts` — move SVGS map + `svg()`/`svgRaw()` from header.ts
- [x] 1.3 Create `frontend/src/app/shared/directives/hover-delay.directive.ts` with configurable open/close delays

## Phase 2: Leaf Components

- [x] 2.1 Create `ThemeToggleComponent` — injects ThemeService, toggles light/dark, emits `themeChanged`
- [x] 2.2 Create `LanguageSwitcherComponent` — cycles es→en→sv→es, calls `TranslateService.use()`
- [x] 2.3 Create `CurrencySwitcherComponent` — cycles SEK→EUR→USD→SEK, persists to localStorage

## Phase 3: Badge Components

- [ ] 3.1 Create `CartBadgeComponent` — subscribes to CartService, hides badge at count 0
- [ ] 3.2 Create `WishlistBadgeComponent` — subscribes to WishlistService + AuthStateService
- [ ] 3.3 Create `UserMenuComponent` — shows login/register when unauthenticated, user info + logout when authenticated

## Phase 4: Complex Components

- [x] 4.1 Create `NavigationComponent` — quick links + gender tabs, reads `ActivatedRoute.queryParamMap`
- [x] 4.2 Create `MegaMenuComponent` — 3-column category grid with promo panel, hover logic with timeout-based delayed close

## Phase 5: Mobile + Orchestrator

- [x] 5.1 Create `MobileMenuComponent` — slide-out panel, `@Input() isOpen` / `@Output() closed`
- [x] 5.2 Refactor `header.ts` to thin orchestrator (~100 lines, 3 services max)
- [x] 5.3 Update `header.html` — replace inline markup with sub-component selectors
- [ ] 5.4 Update `header.scss` — move animations to respective sub-component SCSS files

## Phase 6: Cleanup & Tests

- [ ] 6.1 Remove dead code, old SVG map, and inline hover logic from `header.ts`
- [ ] 6.2 Write unit tests: CategoryService (cache hit, error propagation), HoverDelayDirective (fakeAsync)
- [ ] 6.3 Write unit tests per sub-component: MegaMenu, Navigation, CartBadge, WishlistBadge, UserMenu, LangSwitch, CurrSwitch, ThemeToggle, MobileMenu
