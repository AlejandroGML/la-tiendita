/**
 * Reusable DOM selectors for the Tiendita app (PrimeNG).
 *
 * Prefers accessible roles first, then CSS classes, then Angular component
 * element selectors as last resort.
 * WARNING: The app currently has ZERO `data-testid` attributes in the main
 * UI (home, catalog, cart, etc.). Admin product-form has some (btn-save,
 * btn-cancel). Any test relying on data-testid will fail.
 */

// ---- Layout ----
export const header = 'app-header';
export const headerBrand = 'app-header a[href="/"]';
export const navProducts = 'app-header a[href="/productos"]';
export const navCart = 'app-header a[href="/carrito"]';
export const navAdmin = 'a[href="/admin"]';
export const menuButton = 'app-header button:has([class*="menu"])';

// ---- Product Cards (catalog + homepage) ----
export const productCard = 'a.block[href*="/productos/"]';
export const productCardName = 'a.block[href*="/productos/"] h3';
export const productCardPrice = 'a.block[href*="/productos/"] p:first-of-type';
export const productCardImage = 'a.block[href*="/productos/"] img';

// ---- Product List (Catalog) ----
export const catalogTitle = 'h1';
export const filtersSidebar = 'aside.filters-sidebar';
export const categoryFilter = 'aside.filters-sidebar [role="combobox"]';
export const searchInput = '[role="combobox"][aria-label*="search" i], [role="combobox"][aria-label*="buscar" i]';
export const paginationContainer = '[role="navigation"] button';

// ---- Product Detail ----
export const productTitle = 'h1[data-testid="product-title"], .product-info h1';
export const productPrice = '.text-2xl.font-bold';
export const addToCartButton = 'button:has-text("Agregar"), button:has-text("Add to"), button[aria-label*="cart" i]';
export const productImage = 'img[alt*="product" i], .main-image img';

// ---- Cart ----
export const cartPage = '[data-testid="cart-page"]';
export const cartEmpty = '[data-testid="cart-empty"]';
export const cartTable = '[data-testid="cart-table"]';
export const cartCheckoutButton = '[data-testid="checkout-button"]';
export const cartItemRows = '[data-testid="cart-table"] tr';

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
export const loginError = '.text-red-600, .text-red-500, [class*="error"]';
export const registerLink = 'a[href="/register"]';
export const loginLink = 'a[href="/login"]';

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

// ---- Snackbar / Toasts (PrimeNG Toast) ----
export const snackbar = 'p-toast, [role="alertdialog"]';
export const snackbarText = '[role="alertdialog"] .p-toast-message-text, [role="alertdialog"]';

// ---- Spinner / Loading (PrimeNG) ----
export const spinner = 'p-progressspinner, p-progressbar, [role="progressbar"]';
export const progressBar = 'p-progressbar';

// ---- Homepage ----
export const heroBanner = '[class*="hero"]';
export const categoriesSection = '[class*="categories"]';
export const featuredSection = '[class*="featured"]';

// ---- Catalog ----
export const sortDropdown = '[role="combobox"][aria-label*="sort" i], [role="combobox"][aria-label*="order" i]';
export const searchBar = '[role="combobox"][aria-label*="search" i], [role="combobox"][aria-label*="buscar" i]';

// ---- Product Detail ----
export const reviewSection = '#reviews, [data-testid="reviews-section"]';
export const relatedProducts = '[data-testid="related-products"]';

// ---- Auth ----
export const forgotPasswordLink = 'a[href*="recuperar"], a[href*="forgot"], a:has-text("Olvidé"), a:has-text("Forgot")';
export const forgotPasswordForm = '[data-testid="forgot-password-form"], form:has(input[formControlName="email"]):has(button:has-text("Recuperar"))';

// ---- Cart ----
export const qtyInput = 'input[type="number"], [data-testid="qty-input"]';
export const removeItemButton = 'button:has-text("Quitar"), button:has-text("Remove"), [data-testid="btn-remove"]';

// ---- Checkout ----
export const orderConfirmation = '[data-testid="checkout-success-guest"]';
export const checkoutSuccessPage = '[data-testid="checkout-success-guest"]';
export const checkoutSuccessOrderId = '[data-testid="checkout-success-order-id"]';

// ---- Admin ----
export const adminProductForm = '[data-testid="product-form"]';
export const adminOrderStatusSelect = '[data-testid^="status-select-"]';
export const adminOrdersTable = '[data-testid="orders-table"]';
export const adminOrdersLoading = '[data-testid="orders-loading"]';
export const adminNoOrders = '[data-testid="no-orders"]';
export const adminSaveButton = '[data-testid="btn-save"]';
export const adminInputPrice = '[data-testid="input-price"]';
export const adminSelectCategory = '[data-testid="select-category"]';
export const adminInputBrand = '[data-testid="input-brand"]';

// ---- Language ----
export const languageSelect = 'button:has-text("ES"), button:has-text("EN"), button:has-text("SV")';
