# frontend-core Delta Spec

> Base: `openspec/specs/frontend-core/spec.md`
> Change: `polish-deploy`

## ADDED Requirements

### Requirement: Dark Mode Theme Toggle (NEW)

The system MUST provide a `ThemeService` in `core/services/` that toggles between light and dark Angular Material themes. The toggle SHALL add/remove a `dark-theme` CSS class on `<body>`. State SHALL persist to `localStorage`. A theme toggle button (icon: light_mode/dark_mode) SHALL be placed in the `HeaderComponent`.

#### Scenario: Toggle switches to dark theme

- GIVEN current theme is light
- WHEN user clicks the theme toggle button in the header
- THEN `dark-theme` class is added to `<body>`
- AND Angular Material components render with dark colors
- AND `localStorage` stores `theme=dark`

#### Scenario: Dark theme persists across reload

- GIVEN `localStorage` has `theme=dark`
- WHEN the application loads
- THEN `ThemeService` applies the dark theme on init
- AND the theme toggle icon shows `light_mode` (switch to light)

#### Scenario: System preference default

- GIVEN no `theme` in `localStorage`
- WHEN the application loads
- THEN `ThemeService` checks `prefers-color-scheme` media query
- AND sets theme to match system preference

### Requirement: SEO Meta Tags (NEW)

The system MUST use Angular's `Meta` and `Title` services from `@angular/platform-browser` to set SEO tags. `index.html` MUST include default Open Graph and description meta tags. `AppComponent` SHALL update the title dynamically. Feature route components SHALL set page-specific meta descriptions.

#### Scenario: Default meta tags in index.html

- GIVEN the production build is deployed
- WHEN a search engine crawler fetches `http://localhost/`
- THEN `<meta property="og:title" content="La Tiendita">` is present
- AND `<meta name="description" content="...">` is present
- AND `<meta property="og:type" content="website">` is present

#### Scenario: Dynamic title per route

- GIVEN user navigates to `/productos`
- WHEN `ProductListComponent` initializes
- THEN document title updates to "Productos | La Tiendita"

#### Scenario: Product detail has SEO tags

- GIVEN user navigates to `/productos/chaqueta-denim`
- WHEN `ProductDetailComponent` loads product data
- THEN `og:title` is set to product name
- AND `description` meta tag is set to product description

### Requirement: Responsive Layout Coverage (NEW)

The system SHALL ensure all views render correctly at mobile (≤640px), tablet (641–1024px), and desktop (≥1025px) breakpoints. The header navigation SHALL collapse to a hamburger menu on mobile. The product grid SHALL render 1 column at mobile, 2 at tablet, 3–4 at desktop. The cart table SHALL scroll horizontally on small screens.

#### Scenario: Mobile hamburger menu

- GIVEN viewport width is 375px
- WHEN the application renders
- THEN the header shows a hamburger icon instead of nav links
- AND clicking the hamburger opens a slide-out or dropdown menu

#### Scenario: Product grid responsive columns

- GIVEN viewport is 375px
- WHEN `/productos` renders
- THEN products display in a single column
- AND at 768px they display in 2 columns
- AND at 1280px they display in 3+ columns

#### Scenario: Cart table horizontal scroll

- GIVEN viewport is 375px
- WHEN `/carrito` renders with products in cart
- THEN the cart table is horizontally scrollable
- AND no content is clipped or overflowing outside the viewport
