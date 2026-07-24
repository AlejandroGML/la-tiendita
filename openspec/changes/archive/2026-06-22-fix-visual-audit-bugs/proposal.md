# Proposal: Fix Visual Audit Bugs

## Intent

Post-refactor audit found 9 bugs (4 critical, 5 medium) blocking production: login/register 100% English, dark mode broken (hero/checkout/cards), language switcher non-functional, untranslated categories, test data in views. Two cross-cutting root causes: (1) `--color-*` CSS tokens never overridden in `html.dark-theme` (19 broken locations); (2) field mismatch `t.lang` vs `t.language_code` breaks translation lookups.

## Scope

### In Scope
- Login/Register i18n: `auth` keys (~22 per locale), replace hardcoded strings
- Dark mode CSS: override `--color-*` tokens in `html.dark-theme`
- Dark mode components: checkout `dark:` variants, product-card `CONDITION_COLORS` + shadow
- Language/currency switcher: click-outside, `markForCheck()`, `onLangChange` sub
- Category translations: `getCategoryName()` use flat `cat.name`
- Test data cleanup: teardown in tests, delete ~60 fixtures
- ngx-translate: `defaultLanguage` → `fallbackLang`
- Polish: "Not Applicable" i18n, hero placeholders

### Out of Scope
- Product detail value translations (data migration)
- Backend API schema changes

## Capabilities

### New Capabilities
None

### Modified Capabilities
- `auth`: Login/Register must use `| translate` with `auth.*` keys
- `frontend-core`: Dark mode must override `--color-*` tokens; switchers must close on outside click + OnPush refresh; ngx-translate non-deprecated API
- `checkout`: 14 elements need `dark:` variants
- `product-catalog`: `getCategoryName()`/`getDisplayName()` must use `t.language_code` + flat `cat.name`; seed scripts insert ES translations; test teardown cleans fixtures

## Approach

6-phase: (1) i18n + field rename, (2) dark CSS vars, (3) dark components, (4) switchers, (5) data fixes, (6) polish.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `--color-*` override breaks unaudited components | Low | `grep` audit first |
| Test teardown breaks assertions | Med | Per-test teardown |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/assets/i18n/{es,en,sv}.json` | Modified | Add `auth` + `common.notApplicable` |
| `src/app/features/auth/{login,register}/` | Modified | Replace ~22 hardcoded strings |
| `src/styles.scss` | Modified | `--color-*` overrides |
| `src/app/features/home/home.{html,ts}` | Modified | Hero `dark:` + field fix |
| `src/app/features/checkout/checkout.html` | Modified | 14 `dark:` variants |
| `src/app/shared/components/product-card/` | Modified | Colors, shadow, field fix |
| `src/app/layout/header/components/*-switcher.component.ts` | Modified | Click-outside + `markForCheck()` |
| `src/app/app-module.ts` | Modified | Remove deprecated config |
| `backend/scripts/seed_*.py` | Modified | ES category translations |
| `backend/tests/test_seed_integrity.py` | Modified | Teardown cleanup |

## Rollback Plan

All frontend + seed changes. `git revert` on merge. No DB migrations. Dark mode CSS revertable independently.

## Dependencies

None external. Requires `pnpm` for build verification.

## Success Criteria

- [ ] Login/Register fully translated ES/EN/SV
- [ ] Dark mode: hero/checkout/cards adapt correctly
- [ ] Language/currency switchers close on outside click, change immediately
- [ ] Categories display translated names
- [ ] Zero test products in home/catalog
- [ ] Console: 0 errors, 0 warnings
- [ ] `pnpm run build` passes
