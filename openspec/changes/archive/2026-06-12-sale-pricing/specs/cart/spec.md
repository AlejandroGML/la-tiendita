# cart (MODIFIED)

## Requirement: Get Cart with Subtotals

### Modified: Added discount-aware pricing

#### Scenario: Cart with per-item discounts (UPDATED)
- GIVEN cart has item A (qty 2, price 50, 20% promo → sale_price=40) and item B (qty 1, price 30, no promo)
- WHEN GET `/api/cart`
- THEN items array: item A subtotal=80 (discounted), `sale_price=40`, `discount_percent=20`; item B subtotal=30; `cart_total`=110; `savings`=20

#### Scenario: Empty cart returns zero savings (NEW)
- GIVEN empty cart
- WHEN GET `/api/cart`
- THEN `savings=0`
