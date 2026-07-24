# Tasks: Fix Visual Audit Bugs

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~236 |
| 400-line budget risk | Low |
| Chained PRs recommended | Yes |
| Delivery strategy | auto-chain |
| Chain strategy | pending |
| Decision needed before apply | Yes |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Base | Lines |
|------|------|-----------|------|-------|
| 1 | i18n + field name fix | PR 1 | main | ~120 |
| 2 | Dark mode CSS + components | PR 2 | main | ~40 |
| 3 | Switcher fixes | PR 3 | main | ~30 |
| 4 | Data fixes | PR 4 | main | ~50 |
| 5 | Polish | PR 5 | main | ~7 |

## Phase 1: i18n Foundation

- [x] **1.1** Add `auth` section (22 keys) to `src/assets/i18n/es.json`
- [x] **1.2** Add `auth` section (22 keys) to `src/assets/i18n/en.json`
- [x] **1.3** Add `auth` section (22 keys) to `src/assets/i18n/sv.json`
- [x] **1.4** Replace 9 hardcoded strings with `{{ 'auth.key' | translate }}` in `login.html`
- [x] **1.5** Replace 13 hardcoded strings with translate pipe in `register.html`
- [x] **1.6** `login.ts` L49: `'Login failed'` → `'auth.loginFailed'`
- [x] **1.7** `register.ts` L50: `'Registration failed'` → `'auth.registrationFailed'`
- [x] **1.8** Remove `defaultLanguage: 'es'` from app-module.ts `TranslateModule.forRoot()`

**Verify**: `pnpm run build` + Playwright /login renders Spanish labels + 0 console warnings

## Phase 1.5: Field Name Fix

- [x] **1.9** Fix `t.lang` → `t.language_code` in `product-card.ts` L76, L78
- [x] **1.10** Fix `t.lang` → `t.language_code` in `home.ts` L77, L82
- [x] **1.11** Fix `t.lang` → `t.language_code` in `product-detail.ts` L232, L234, L250, L252
- [x] **1.12** Fix `t.lang` → `t.language_code` in `admin-products.ts` L66, L86
- [x] **1.13** Fix `t.lang` → `t.language_code` in `product-basic-info.component.ts` L23
- [x] **1.14** Rewrite `getCategoryName()` in `home.ts` to use flat `cat.name` directly

**Verify**: `pnpm run build` + Playwright home shows Spanish category names

## Phase 2: Dark Mode CSS Variables

- [x] **2.1** Override `--color-*` tokens in `styles.scss` `html.dark-theme` block
- [x] **2.2** Add `dark:from-gray-950 dark:via-emerald-950 dark:to-teal-950` to hero gradient `home.html` L4
- [x] **2.3** Wave SVG: `fill="currentColor"` + `class="text-[var(--color-bg)]"` in `home.html` L76

**Verify**: Playwright toggle dark mode → hero background + wave adapt

## Phase 3: Dark Mode Components

- [x] **3.1** Add 14 `dark:` variant classes to `checkout.html` (h1, cards, headings, borders, dividers)
- [x] **3.2** Add `dark:bg-*-900/40 dark:text-*-200 dark:border-*-700` to all 5 `CONDITION_COLORS` entries
- [x] **3.3** Add `:host-context(.dark-theme)` light-shadow override in `product-card.scss` hover

**Verify**: Playwright dark mode on checkout + product card badges and shadow adapt

## Phase 4: Switcher Fixes

- [x] **4.1** `language-switcher.component.ts`: inject ElementRef, add `@HostListener('document:click')`, `markForCheck()` in setLang, subscribe `onLangChange`
- [x] **4.2** `currency-switcher.component.ts`: same pattern (ElementRef, HostListener, markForCheck, onCurrencyChange)

**Verify**: Playwright click outside closes dropdown, language change updates badge immediately

## Phase 5: Data Fixes

- [x] **5.1** Add `CATEGORY_ES` mapping dict + ES insert in `seed_dataset.py`
- [x] **5.2** Add `CATEGORY_ES` mapping dict + ES insert in `seed_parquet.py`
- [x] **5.3** Add per-test teardown (DELETE by slug pattern) in `test_seed_integrity.py` for all 8 patterns
- [x] **5.4** One-time SQL: `DELETE FROM products WHERE slug LIKE 'boundary-%' OR slug LIKE 'empty-cond-%' OR ...`

**Verify**: Backend tests pass, re-seed → translated categories, 0 test products visible

## Phase 6: Polish

- [x] **6.1** Add `common.notApplicable` key to `es.json` / `en.json` / `sv.json`
- [x] **6.2** Replace "Not Applicable" literal with `{{ 'common.notApplicable' | translate }}` in product-card brand/material fallback
- [x] **6.3** Replace broken `<img>` in hero decorative cards with inline SVG icon fallback (no network dep)

**Verify**: `pnpm run build` + Playwright hero cards show icons, empty field shows "No especificado"
