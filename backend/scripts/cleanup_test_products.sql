-- Cleanup test products from test_seed_integrity.py
-- Run this if test products are visible in production views.
-- These products were inserted by integration tests that previously
-- lacked teardown. The per-test cleanup was added in fix-visual-audit-bugs
-- Phase 5.3, but existing leftover data needs a one-time purge.

BEGIN;

DELETE FROM product_translations
WHERE product_id IN (
    SELECT id FROM products
    WHERE slug ~ '^(boundary-|empty-cond-|partial-cond-|positive-|material-|swedish-|multi-lang-|batch-)'
);

DELETE FROM products
WHERE slug ~ '^(boundary-|empty-cond-|partial-cond-|positive-|material-|swedish-|multi-lang-|batch-)';

COMMIT;

-- Verify: SELECT count(*) FROM products WHERE slug ~ '^(boundary-|empty-cond-|partial-cond-|positive-|material-|swedish-|multi-lang-|batch-)';
-- Should return 0 after running.
