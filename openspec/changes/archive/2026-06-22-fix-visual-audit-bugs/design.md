# Design: Fix Visual Audit Bugs

## Technical Approach

6-phase bottom-up execution: i18n foundation → field name fix → CSS tokens → dark components → switchers → polish. Each phase is independently verifiable via `pnpm run build`. The two cross-cutting root causes are: (1) `html.dark-theme` never overrides `--color-*` tokens (19 components stay light), (2) `t.lang` vs `t.language_code` field mismatch breaks all translation lookups.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Override `--color-*` vs add new tokens | Override the 4 existing tokens directly | 19+ components use `var(--color-*)` — overriding fixes them all atomically |
| `t.lang` → `t.language_code` | Fix all 5 public-facing files, leave admin-form internal form controls | Admin-form uses `t.lang` as Angular form control key, not API response field |
| Test teardown strategy | `SELECT slug FROM products WHERE slug LIKE 'boundary-%'` → DELETE per test | Per-test cleanup avoids cross-test contamination; patterns match exactly what each test inserts |
| Wave SVG fill | `fill="currentColor"` + `class="text-[var(--color-bg)]"` | CSS variable approach keeps SVG inline; no JS needed |
| ngx-translate fix | Remove `defaultLanguage` from `forRoot()`, keep `setDefaultLang('es')` in `AppComponent` | Deprecated in v14; runtime init is the supported API |

## Phase Execution Order

**P1** (i18n + ngx-translate) → **P1.5** (field rename) → **P2** (CSS tokens) → **P3** (dark components) → **P4** (switchers) → **P5** (data + seed + teardown) → **P6** (polish)

Rationale: P1.5 field rename unlocks displayName for all later phases. P2 CSS tokens fix hero/checkout/cards in one pass before P3 incremental component fixes. P5 seed/teardown is backend-only and can run last.

## Phase 1: i18n Foundation

### New `auth` section (exact JSON shape)

Added to `es.json` / `en.json` / `sv.json`:

```json
"auth": {
  "signIn": "Iniciar Sesión",
  "email": "Correo electrónico",
  "emailRequired": "El correo es obligatorio",
  "emailInvalid": "Ingresa un correo válido",
  "password": "Contraseña",
  "passwordRequired": "La contraseña es obligatoria",
  "passwordMinLength": "Al menos 8 caracteres",
  "signInButton": "Iniciar Sesión",
  "signInGoogle": "Iniciar sesión con Google",
  "noAccount": "¿No tienes cuenta?",
  "register": "Registrarse",
  "loginFailed": "Error al iniciar sesión",
  "createAccount": "Crear Cuenta",
  "name": "Nombre",
  "nameRequired": "El nombre es obligatorio",
  "confirmPassword": "Confirmar Contraseña",
  "confirmRequired": "Confirma tu contraseña",
  "passwordMismatch": "Las contraseñas no coinciden",
  "createAccountButton": "Crear Cuenta",
  "hasAccount": "¿Ya tienes cuenta?",
  "registrationFailed": "Error al registrarse"
}
```

### Template changes

- **login.html**: 9 strings → `{{ 'auth.key' | translate }}` (reference pattern: checkout.html). p-card `header` attribute → `[header]="'auth.signIn' | translate"`. p-button `label` → `[label]="'auth.signInButton' | translate"`.
- **register.html**: 13 strings, same pattern. Validation errors use `*ngIf` with translated content. p-card header → `[header]="'auth.createAccount' | translate"`.
- **login.ts L49**: `'Login failed'` → `'auth.loginFailed'`
- **register.ts L50**: `'Registration failed'` → `'auth.registrationFailed'`

### ngx-translate fix

- `app-module.ts L25`: `TranslateModule.forRoot({ defaultLanguage: 'es' })` → `TranslateModule.forRoot()`

## Phase 1.5: Field Name Fix (`t.lang` → `t.language_code`)

| File | Line(s) | Change |
|------|---------|--------|
| `product-card.ts` | L76, L78 | `t.lang` → `t.language_code` (2 occurrences) |
| `home.ts` | L77, L82 | `t.lang` → `t.language_code` + L76-79 rewrite |
| `product-detail.ts` | L232, L234, L250, L252 | `t.lang` → `t.language_code` (4 occurrences) |
| `admin-products.ts` | L66, L86 | `t.lang` → `t.language_code` (2 occurrences) |
| `product-basic-info.component.ts` | L23 | `t.lang` → `t.language_code` |

### getCategoryName() rewrite

```typescript
// Before: iterates cat.translations[] (field doesn't exist in list endpoint)
getCategoryName(cat: any): string {
  const t = cat?.translations?.find((t: any) => t.lang === 'es');
  return t?.name ?? '';
}

// After: uses flat cat.name (API /categories?lang=es returns pre-translated name)
getCategoryName(cat: any): string {
  return cat?.name ?? '';
}
```

## Phase 2: Dark Mode CSS Variables

### styles.scss `html.dark-theme` changes

```scss
html.dark-theme {
  // Override design tokens — these cascade to all var(--color-*) consumers
  --color-bg: #0f172a;              // slate-900
  --color-text: #f1f5f9;            // slate-100
  --color-text-secondary: #94a3b8;  // slate-400
  --color-primary: #4ade80;         // green-400

  // Keep existing custom tokens (used by scoped components)
  --bg-primary: #1e1e2e;
  --bg-secondary: #2a2a3c;
  --text-primary: #cdd6f4;
  --text-secondary: #a0a0b0;

  color-scheme: dark;

  body {
    background-color: var(--color-bg);
    color: var(--color-text);
  }
}
```

### home.html changes

- **Hero gradient (L4)**: add `dark:from-gray-950 dark:via-emerald-950 dark:to-teal-950`
- **Wave SVG (L76)**: `fill="#FAF9F6"` → `fill="currentColor" class="text-[var(--color-bg)]"`

## Phase 3: Dark Mode Components

### Checkout (14 elements)

| Element | Before | After |
|---------|--------|-------|
| H1 title | `text-gray-900` | `text-gray-900 dark:text-gray-100` |
| Overlay card | `bg-white` | `bg-white dark:bg-gray-800` |
| Overlay text | `text-gray-700` | `text-gray-700 dark:text-gray-300` |
| Error msg | `text-red-600` | `text-red-600 dark:text-red-400` |
| Shipping card | `bg-white` | `bg-white dark:bg-gray-800` |
| H2 shipping | (none) | `dark:text-gray-100` |
| Summary card | `bg-white` | `bg-white dark:bg-gray-800` |
| H2 summary | (none) | `dark:text-gray-100` |
| Item divider | `divide-gray-200` | `divide-gray-200 dark:divide-gray-700` |
| Product name | `text-gray-900` | `text-gray-900 dark:text-gray-100` |
| Quantity label | `text-gray-500` | `text-gray-500 dark:text-gray-400` |
| Total label | (none) | `dark:text-gray-100` |
| Total amount | (none) | `dark:text-gray-100` |
| Bottom divider | `border-gray-200` | `border-gray-200 dark:border-gray-700` |

Light mode: zero visual change — `dark:` variants are inert without `.dark-theme`.

### ProductCard condition badges

```typescript
const CONDITION_COLORS: Record<string, string> = {
  new:       'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700',
  like_new:  'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 border-blue-300 dark:border-blue-700',
  good:      'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700',
  fair:      'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700',
  fallback:  'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600',
};
```

### ProductCard shadow (product-card.scss)

```scss
&:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);

  :host-context(.dark-theme) & {
    box-shadow: 0 12px 32px rgba(255, 255, 255, 0.06);
  }
}
```

## Phase 4: Language + Currency Switcher

### language-switcher.component.ts changes

```typescript
// Inject ElementRef
private readonly elementRef = inject(ElementRef);

// Click-outside
@HostListener('document:click', ['$event'])
onDocumentClick(event: MouseEvent): void {
  if (!this.elementRef.nativeElement.contains(event.target)) {
    this.langOpen = false;
    this.cdr.markForCheck();
  }
}

// Fix setLang (add markForCheck + close)
protected setLang(lang: string): void {
  this.translate.use(lang);
  this.langOpen = false;
  this.cdr.markForCheck();
}

// OnPush refresh via onLangChange subscription (add in ngOnInit)
this.langSub = this.translate.onLangChange.subscribe(() => this.cdr.markForCheck());
```

Same pattern for `currency-switcher.component.ts`: inject `ElementRef`, add `@HostListener`, `cdr.markForCheck()` in `setCurrency()`, subscribe to `currencyService.onCurrencyChange`.

## Phase 5: Data Fixes

### Seed scripts: Spanish category translations

Both `seed_dataset.py` L152-153 and `seed_parquet.py` L99-100 insert ES name = English name. Add a mapping dict:

```python
CATEGORY_ES: dict[str, str] = {
    "Accessories": "Accesorios", "Bag": "Bolso", "Belt": "Cinturón",
    "Blazer": "Chaqueta", "Blouse": "Blusa", "Boots": "Botas",
    "Cardigan": "Cárdigan", "Coat": "Abrigo", "Dress": "Vestido",
    "Hat": "Sombrero", "Heels": "Tacones", "Jacket": "Chaqueta",
    "Jeans": "Vaqueros", "Jumpsuit": "Mono", "Pants": "Pantalones",
    # ... full 30+ mapping
}
# Usage:
es_name = CATEGORY_ES.get(type_name, type_name)
session.add(CategoryTranslation(category_id=cat.id, language_code="es", name=es_name))
```

### Test teardown

Per-test cleanup in `test_seed_integrity.py`. At the end of each test that inserts products:

```python
# Delete products inserted by this test
slugs_to_delete = await session.execute(
    select(Product.slug).where(
        Product.slug.like(f"boundary-{uid}%") |
        Product.slug.like(f"roundtrip-{uid}%") |
        Product.slug.like(f"empty-cond-{uid}%")
        # ... per-test pattern
    )
)
for (slug,) in slugs_to_delete:
    await session.execute(delete(Product).where(Product.slug == slug))
await session.commit()
```

Alternative: use `_uid()` prefix stored per test and deleted in a `try/finally` block.

## Phase 6: Polish

### common.notApplicable keys

| key | es | en | sv |
|-----|----|----|-----|
| `common.notApplicable` | No especificado | Not specified | Ej specificerat |

### Hero placeholder images

Replace broken `<img>` in hero decorative cards with inline SVG icons (no network dependency). Use `<i class="pi pi-image text-3xl text-white/40">` already shown in the fallback branch as a permanent replacement, removing the `*ngIf="!card.image_urls?.[0]"` condition.

## File Manifest

| Phase | File | Action | ~Lines |
|-------|------|--------|--------|
| P1 | `es.json` | +`auth` section | +22 |
| P1 | `en.json` | +`auth` section | +22 |
| P1 | `sv.json` | +`auth` section | +22 |
| P1 | `login/login.html` | Replace 9 strings → translate | ~15 changed |
| P1 | `register/register.html` | Replace 13 strings → translate | ~22 changed |
| P1 | `login/login.ts` | L49 error fallback | 1 |
| P1 | `register/register.ts` | L50 error fallback | 1 |
| P1 | `app-module.ts` | Remove `defaultLanguage` | 1 |
| P1.5 | `product-card/product-card.ts` | L76,78 `t.lang`→`t.language_code` | 2 |
| P1.5 | `home/home.ts` | L76-79 rewrite + L82 fix | ~5 |
| P1.5 | `product-detail/product-detail.ts` | L232,234,250,252 | 4 |
| P1.5 | `admin/admin-products.ts` | L66,86 | 2 |
| P1.5 | `admin/.../product-basic-info.component.ts` | L23 | 1 |
| P2 | `styles.scss` | Override `--color-*` in dark-theme | +5 |
| P2 | `home/home.html` | Hero gradient + wave SVG | +2 lines |
| P3 | `checkout/checkout.html` | 14 `dark:` variants | ~14 changed |
| P3 | `product-card/condition-badge.component.ts` | Dark variants in 5 entries | ~5 changed |
| P3 | `product-card/product-card.scss` | `:host-context(.dark-theme)` shadow | +3 |
| P4 | `language-switcher.component.ts` | ElementRef + HostListener + sub | +15 |
| P4 | `currency-switcher.component.ts` | Same pattern | +15 |
| P5 | `seed_dataset.py` | ES category translations | +10 |
| P5 | `seed_parquet.py` | ES category translations | +10 |
| P5 | `test_seed_integrity.py` | Per-test teardown | +30 |
| P6 | `es.json` | `common.notApplicable` | +1 |
| P6 | `en.json` | `common.notApplicable` | +1 |
| P6 | `sv.json` | `common.notApplicable` | +1 |
| P6 | `home/home.html` | Hero placeholder → permanent SVG fallback | ~4 |

## Testing Strategy

| Phase | Verification |
|-------|-------------|
| P1 | `pnpm run build` — zero TS errors. `/login` renders Spanish. `/register` renders Spanish. |
| P1.5 | Product card on home shows Spanish names (not slug fallback). Category carousel shows Spanish labels. |
| P2 | Toggle dark mode → hero background switches, wave SVG matches page bg. |
| P3 | Toggle dark mode → checkout readable, product card badges + shadow adapt. |
| P4 | Open language dropdown, click outside → closes. Select language → badge updates immediately. |
| P5 | Re-seed → categories display Spanish. Run tests → no test products on home. |
| P6 | Empty product field shows "No especificado" in ES. |
| Final | `pnpm run build` pass, Playwright smoke on 8 routes, console: 0 errors 0 warnings. |
