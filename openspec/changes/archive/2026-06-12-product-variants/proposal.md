# Proposal: Product Variants

## Intent

Products currently have a single `size` (nullable) and single `stock` column. Colors are a JSONB array with no stock association. Multi-size items (XS-XL) require duplicate product rows with different slugs. Customers cannot select size/color on product detail or in cart. Checkout validates only product-level stock, not variant-level. This change introduces a `ProductVariant` model (size + color + stock + SKU) so each product can have multiple sellable units.

## Scope

### In Scope
- `ProductVariant` model (FK→products, size, color, color_hex, stock, sku, timestamps)
- DB migration: remove `size`/`stock` from products, create default variants from existing data
- Product detail: interactive size selector (buttons), color selector (swatches), dynamic stock per variant
- Cart: `variant_id` FK (nullable), `size`/`color` fields; add-to-cart by variant
- Checkout: per-variant stock validation; variant info in product_snapshot
- Admin product form: variant CRUD (add/remove size+color combos with stock)
- Product listing: show available sizes/colors count per product
- `ProductSize` enum reused (XS, S, M, L, XL, XXL)
- Backward compatibility: nullable `variant_id` on cart items; old carts keep working
- SKU auto-generation: `{slug-brief}-{size}-{color-abbr}-{seq}`

### Out of Scope
- Variant-specific pricing (all variants share product price)
- Variant-specific images
- Inventory management beyond stock count
- Bulk variant import/export
- Variant filtering on product listing (future)

## Capabilities

### New Capabilities
- `product-variants`: ProductVariant model, variant CRUD, variant-aware stock management, size/color selection UI

### Modified Capabilities
- `product-catalog`: product detail and listing must expose variants; `GET /api/products/{slug}` includes variants array
- `product-management`: admin create/update must support variant management; `size`/`stock` removed from Product model
- `cart`: `AddToCartRequest` adds optional `variant_id`, `size`, `color`; `CartItemResponse` includes them; unique constraint on `(user_id, variant_id)` or `(user_id, product_id, size, color)`
- `checkout`: stock validation per-variant via `UPDATE product_variants WHERE stock >= qty`; `product_snapshot` includes `variant_id`, `size`, `color`

## Approach

**Database**: New `product_variants` table with FK cascade on product soft-delete. Alembic migration: (1) create table, (2) insert default variant per product from existing `size`/`stock`, (3) drop `size`/`stock` from products. Unique index on `sku`.

**Backend**: ProductVariant ORM model + Pydantic schemas. ProductService eager-loads variants via `selectinload`. CartService accepts `variant_id` in add-to-cart; unique constraint resolves on `(user_id, product_id, variant_id)` — if `variant_id` is NULL, falls back to `(user_id, product_id)`. OrderService validates per-variant stock with atomic `UPDATE ... WHERE stock >= qty`. Admin product controller handles variant CRUD within product lifecycle.

**Frontend**: Product detail gets `variants` array from API. Size buttons filter available colors; color swatches filter stock for selected combo. Cart shows size/color per item. Admin form has dynamic variant rows with add/remove.

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/product.py` | Modified | Remove `size`, `stock`; add `variants` relationship |
| `backend/app/models/variant.py` | New | ProductVariant model |
| `backend/app/models/cart.py` | Modified | Add `variant_id`, `size`, `color`; change unique constraint |
| `backend/app/models/order.py` | Modified | product_snapshot schema updated |
| `backend/app/services/product_service.py` | Modified | Eager-load variants; variant-aware queries |
| `backend/app/services/cart_service.py` | Modified | Add by variant_id; return size/color in response |
| `backend/app/services/order_service.py` | Modified | Per-variant stock check; variant in snapshot |
| `backend/app/schemas/product.py` | Modified | Variant schemas added; size/stock removed from Product |
| `backend/app/schemas/cart.py` | Modified | `variant_id`, `size`, `color` fields |
| `backend/app/schemas/order.py` | Modified | Variant info in product_snapshot dict |
| `backend/app/controllers/products.py` | Modified | Variants in product detail response |
| `backend/app/controllers/admin.py` | Modified | Variant CRUD in admin product endpoints |
| `backend/app/controllers/cart.py` | Modified | Accept variant_id in add-to-cart |
| `backend/alembic/versions/` | New | Migration for product_variants + data migration |
| `frontend/src/app/shared/models/product.model.ts` | Modified | Add `ProductVariant` interface |
| `frontend/src/app/features/product-detail/` | Modified | Size selector, color swatches, variant stock |
| `frontend/src/app/shared/models/cart.model.ts` | Modified | `variant_id`, `size`, `color` |
| `frontend/src/app/features/cart/` | Modified | Display size/color per item |
| `frontend/src/app/features/admin/product-form/` | Modified | Dynamic variant rows |
| `frontend/src/app/shared/components/product-card/` | Modified | Show available sizes/colors |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modified | New translation keys for variant UI |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Data migration corrupts existing products | Low | Migration inserts one default variant per product; reversible |
| Cart unique constraint breakage | Med | Keep `(user_id, product_id)` as fallback when `variant_id` is NULL; add separate constraint for variant-based entries |
| Frontend checkout breaks without size selected | Med | Disable add-to-cart until size selected; validate on checkout endpoint |
| SKU collision | Low | Database `UNIQUE` constraint; migration skips duplicates and appends suffix |

## Rollback Plan

1. Revert Alembic migration (create reverse migration restoring `size`/`stock` from default variants)
2. Deploy prior backend version (no variant endpoints)
3. Frontend falls back to legacy product detail (no variant selectors) — cart items with `variant_id` NULL are still valid

## Dependencies

- Existing `ProductSize` enum (reuse)
- Existing soft-delete on products (cascade to variants)
- Admin guard on `/api/admin/*`

## Success Criteria

- [ ] Product detail shows size buttons and color swatches; selecting a combo shows variant stock
- [ ] Cart items display selected size and color
- [ ] Checkout validates per-variant stock atomically; rejects if variant stock insufficient
- [ ] Admin form allows adding/removing variants with stock per combo
- [ ] Existing products work after migration (one default variant auto-created)
- [ ] Cart items without `variant_id` continue to work (backward compat)
- [ ] SKU uniqueness enforced at DB level
