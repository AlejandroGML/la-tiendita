# Design: Refactor Header — God Node Decomposition

## Technical Approach

Decompose the 785-line monolithic `HeaderComponent` into 9 focused standalone sub-components and 1 new `CategoryService`. Header becomes a thin template-only orchestrator (~100 lines TS). Each sub-component is `standalone: true`, uses `ChangeDetectionStrategy.OnPush`, and co-locates its template + styles. The SVG icon system moves to a shared utility. Hover timeout logic is encapsulated in a reusable directive.

## Architecture Decisions

### Decision: SVG Icon Strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| A: IconService (injectable) | Adds DI overhead for static data | Rejected |
| B: Shared utility file (`svg-icons.ts`) | Zero DI, tree-shakeable, pure functions | **Chosen** |
| C: Pass via @Input from parent | Couples parent to all icon names | Rejected |

**Rationale**: The SVGS map is pure static data with no runtime state. A utility file with `svg(name, className)` and `svgRaw(name)` functions preserves the exact API used in templates (`[innerHTML]="svg('search')"`) without requiring injection. Each sub-component imports directly.

### Decision: Hover Delay Pattern

| Option | Tradeoff | Decision |
|--------|----------|----------|
| A: Duplicate timeout logic per component | Repeats 3x the same setTimeout/clearTimeout pattern | Rejected |
| B: `HoverDelayDirective` (`[appHoverDelay]`) | Reusable, encapsulates enter/leave timers, testable in isolation | **Chosen** |
| C: Shared service for hover state | Overkill for UI-only concern | Rejected |

**Rationale**: The codebase has 3 identical hover-timeout patterns (mega menu, language dropdown, user menu). A structural directive with `@Input() appHoverDelayOpen` (boolean binding) and `@Output() appHoverDelayOpenChange` (two-way) encapsulates the 150ms open / 200ms close grace period. Components bind `[(appHoverDelayOpen)]="isOpen"` and own only the boolean.

### Decision: Component Communication

| Pattern | When to use |
|---------|-------------|
| `@Input` / `@Output` | Sub-components that need data from orchestrator (MegaMenu ← categories, MobileMenu ← isOpen) |
| Direct service injection | Sub-components that own their data (CartBadge ← CartService, ThemeToggle ← ThemeService, UserMenu ← AuthService) |
| `ActivatedRoute` | NavigationComponent reads `gender` query param directly — no parent involvement |

**Rationale**: Services already exist as singletons (`providedIn: 'root'`). Sub-components that only read service state inject directly — no need to pipe through the parent. This keeps Header free of subscription management.

### Decision: CategoryService Caching

| Option | Tradeoff | Decision |
|--------|----------|----------|
| A: `BehaviorSubject` + manual cache flag | Matches existing CartService pattern | **Chosen** |
| B: `shareReplay(1)` on HTTP observable | Simpler but no explicit cache control | Rejected |
| C: Signal-based | Inconsistent with CartService/WishlistService | Rejected |

**Rationale**: CartService and WishlistService both use `BehaviorSubject`. CategoryService follows the same pattern for consistency. `load()` checks if cache is populated before issuing HTTP. Errors are logged to `console.error` and surfaced via the observable error channel (no silent swallow).

## Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│  Header (orchestrator — template only, ~100 lines TS)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │MegaMenu  │ │Navigation│ │CartBadge │ │WishBadge │       │
│  │          │ │          │ │          │ │          │        │
│  │CategorySvc│ │ActivRte │ │CartSvc   │ │WishlistSvc│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │UserMenu  │ │LangSwitch│ │CurrSwitch│ │ThemeTogl │       │
│  │          │ │          │ │          │ │          │        │
│  │AuthSvc   │ │Translate │ │CurrencySvc│ │ThemeSvc │        │
│  │AuthState │ │          │ │          │ │          │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────────────────────────────────┐                    │
│  │MobileMenu (receives [isOpen],        │                    │
│  │ [categories] via @Input)             │                    │
│  └──────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

Header injects only: `Router` (for search navigation), `TranslateService` (for search), and `CategoryService` (passes categories to MegaMenu + MobileMenu via `@Input`). Total: 3 services (down from 12).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/app/core/services/category.service.ts` | Create | Category loading + in-memory cache |
| `frontend/src/app/shared/utils/svg-icons.ts` | Create | SVG map + `svg()` / `svgRaw()` pure functions |
| `frontend/src/app/shared/directives/hover-delay.directive.ts` | Create | Reusable hover open/close with configurable delays |
| `frontend/src/app/layout/header/components/mega-menu/` | Create | MegaMenuComponent (.ts, .html, .scss) |
| `frontend/src/app/layout/header/components/navigation/` | Create | NavigationComponent (.ts, .html, .scss) |
| `frontend/src/app/layout/header/components/cart-badge/` | Create | CartBadgeComponent (.ts, .html) |
| `frontend/src/app/layout/header/components/wishlist-badge/` | Create | WishlistBadgeComponent (.ts, .html) |
| `frontend/src/app/layout/header/components/user-menu/` | Create | UserMenuComponent (.ts, .html, .scss) |
| `frontend/src/app/layout/header/components/language-switcher/` | Create | LanguageSwitcherComponent (.ts, .html) |
| `frontend/src/app/layout/header/components/currency-switcher/` | Create | CurrencySwitcherComponent (.ts, .html) |
| `frontend/src/app/layout/header/components/theme-toggle/` | Create | ThemeToggleComponent (.ts, .html) |
| `frontend/src/app/layout/header/components/mobile-menu/` | Create | MobileMenuComponent (.ts, .html, .scss) |
| `frontend/src/app/layout/header/header.ts` | Modify | Reduce to orchestrator (~100 lines) |
| `frontend/src/app/layout/header/header.html` | Modify | Replace inline markup with sub-component selectors |
| `frontend/src/app/layout/header/header.scss` | Modify | Move animations to respective sub-component SCSS files |

## Interfaces / Contracts

```typescript
// ── CategoryService ──
@Injectable({ providedIn: 'root' })
export class CategoryService {
  readonly categories$: Observable<Category[]>;
  load(): void; // fetches GET /api/categories?lang=es, caches result
}

// ── Sub-component contracts ──

// MegaMenuComponent
@Input() categories: Category[] = [];
@Output() categorySelected = new EventEmitter<Category>();

// NavigationComponent — no @Input, reads ActivatedRoute.queryParamMap directly
@Output() genderChanged = new EventEmitter<string>();

// CartBadgeComponent — injects CartService directly
@Output() clicked = new EventEmitter<void>();

// WishlistBadgeComponent — injects WishlistService + AuthStateService directly
@Output() clicked = new EventEmitter<void>();

// UserMenuComponent — injects AuthService, AuthStateService directly
@Output() loginClicked = new EventEmitter<void>();
@Output() logoutCompleted = new EventEmitter<void>();

// LanguageSwitcherComponent — injects TranslateService directly
@Output() languageChanged = new EventEmitter<string>();

// CurrencySwitcherComponent — injects CurrencyService directly
@Output() currencyChanged = new EventEmitter<CurrencyCode>();

// ThemeToggleComponent — injects ThemeService directly
@Output() themeChanged = new EventEmitter<ThemeMode>();

// MobileMenuComponent
@Input() isOpen = false;
@Input() categories: Category[] = [];
@Output() closed = new EventEmitter<void>();
```

### HoverDelayDirective Contract

```typescript
@Directive({ selector: '[appHoverDelay]' })
export class HoverDelayDirective {
  @Input() appHoverDelayOpen = false;
  @Output() appHoverDelayOpenChange = new EventEmitter<boolean>();
  @Input() openDelay = 150;   // ms
  @Input() closeDelay = 200;  // ms
  // Binds (mouseenter)/(mouseleave) on host, manages setTimeout internally
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit — CategoryService | Cache hit on second `load()`, error propagation | `HttpClientTestingModule`, verify no second HTTP call |
| Unit — HoverDelayDirective | Open after delay, close after grace period, cancel on re-enter | `fakeAsync` + `tick()` |
| Unit — MegaMenuComponent | Renders category groups, emits on click, hover opens/closes | Mock CategoryService, `fakeAsync` for hover |
| Unit — CartBadge / WishlistBadge | Badge hidden at 0, shows count, click emits | Mock CartService/WishlistService BehaviorSubjects |
| Unit — UserMenu | Shows login when logged out, user info + logout when logged in | Mock AuthStateService signals |
| Unit — LanguageSwitcher | Cycles es→en→sv→es, calls TranslateService.use() | Mock TranslateService |
| Unit — ThemeToggle | Calls ThemeService.toggle(), emits themeChanged | Mock ThemeService |
| Unit — MobileMenu | Renders when isOpen=true, emits closed on backdrop click | Pure @Input/@Output test |
| Integration — Header orchestrator | All 9 sub-components instantiate, categories flow to MegaMenu + MobileMenu | `TestBed` with mocked services |

## Migration / Rollout

Phased implementation to keep each PR under 400 lines:

| Phase | Scope | Est. Lines | Files |
|-------|-------|-----------|-------|
| 1 | CategoryService + svg-icons.ts + hover-delay directive | ~120 | 3 new |
| 2 | Leaf components: ThemeToggle, LanguageSwitcher, CurrencySwitcher | ~180 | 6 new |
| 3 | Badge + menu components: CartBadge, WishlistBadge, UserMenu | ~200 | 6 new |
| 4 | Complex components: MegaMenu, Navigation | ~250 | 5 new |
| 5 | MobileMenu + Header orchestrator refactor | ~300 | 2 new + 3 modified |
| 6 | Cleanup: remove dead code from header.ts, update header.scss | ~-100 | 2 modified |

Each phase is an independent commit/PR. Phase 5 is the integration point where Header template switches to sub-component selectors.

## Open Questions

- [ ] Should `NavigationComponent` receive `GENDER_TABS` as a static constant or hardcode internally? (Leaning: internal constant — no parent needs this data)
- [ ] Should the promo panel in MegaMenu be configurable via `@Input` or hardcoded? (Leaning: hardcoded for now — matches current behavior, no i18n-driven content)
