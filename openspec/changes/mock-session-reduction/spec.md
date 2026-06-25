# Spec: mock-session-reduction

## Requirements

### R1 — Promotions integration tests
- PromotionService.list_active returns only currently-active promotions
- PromotionService.create persists a new promotion with translations
- PromotionService.delete removes a promotion
- Expired promotions (end_date < now) excluded from list_active
- Exhausted promotions (current_uses >= max_uses) excluded from list_active
- PromotionRepository.get_best_for_product returns product-scoped promotion

### R2 — Product variants integration tests
- VariantService.list_variants returns non-deleted variants by product
- VariantService.create_variant persists a new variant with auto-generated SKU
- VariantService.update_variant modifies stock in-place
- VariantService.delete_variant soft-deletes (sets deleted_at)
- Soft-deleted variants excluded from list_variants

### R3 — Admin integration tests
- AdminOrderService.update_order_status enforces state machine transitions
- AdminUserService.update_user_role persists role change (non-self)
- DashboardService.get_dashboard_stats returns non-zero with seeded data
- ProductRepository persists a product correctly
- Self-demotion is rejected

### R4 — Conftest documentation
- `mock_session()` fixture docstring informs developers to prefer real session for integration tests
