# Design: Sale Pricing Integration

## Technical Approach

Backend resolves best active promotion per product via a single batched DB query, computes `sale_price = price × (1 - discount%/100)` rounded to 2 decimals, and attaches nullable sale fields to ProductResponse and CartResponse. Frontend conditionally renders strike-through pricing, SALE badges, and savings only when `sale_price` is present.

## Architecture Decisions

| Decision | Option | Tradeoff | Choice |
|----------|--------|----------|--------|
| Where to resolve promotions | Controller-level | Keeps ProductService focused on catalog queries | **Controller-level** for products |
| Cart promo resolution | Inside CartService | CartService already owns item-response logic; batching across items natural | **Inside CartService** via injected PromotionService |
| `_build_product_response` signature | Add optional `promotion` param | Minimal diff; backward-compatible (default None) | **Optional promotion param** |
| `_build_cart_item_response` | Make instance method | Needs access to `self.promotion_service` | **Instance method** |
| Best promo tie-breaking | product-scoped > store-wide; then end_date | Spec requirement; prevents non-deterministic picks | **As specified** |

## Data Flow

```
ProductController.list_products()
  → ProductService.list_products() → [Product]
  → PromotionService.get_active_promotions_for_products(product_ids) → {UUID: Promotion}
  → _build_product_response(product, promotion) → dict with sale_price, discount_label, promotion

CartService.get_cart()
  → _load_cart_items() → [CartItem] + Product
  → PromotionService.get_active_promotions_for_products(product_ids) → {UUID: Promotion}
  → _build_cart_item_response(item, promotions) → CartItemResponse with savings
```

## Files Changed

| File | Action |
|------|--------|
| `backend/app/schemas/product.py` | Add `PromotionSummary`, `sale_price`/`discount_label`/`promotion` to `ProductResponse` |
| `backend/app/schemas/cart.py` | Add discount fields to `CartItemResponse` and `CartResponse` |
| `backend/app/services/promotion_service.py` | Add `get_active_promotions_for_products()` |
| `backend/app/controllers/products.py` | Wire promotion resolution into list/detail endpoints |
| `backend/app/services/cart_service.py` | Inject PromotionService, compute per-item savings |
| `frontend/.../models/product.model.ts` | Add sale-pricing optional fields |
| `frontend/.../models/cart.model.ts` | Add discount optional fields |
| `frontend/.../product-card.*` | SALE badge + strike-through pricing |
| `frontend/.../product-detail.*` | SALE badge + savings % |
| `frontend/.../cart.html` | Discount breakdown in cart summary |
| `frontend/.../i18n/es.json` | Sale pricing keys (Spanish) |
| `frontend/.../i18n/en.json` | Sale pricing keys (English) |
| `frontend/.../i18n/sv.json` | Sale pricing keys (Swedish) |
