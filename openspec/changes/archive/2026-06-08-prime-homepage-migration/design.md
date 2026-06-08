# Design: PrimeNG Homepage Migration — Phase 1

## Technical Approach

Replace 5 Material component usages across 2 templates with PrimeNG equivalents. Add 3 PrimeNG modules to the existing empty `PrimeNgModule` anchor. Material imports remain untouched in `SharedModule` — this is a pure template+style migration. Severity mapping follows the Aura preset color semantics.

## Architecture Decisions

### Decision: Severity mapping (Material → PrimeNG)

| Material color | PrimeNG severity | Rationale |
|---|---|---|
| `accent` | `help` | Aura `help` = purple/violet tones; matches accent role (hero CTA on purple gradient bg) |
| `primary` | `primary` | Direct semantic equivalent (blue/indigo) |
| `warn` | `danger` | Not used in this phase, documented for consistency |

### Decision: Button variant mapping

| Material directive | PrimeNG property | Rationale |
|---|---|---|
| `mat-flat-button` | `pButton` (default, no variant flag) | Both render solid filled buttons |
| `mat-stroked-button` | `pButton [outlined]="true"` | Direct visual equivalent — border with transparent fill |
| `mat-raised-button` | `pButton [raised]="true"` | Not used in this phase, documented for consistency |

### Decision: p-card template structure

| Material element | PrimeNG replacement |
|---|---|
| `<mat-card>` wrapper | `<p-card styleClass="...">` (styleClass passes CSS classes to root `.p-card` div) |
| `<img mat-card-image>` inside card root | `<ng-template pTemplate="header"><img ... /></ng-template>` |
| `<mat-card-content>` | `<ng-template pTemplate="content"><div>...</div></ng-template>` |

PrimeNG renders `pTemplate="header"` inside `.p-card-header` and `pTemplate="content"` inside `.p-card-body > .p-card-content`. The `styleClass` on `p-card` applies to the outermost `.p-card` wrapper, preserving `.product-card` + Tailwind classes.

### Decision: p-progressSpinner sizing

`mat-spinner diameter="48"` does not have a direct `diameter` input on `p-progressSpinner`. The spinner SVG fills its container via `viewBox="0 0 100 100"`. Solution: `[style]="{ width: '48px', height: '48px' }"` to set exact dimensions, matching the original 48×48px spinner.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/app/shared/primeng-module.ts` | Modify | Add ButtonModule, CardModule, ProgressSpinnerModule imports + exports |
| `frontend/src/app/shared/components/product-card/product-card.html` | Modify | Replace `mat-card`/`mat-card-image`/`mat-card-content` with `p-card` + `ng-template` structure |
| `frontend/src/app/shared/components/product-card/product-card.scss` | Modify | Replace `img[mat-card-image]` selector with `img` scoped to `.product-card` |
| `frontend/src/app/features/home/home.html` | Modify | Replace 1 `mat-flat-button`, 2 `mat-stroked-button`, 1 `mat-spinner` with PrimeNG equivalents |

## HTML Before/After

### ProductCard (`product-card.html`)

**Before:**
```html
<mat-card class="product-card w-full cursor-pointer hover:shadow-lg transition-shadow">
  <img mat-card-image [src]="imageUrl" [alt]="displayName" class="h-48 object-cover" loading="lazy" />
  <mat-card-content class="p-3">
    <!-- body content unchanged -->
  </mat-card-content>
</mat-card>
```

**After:**
```html
<p-card styleClass="product-card w-full cursor-pointer hover:shadow-lg transition-shadow">
  <ng-template pTemplate="header">
    <img [src]="imageUrl" [alt]="displayName" class="h-48 object-cover w-full" loading="lazy" />
  </ng-template>
  <ng-template pTemplate="content">
    <div class="p-3">
      <!-- body content unchanged -->
    </div>
  </ng-template>
</p-card>
```

### Homepage buttons (`home.html`)

**Before — mat-flat-button (hero CTA):**
```html
<a mat-flat-button color="accent" class="text-lg px-8 py-4" routerLink="/productos">
  {{ 'home.browseCatalog' | translate }}
</a>
```
**After:**
```html
<a pButton severity="help" class="text-lg px-8 py-4" routerLink="/productos">
  {{ 'home.browseCatalog' | translate }}
</a>
```

**Before — mat-stroked-button (retry):**
```html
<button mat-stroked-button color="primary" class="mt-4" (click)="retry()">
  {{ 'catalog.retry' | translate }}
</button>
```
**After:**
```html
<button pButton [outlined]="true" severity="primary" class="mt-4" (click)="retry()">
  {{ 'catalog.retry' | translate }}
</button>
```

**Before — mat-stroked-button (view all):**
```html
<a mat-stroked-button color="primary" routerLink="/productos" class="text-lg px-8">
  {{ 'home.viewAll' | translate }}
</a>
```
**After:**
```html
<a pButton [outlined]="true" severity="primary" routerLink="/productos" class="text-lg px-8">
  {{ 'home.viewAll' | translate }}
</a>
```

**Before — mat-spinner:**
```html
<mat-spinner diameter="48"></mat-spinner>
```
**After:**
```html
<p-progressSpinner [style]="{ width: '48px', height: '48px' }" strokeWidth="4"></p-progressSpinner>
```

### ProductCard SCSS (`product-card.scss`)

**Before:**
```scss
.product-card {
  transition: box-shadow 0.2s ease;
  img[mat-card-image] {
    aspect-ratio: 3 / 4;
  }
}
```
**After:**
```scss
.product-card {
  transition: box-shadow 0.2s ease;
  .p-card-header img {
    aspect-ratio: 3 / 4;
  }
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Compile | `ng build` succeeds | Run build, verify no template/material errors |
| Visual | Homepage renders all sections | Manual: hero, categories, spinner, error+retry, grid, "view all" |
| Visual | ProductCard renders in 4 contexts | Manual: homepage, catalog, wishlist, product-detail |
| Visual | Dark mode | Toggle dark mode, verify PrimeNG component colors |
| Regression | Other pages unaffected | Spot-check catalog, wishlist, product-detail — no Material console warnings unrelated to migrated elements |

## Open Questions

None — all decisions are resolved.
