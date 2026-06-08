# Design: PrimeNG Cart & Checkout Migration

## Technical Approach

Replace Material components on cart/checkout pages with PrimeNG equivalents following the same pattern as Phases 1–3: swap templates, keep `.ts` logic unchanged, add module imports. 7 files modified, 0 created, 0 deleted.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Table columns | `ng-template pTemplate="header"/"body"` with `[value]` | PrimeNG declarative API; `displayedColumns` stays in TS but unused by template |
| Quantity buttons | `p-button icon="pi pi-plus/minus/trash" [text]="true"` | Outlined icon-only style matches current mat-icon-button look |
| Form fields | `p-floatLabel variant="on"` + `input pInputText formControlName="..."` | No wrapper directive needed; `formControlName` binds directly to `<input>` |
| Validation display | `*ngIf`-driven `<small class="p-error">` per field | PrimeNG has no `mat-error` equivalent; `p-error` is a CSS class, not a directive |
| Toast vs SnackBar | `MessageService.add()` + `<p-toast>` in template | Preserves `onAction()` navigation behavior; ToastModule imported in CheckoutModule, MessageService in providers |
| ToastModule location | Direct import in `CheckoutModule`, NOT SharedModule | `MessageService` is scoped to its importing module per PrimeNG docs; avoids circular dependencies |
| Submit spinner | `p-button [loading]="submitting()"` | Replaces nested `<mat-spinner>` inside `<button>`; PrimeNG handles the spinner overlay natively |

## HTML Transformations

### Cart: mat-table → p-table

**Before:**
```html
<table mat-table [dataSource]="items()" class="w-full">
  <ng-container matColumnDef="product">
    <th mat-header-cell *matHeaderCellDef>Product</th>
    <td mat-cell *matCellDef="let item">{{ item.product_name }}</td>
  </ng-container>
  <!-- ... more columns ... -->
  <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
  <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
</table>
```

**After:**
```html
<p-table [value]="items()" styleClass="w-full">
  <ng-template pTemplate="header">
    <tr><th>Product</th><th>Qty</th><th>Price</th><th>Subtotal</th><th></th></tr>
  </ng-template>
  <ng-template pTemplate="body" let-item>
    <tr>
      <td>{{ item.product_name }}</td>
      <td>...</td>
      <td>{{ item.unit_price | currency }}</td>
      <td>{{ item.subtotal | currency }}</td>
      <td>...</td>
    </tr>
  </ng-template>
</p-table>
```

### Cart: mat-icon-button → p-button icon

**Before:**
```html
<button mat-icon-button color="primary" (click)="increaseQuantity(item)" [attr.aria-label]="'cart.increase' | translate">
  <mat-icon>add</mat-icon>
</button>
<button mat-icon-button color="warn" (click)="removeItem(item)" [attr.aria-label]="'cart.remove' | translate">
  <mat-icon>delete</mat-icon>
</button>
```

**After:**
```html
<p-button icon="pi pi-plus" [text]="true" severity="primary" (onClick)="increaseQuantity(item)" [disabled]="loading()" [ariaLabel]="'cart.increase' | translate" />
<p-button icon="pi pi-trash" [text]="true" severity="danger" (onClick)="removeItem(item)" [disabled]="loading()" [ariaLabel]="'cart.remove' | translate" />
```

### Cart: mat-flat-button → p-button

**Before:**
```html
<button mat-flat-button color="primary" (click)="checkout()" data-testid="checkout-button">Checkout</button>
```

**After:**
```html
<p-button label="Checkout" severity="primary" (onClick)="checkout()" [disabled]="loading() || items().length === 0" styleClass="px-8 py-3 text-lg" data-testid="checkout-button" />
```

### Cart: mat-spinner → p-progressSpinner

**Before:**
```html
<mat-spinner diameter="48"></mat-spinner>
```

**After:**
```html
<p-progressSpinner [style]="{ width: '48px', height: '48px' }" strokeWidth="4" />
```

### Checkout: mat-form-field → p-floatLabel

**Before:**
```html
<mat-form-field appearance="outline" class="w-full mb-4">
  <mat-label>Name</mat-label>
  <input matInput formControlName="name" data-testid="input-name" />
  <mat-error *ngIf="shippingForm.get('name')?.invalid">Required</mat-error>
</mat-form-field>
```

**After:**
```html
<p-floatLabel variant="on" class="w-full mb-4">
  <input pInputText formControlName="name" data-testid="input-name" class="w-full" />
  <label>Name</label>
</p-floatLabel>
<small *ngIf="shippingForm.get('name')?.invalid && shippingForm.get('name')?.touched" class="p-error block mt-1">Required</small>
```

### Checkout: MatSnackBar → MessageService

**Before (`checkout.ts`):**
```typescript
import { MatSnackBar } from '@angular/material/snack-bar';
constructor(private readonly snackBar: MatSnackBar) {}
// ...
this.snackBar.open('checkout.orderPlaced', 'checkout.viewOrder', { duration: 8000 })
  .onAction().subscribe(() => this.router.navigate(['/perfil/ordenes']));
```

**After (`checkout.ts`):**
```typescript
import { MessageService } from 'primeng/api';
constructor(private readonly messageService: MessageService) {}
// ...
this.messageService.add({
  severity: 'success',
  summary: this.translate.instant('checkout.orderPlaced'),
  detail: this.translate.instant('checkout.viewOrder'),
  life: 8000,
});
```

**After (`checkout.html`):**
```html
<p-toast position="bottom-right"></p-toast>  <!-- add at top of template -->
```

### Checkout: mat-flat-button + inner spinner → p-button [loading]

**Before:**
```html
<button mat-flat-button color="primary" [disabled]="submitting() || shippingForm.invalid" (click)="submitOrder()">
  <mat-spinner *ngIf="submitting()" diameter="20"></mat-spinner>
  Confirm
</button>
```

**After:**
```html
<p-button label="Confirm" severity="primary" [loading]="submitting()" [disabled]="shippingForm.invalid || items.length === 0" (onClick)="submitOrder()" styleClass="w-full py-3 text-lg" data-testid="confirm-button" />
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `shared/primeng-module.ts` | Modify | Add `TableModule`, `FloatLabelModule`, `ToastModule` imports + exports |
| `features/cart/cart.html` | Modify | mat-table→p-table, mat-icon-button→p-button, mat-flat-button→p-button, mat-spinner→p-progressSpinner, mat-icon→pi classes |
| `features/cart/cart.spec.ts` | Modify | Replace MatTableModule/MatButtonModule/MatIconModule/MatProgressSpinnerModule with PrimeNgModule; update `.mat-mdc-row`→`[data-testid]` selectors |
| `features/checkout/checkout.html` | Modify | mat-form-field→p-floatLabel, matInput→pInputText, mat-error→p-error, mat-flat-button→p-button, mat-spinner→p-progressSpinner, add `<p-toast>` |
| `features/checkout/checkout.ts` | Modify | Import `MessageService` from `primeng/api`; replace `MatSnackBar` DI; optional `TranslateService` DI for toast labels |
| `features/checkout/checkout.spec.ts` | Modify | Replace MatFormFieldModule/MatInputModule/MatSnackBarModule/MatButtonModule/MatProgressSpinnerModule with PrimeNgModule; add `MessageService` provider |
| `features/checkout/checkout-module.ts` | Modify | Add `MessageService` to providers; PrimeNgModule already imported via SharedModule |

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit (Cart) | Table renders rows, quantity buttons dispatch, delete calls removeItem | Query by `[data-testid]` + `[aria-label]` selectors instead of `.mat-mdc-row` |
| Unit (Checkout) | Form fields render, validation errors show on touch, confirm button disabled when invalid, toast on success, error on 409 | Spy on `messageService.add`; query inputs by `[data-testid]`; PrimeNgModule + MessageService in TestBed |
| E2E | None | Journey spec `cart-checkout.spec.ts` uses `page.locator()` — Material-agnostic, no changes needed |

## Migration

No data migration. Rollback via `git revert`. SharedModule retains all Material modules — no other pages affected.

## Open Questions

None.
