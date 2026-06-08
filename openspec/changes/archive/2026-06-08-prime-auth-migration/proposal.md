# Proposal: PrimeNG Auth Pages Migration — Phase 5

## Intent

Replace Angular Material components on Login and Register pages with PrimeNG equivalents. Pure template swap — no new modules, no TypeScript changes, no service migrations. All required PrimeNG modules (CardModule, InputTextModule, FloatLabelModule, ButtonModule) already exported via PrimeNgModule→SharedModule→AuthModule chain.

## Scope

### In Scope
- **login.html**: 10 Material elements → PrimeNG (card, 2 form fields with labels+inputs+errors, 3 buttons)
- **register.html**: 10 Material elements → PrimeNG (card, 4 form fields with labels+inputs+errors, 2 buttons)
- **Validation**: error message display migrated from `mat-error` to `p-error` class with `*ngIf`

### Out of Scope
- **TypeScript files**: `login.ts`, `register.ts`, `auth-module.ts` — zero changes; unused Material imports retained
- **PrimeNgModule**: no module additions (14 modules already sufficient)
- **SharedModule**: no Material module removals
- **Google OAuth placeholder**: stays as-is (disabled `mat-stroked-button` staying commented)

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. This is a pure template refactor: no spec-level behavior changes. The `auth` spec requirements (form validation, submit flow, error display, navigation) remain unchanged.

## Approach

Pure HTML-only replacements per file, no TS or module changes.

### login.html (10 Material → PrimeNG)
| Material | PrimeNG |
|----------|---------|
| `<mat-card>` | `<p-card>` |
| `<mat-card-header>` / `<mat-card-content>` | `<ng-template pTemplate="header">` / content goes in body |
| `<mat-card-title>` | plain `<h2>` inside header template |
| `<mat-form-field appearance="outline">` | `<p-floatLabel variant="on">` |
| `<mat-label>Email</mat-label>` | n/a (floatLabel inline) |
| `<input matInput>` | `<input pInputText>` |
| `<mat-error *ngIf="...">` | `<small class="p-error" *ngIf="...">` |
| `<button mat-flat-button color="primary">` | `<p-button label="Sign In" [disabled]="..." [loading]="...">` |
| `<button mat-stroked-button>` | `<p-button [outlined]="true" [disabled]="true">` |
| `<a mat-button>` | `<a pButton [text]="true" routerLink="/register">` |

### register.html (10 Material → PrimeNG)
Same mapping as Login plus 2 extra form-field groups and the passwordsMismatch cross-field error. Confirm button uses `[loading]="submitting"`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `features/auth/login/login.html` | Modified | mat-card + 2 mat-form-fields + 3 mat-buttons → p-card + p-floatLabel + p-buttons |
| `features/auth/register/register.html` | Modified | mat-card + 4 mat-form-fields + 2 mat-buttons → p-card + p-floatLabel + p-buttons |

## Dependencies

- Phase 0 (prime-migration-setup): PrimeNG v21.1.9 installed
- Phases 1–4: CardModule, InputTextModule, FloatLabelModule, ButtonModule already in PrimeNgModule (14 modules)
- No new packages required

## Success Criteria

- [x] `ng build` compiles without errors or "not a known element" warnings
- [x] Login page: email + password fields render with float labels, Sign In button submits
- [x] Login page: validation errors display per field (required, email format, minlength)
- [x] Login page: server error message displays (invalid credentials)
- [x] Register page: all 4 fields render with float labels, Create Account button submits
- [x] Register page: validation errors display per field including passwords mismatch
- [x] Register page: navigation links ("Don't have an account?", "Already have an account?") navigate correctly
- [x] Dark mode: p-card, p-floatLabel, p-button follow `.dark-theme`
