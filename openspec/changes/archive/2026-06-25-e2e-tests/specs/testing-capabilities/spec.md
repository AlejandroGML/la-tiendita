# Delta for Testing Capabilities

## ADDED Requirements

### Requirement: Homepage E2E Journey
The system MUST pass automated Playwright tests that verify homepage critical content loads without errors.

#### Scenario: Hero banner visible
- GIVEN an unauthenticated user navigates to `/`
- WHEN the page loads
- THEN the hero banner section MUST be visible
- AND the main heading or hero text MUST be present

#### Scenario: Categories carousel loads
- GIVEN the homepage renders
- WHEN the categories section appears
- THEN at least one category item or carousel track MUST be visible

#### Scenario: Featured products display
- GIVEN seed data exists with at least 3 products
- WHEN the homepage renders
- THEN featured product cards MUST be visible in the featured section

### Requirement: Catalog E2E Journey
The system MUST pass automated tests that verify catalog search, filter, sort, and pagination work end-to-end.

#### Scenario: Search returns results
- GIVEN seed data with matching products
- WHEN user types a search term and submits
- THEN product cards matching the query MUST appear
- OR a no-results message MUST display if no match

#### Scenario: Filters narrow results
- GIVEN the catalog page renders with products
- WHEN user selects a category filter or price range
- THEN visible product cards MUST reflect the active filter

#### Scenario: Sort reorders products
- GIVEN the catalog page renders with multiple products
- WHEN user changes sort order (e.g., price low-to-high)
- THEN product card order MUST change accordingly

#### Scenario: Pagination works
- GIVEN seed data exceeds one page of results
- WHEN user clicks next page or page number
- THEN the next set of products MUST load

### Requirement: Product Detail E2E Journey
The system MUST pass automated tests that verify product detail page content renders fully.

#### Scenario: Product images load
- GIVEN a product exists in the catalog
- WHEN user navigates to `/productos/{slug}`
- THEN the main product image MUST be visible

#### Scenario: Reviews section loads
- GIVEN a product has at least one review
- WHEN user navigates to the product detail page
- THEN the reviews section MUST be visible with review content

#### Scenario: Related products display
- GIVEN the catalog has related products for the current item
- WHEN user views the product detail page
- THEN a related-products section MUST render with at least one card

### Requirement: Auth E2E Journey
The system MUST pass automated tests that verify forgot-password and registration-success flows work end-to-end.

#### Scenario: Forgot-password flow submits
- GIVEN a registered user email
- WHEN user navigates to forgot-password page and submits the email
- THEN a success confirmation MUST appear or redirect to a confirmation page

#### Scenario: Registration success page renders
- GIVEN valid registration data
- WHEN user completes the registration form and submits
- THEN user MUST be redirected to a success page or logged-in state

#### Scenario: Auth guard redirects on protected route
- GIVEN an unauthenticated user
- WHEN user navigates to `/carrito`, `/admin`, or `/checkout`
- THEN user MUST be redirected to `/login`

### Requirement: Cart E2E Journey
The system MUST pass automated tests that verify cart item manipulation works end-to-end.

#### Scenario: Add item to cart
- GIVEN an authenticated user on a product detail page
- WHEN user clicks "Add to Cart"
- THEN a snackbar or toast MUST confirm the action

#### Scenario: Update item quantity
- GIVEN an item exists in the cart
- WHEN user changes the quantity via the quantity control
- THEN the cart total MUST update accordingly

#### Scenario: Remove item from cart
- GIVEN an item exists in the cart
- WHEN user clicks the remove/delete action on that item
- THEN the item MUST disappear from the cart table

#### Scenario: Empty cart state
- GIVEN an authenticated user with an empty cart
- WHEN user navigates to `/carrito`
- THEN the empty cart state MUST render with a "continue shopping" link

### Requirement: Checkout E2E Journey
The system MUST pass automated tests that verify the full checkout flow works end-to-end.

#### Scenario: Checkout form validates required fields
- GIVEN an authenticated user on the checkout page with items in cart
- WHEN the form is submitted with empty fields
- THEN validation errors MUST appear on required fields

#### Scenario: Successful order confirmation
- GIVEN an authenticated user with items in cart and valid shipping data
- WHEN user fills the checkout form and confirms the order
- THEN user MUST be redirected to an order confirmation page
- AND the confirmation page MUST display the order ID

### Requirement: Admin E2E Journey
The system MUST pass automated tests that verify admin product creation and order management lifecycle.

#### Scenario: Admin creates a product
- GIVEN an admin-authenticated session
- WHEN admin navigates to `/admin/productos/nuevo` and fills the form
- THEN the new product MUST appear in the admin products table

#### Scenario: Admin manages order status
- GIVEN at least one order exists in the system
- WHEN admin navigates to `/admin/ordenes` and changes an order status
- THEN the status MUST update and reflect in the orders list
