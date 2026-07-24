# Change: retro-admin-crud-extensions (Archived 2026-07-25)

## Intent

Extend the admin panel with full user edit (PUT endpoint + modal) and category CRUD (create/edit/delete with translations).

## Scope

- **admin-dashboard**: PUT /admin/users/:id (name, email, role, is_verified, marketing_consent), DELETE /admin/users/:id with cascade, GET /admin/categories/:id with translations, category CRUD UI
- **Backend**: AdminUserService.update_user(), AdminUserService.delete_user(), slug-based product endpoints

## Implementation

Implemented directly without formal SDD phases. Documentation retroactive.

## Commits

- `feat(products): add slug-based update and delete endpoints` (da107a42)
- `feat(admin): add user edit endpoint and modal UI` (325ba2d3)
- `feat(admin): add category CRUD with create/edit/delete UI` (4109bf76)

## Specs Synced

| Domain | Action |
|--------|--------|
| admin-dashboard | Added R10 (user edit), R11 (category CRUD), R12 (user deletion cascade) |
