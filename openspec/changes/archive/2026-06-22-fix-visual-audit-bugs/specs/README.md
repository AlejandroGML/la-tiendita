# Specs for `fix-visual-audit-bugs`

Delta specs covering 4 modified capabilities that fix the 9 visual audit bugs found in `AUDIT_VISUAL_REPORT.md` and prioritized in `.opencode/plans/fix-9-bugs.md`.

## Specs

| Capability | Type | File | Requirements | Scenarios | Bugs Covered |
|---|---|---|---|---|---|
| `auth` | Delta (all ADDED) | [auth/spec.md](./auth/spec.md) | 5 | 8 | C1, m1 |
| `frontend-core` | Delta (2 MODIFIED, 4 ADDED) | [frontend-core/spec.md](./frontend-core/spec.md) | 6 | 11 | C2, C4, M4, displayName field |
| `checkout` | Delta (all ADDED) | [checkout/spec.md](./checkout/spec.md) | 2 | 5 | C3 |
| `product-catalog` | Delta (all ADDED) | [product-catalog/spec.md](./product-catalog/spec.md) | 6 | 14 | M1, M2, M3, M5, m1 |

## Bug → Spec Mapping

| Bug | Severity | Spec / Requirement |
|---|---|---|
| C1 — Login/Register 100% English | CRITICAL | `auth` (5 requirements) |
| C2 — Hero dark mode | CRITICAL | `frontend-core` → Dark Mode Theme Toggle (UPDATED) |
| C3 — Checkout dark mode unreadable | CRITICAL | `checkout` (2 requirements) |
| C4 — Language switcher broken | CRITICAL | `frontend-core` → Language Switcher (2 requirements) |
| M1 — Categories in English | MEDIUM | `product-catalog` → Category Carousel + Display Name Chain |
| M2 — Test products on home | MEDIUM | `product-catalog` → Test Fixture Products Are Not Visible |
| M3 — Catalog = test fixtures | MEDIUM | `product-catalog` → Test Fixture Products Are Not Visible |
| M4 — ngx-translate deprecation | MEDIUM | `frontend-core` → ngx-translate Internationalization (UPDATED) |
| M5 — Product cards light in dark | MEDIUM | `product-catalog` → Product Cards Legible in Dark Mode + Condition Badges |
| m1 — "Not Applicable" untranslated | MINOR | `auth` (Backend Auth Errors) + `product-catalog` → Not Applicable Displays as Localized Fallback |
| displayName field mismatch (`t.lang` vs `t.language_code`) | CRITICAL root cause | `frontend-core` → Translation Lookups Use `t.language_code` |
| Currency switcher broken (same as C4) | CRITICAL | `frontend-core` → Currency Switcher (2 requirements) |

## Notes

- Most changes are **ADDED** requirements because the existing specs are backend-focused and lack frontend rendering, dark-mode, and i18n-pipeline behaviors.
- The two MODIFIED requirements in `frontend-core` (ngx-translate config and dark-mode tokens) replace existing wording with the corrected behavior; downstream archive step will swap the corresponding blocks in `openspec/specs/frontend-core/spec.md`.
- The `auth` and `checkout` capabilities do not need MODIFIED entries because no prior frontend-rendering requirement exists for those pages.
- The `product-catalog` spec gets six new ADDED entries covering category resolution, display-name fallback chain, dark-mode legibility, condition badges, Not Applicable i18n, and test-fixture cleanup.

## Next Phase

Ready for `sdd-design` — define the technical approach for each phase (CSS variable overrides, OnPush subscription pattern, i18n key taxonomy, teardown strategy).
