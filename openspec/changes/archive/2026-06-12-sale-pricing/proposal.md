# Proposal: Sale Pricing Integration

## Intent

Promotions exist as admin-managed discount codes but are never surface to shoppers. Products show base price only — no sale prices, badges, or savings indicators. This change bridges promotion logic into the product catalog, cart, and UI so customers SEE and FEEL discounts.

## Scope

### In Scope
- Compute `sale_price` from best active promotion per product in backend responses
- Show strike-through base price + sale price on product card and detail page
- Display "SALE" badge and "You save X%" on product detail
- Cart: per-item discount info, original vs discounted subtotal
- i18n keys for all new UI (es/en/sv)

### Out of Scope
- Coupon code entry at checkout (promotion code is admin-set, not user-entered)
- Promotion auto-apply via cart validation (next change)
- Stacking multiple promotions (best discount wins only)
- Fixed-amount discounts (percentage-only for now)
- Admin: no changes to promotion CRUD

## Capabilities

### New Capabilities
- `sale-pricing`: compute sale price from best active promotion (percentage discount), resolve product-scoped vs store-wide promos, expose via product/cart API responses

### Modified Capabilities
- `product-catalog`: `ProductResponse` gains `sale_price` (nullable Decimal), `discount_label` (nullable str), `promotion` (nullable summary). `list_products` and `get_product_by_slug` include these.
- `cart`: `CartItemResponse` gains `sale_price`, `discount_percent`; `CartResponse` gains `savings` (subtotal before vs after discount)
- `promotions`: adds "best active promotion per product" resolution — highest discount_percent from active, date-range-valid, uses-remaining promotions; respects product_id scope (null = store-wide)

## Approach

**Backend — ProductService**: `list_products()` and `get_product_by_slug()` issue a single batched query for active promotions (product_id matches product OR product_id IS NULL). Best promo = max discount_percent. Compute `sale_price = price × (1 - discount_percent/100)` rounded to 2 decimal places. Attach to `_build_product_response`.

**Backend — CartService**: `_build_cart_item_response()` retrieves best active promo for the line item's product. Exposes `sale_price` and `savings` per line + cart total.

**Frontend**: `product-card.html` shows strike-through price + sale price in red. `product-detail.html` adds "SALE" badge + "You save X%". `cart.html` shows original/subtotal + discount + new total. Five new i18n keys: `product.sale`, `product.youSave`, `cart.originalTotal`, `cart.discount`, `cart.youSave`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/product.py` | Modified | Add `sale_price`, `discount_label`, `promotion` to `ProductResponse` |
| `backend/app/schemas/cart.py` | Modified | Add `sale_price`, `discount_percent` to `CartItemResponse`; `savings` to `CartResponse` |
| `backend/app/services/product_service.py` | Modified | New `_resolve_best_promotion()`; batched promo query in list/detail |
| `backend/app/controllers/products.py` | Modified | `_build_product_response` attaches promotion data |
| `backend/app/services/cart_service.py` | Modified | `_build_cart_item_response` computes per-item discount |
| `frontend/src/app/shared/models/product.model.ts` | Modified | Add `sale_price`, `discount_label`, `promotion` |
| `frontend/src/app/shared/models/cart.model.ts` | Modified | Add `sale_price`, `discount_percent`, `savings` |
| `frontend/src/app/shared/components/product-card/` | Modified | Sale price + badge in template |
| `frontend/src/app/features/product-detail/` | Modified | Discount indicator in template |
| `frontend/src/app/features/cart/` | Modified | Discount breakdown in template |
| `frontend/src/assets/i18n/{es,en,sv}.json` | Modified | 5 new sale-related keys |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| N+1 promo queries per product in listing | Med | Single batched query per page load; results cached in dict |
| Expired-end-date race condition (promo active at query, expired by add-to-cart) | Low | Cart sends product_id; server re-resolves at checkout (future), for now the listing is best-effort |
| Confusion when no promo applies (sale_price=null) | Low | Frontend conditionally renders discount UI only when `sale_price` is present |

## Rollback Plan

Remove `sale_price`/`promotion` fields from `_build_product_response` and `_build_cart_item_response`. Revert frontend templates to base-price-only. No DB migration needed — promo model unchanged.

## Dependencies

- Product variants (implemented, fully supported)
- Promotion model + CRUD (implemented)
- i18n framework ngx-translate (implemented)

## Success Criteria

- [ ] Product listing returns `sale_price` when an active promotion applies
- [ ] Product card renders strike-through + sale price + badge
- [ ] Product detail shows "You save X%" when discounted
- [ ] Cart shows per-item discount and savings total
- [ ] i18n keys resolve correctly in es/en/sv
- [ ] Zero behavioral change for products without active promotions
