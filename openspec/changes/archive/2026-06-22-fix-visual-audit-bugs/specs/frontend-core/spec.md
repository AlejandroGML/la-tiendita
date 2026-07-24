# Delta for frontend-core

> **Capability**: frontend-core
> **Driver**: C2, C4, M4, displayName field

## ADDED Requirements

### Requirement: Language Switcher Closes on Outside Click

The `LanguageSwitcherComponent` MUST close its dropdown on `document:click` outside the host element.

#### Scenario: Click outside closes dropdown

- GIVEN the dropdown is open showing ES/EN/SV
- WHEN the user clicks anywhere outside the switcher
- THEN the dropdown closes immediately

#### Scenario: OnLangChange refreshes OnPush

- GIVEN the switcher uses OnPush change detection
- WHEN `translate.onLangChange` fires
- THEN the switcher calls `markForCheck()` and the badge updates

### Requirement: Language Switcher Changes Language and Updates Badge

Selecting a language option MUST call `translate.use(lang)` and update the visible badge (e.g. "ES" → "EN") via `markForCheck()`.

#### Scenario: Selecting English updates badge

- GIVEN current language is Spanish and badge shows "ES"
- WHEN the user selects English
- THEN `translate.use('en')` is called AND the badge updates to "EN" without a page reload

### Requirement: Currency Switcher Closes on Outside Click

The `CurrencySwitcherComponent` MUST close its dropdown on `document:click` outside the host element.

#### Scenario: Click outside closes currency dropdown

- GIVEN the currency dropdown is open
- WHEN the user clicks outside the switcher
- THEN the dropdown closes

### Requirement: Currency Switcher Changes Currency and Updates Badge

Selecting a currency MUST update the currency service and refresh the badge.

#### Scenario: Selecting EUR updates badge

- GIVEN current currency is SEK (badge "kr")
- WHEN the user selects EUR
- THEN the badge updates to "€" without a page reload

### Requirement: Translation Lookups Use `t.language_code`

Frontend code reading a `translations[]` entry MUST access the language via `t.language_code` (backend contract), NOT `t.lang` (stale field).

#### Scenario: ProductCard displayName lookup

- GIVEN a product has `translations:[{language_code:"es",name:"Chaqueta"}]`
- WHEN the card renders in Spanish
- THEN the lookup uses `t.language_code === 'es'` and shows "Chaqueta"

#### Scenario: Home getCategoryName uses flat `cat.name`

- GIVEN `/api/categories?lang=es` returns `{slug,name:"Chaquetas"}` (flat)
- WHEN `getCategoryName(cat)` runs
- THEN it returns `cat.name` directly (not `cat.translations[i].name`)

## MODIFIED Requirements

### Requirement: ngx-translate Internationalization (UPDATED)

`TranslateModule.forRoot()` MUST NOT pass `defaultLanguage` (deprecated since v14). The runtime default SHALL be set via `translate.setDefaultLang('es')` in `AppComponent` only. `auth.*` keys SHALL exist in all three locale files.
(Previously: `forRoot({defaultLanguage:'es'})` produced a deprecation warning.)

#### Scenario: No deprecation warnings on boot

- GIVEN `forRoot()` has no `defaultLanguage` AND `AppComponent` calls `setDefaultLang('es')` once
- WHEN the app loads
- THEN console shows zero warnings about `defaultLanguage` or `useDefaultLang`

#### Scenario: Auth keys resolve

- GIVEN `auth.*` keys exist in es/en/sv
- WHEN login or register renders in any of the three languages
- THEN `auth.*` keys resolve and text appears in the selected language

### Requirement: Dark Mode Theme Toggle (UPDATED)

The `ThemeService` toggles a `dark-theme` class on `<html>`. State persists to `localStorage`. Falls back to `prefers-color-scheme`. **Critical**: `html.dark-theme` MUST override the design tokens `--color-bg`, `--color-text`, `--color-text-secondary`, and `--color-primary` so every component reading `var(--color-*)` switches to dark values. Components MUST NOT hardcode light colors when a token exists.
(Previously: `html.dark-theme` defined new `--bg-primary`/`--text-primary` without overriding `--color-*` — 19 components stayed light.)

#### Scenario: Design tokens overridden in dark mode

- GIVEN `html.dark-theme` is active
- WHEN a component reads `var(--color-bg)`, `var(--color-text)`, `var(--color-text-secondary)`, or `var(--color-primary)`
- THEN the value resolves to a dark-mode-appropriate color

#### Scenario: Storefront sections using `--color-*` adapt

- GIVEN hero, product cards, and carousel use `var(--color-*)` tokens
- AND `html.dark-theme` is active
- WHEN the home page renders
- THEN all sections using these tokens show dark backgrounds and light text
