/**
 * Reusable DOM selectors for the Tiendita app.
 *
 * Prefer `data-testid` first, then accessible roles, then classes as last resort.
 * All selectors return Playwright-compatible strings.
 */

// ---- Layout ----
export const header = 'mat-toolbar';
export const headerBrand = 'mat-toolbar a[routerLink="/"]';
export const navProducts = 'a[routerLink="/productos"]';
export const navCart = 'a[routerLink="/carrito"]';
export const navAdmin = 'a[routerLink="/admin"]';
export const menuButton = 'button[aria-label="Open navigation menu"]';

// ---- Product Cards ----
export const productCard = '.product-card';
export const productCardName = '.product-card h3';
export const productCardPrice = '.product-card .text-lg';
export const productCardImage = '.product-card img';

// ---- Product List (Catalog) ----
export const catalogTitle = 'h1';
export const filtersSidebar = '.filters-sidebar';
export const categoryFilter = '.filters-sidebar mat-select';
export const searchInput = 'app-search-bar input';
export const paginationContainer = 'app-pagination';

// ---- Product Detail ----
export const productTitle = '.product-info h1';
export const productPrice = '.product-info .text-2xl.font-bold';
export const addToCartButton = 'button:has-text("Agregar al carrito"), button:has-text("Add to Cart")';
export const productImage = '.main-image img';

// ---- Cart ----
export const cartPage = '[data-testid="cart-page"]';
export const cartEmpty = '[data-testid="cart-empty"]';
export const cartTable = '[data-testid="cart-table"]';
export const cartCheckoutButton = '[data-testid="checkout-button"]';
export const cartItemRows = '[data-testid="cart-table"] tr.mat-mdc-row';

// ---- Checkout ----
export const checkoutPage = '[data-testid="checkout-page"]';
export const checkoutForm = '[data-testid="shipping-form"]';
export const confirmOrderButton = '[data-testid="confirm-button"]';
export const inputName = '[data-testid="input-name"]';
export const inputAddress = '[data-testid="input-address"]';
export const inputCity = '[data-testid="input-city"]';
export const inputPhone = '[data-testid="input-phone"]';

// ---- Auth ----
export const loginForm = 'form';
export const loginEmailInput = 'input[type="email"]';
export const loginPasswordInput = 'input[type="password"]';
export const loginSubmitButton = 'button[type="submit"]';
export const loginError = '.text-red-600';
export const registerLink = 'a[routerLink="/register"]';
export const loginLink = 'a[routerLink="/login"]';

// ---- Admin ----
export const adminDashboard = '[data-testid="dashboard-stats"]';
export const adminDashboardLoading = '[data-testid="dashboard-loading"]';
export const adminDashboardError = '[data-testid="dashboard-error"]';
export const adminDashboardRetry = '[data-testid="dashboard-retry"]';
export const adminProductsTable = '[data-testid="products-table"]';
export const adminNoProducts = '[data-testid="no-products"]';
export const adminProductsError = '[data-testid="products-error"]';
export const adminNewProductButton = '[data-testid="btn-new-product"]';

// ---- Orders ----
export const orderListPage = '[data-testid="order-list-page"]';
export const orderListEmpty = '[data-testid="order-list-empty"]';

// ---- Wishlist ----
export const wishlistEmpty = '[data-testid="wishlist-empty"]';
export const wishlistError = '[data-testid="wishlist-error"]';
export const wishlistBrowseButton = '[data-testid="btn-browse"]';

// ---- Snackbar / Toasts ----
export const snackbar = '.mat-mdc-snack-bar-container, snack-bar-container';
export const snackbarText = '.mat-mdc-snack-bar-container .mat-mdc-snack-bar-label';

// ---- Spinner / Loading ----
export const spinner = 'mat-spinner, .mat-mdc-progress-spinner';
export const progressBar = 'mat-progress-bar';

// ---- Language ----
export const languageSelect = '[aria-label*="language" i], [aria-label*="idioma" i], select[aria-label]';
