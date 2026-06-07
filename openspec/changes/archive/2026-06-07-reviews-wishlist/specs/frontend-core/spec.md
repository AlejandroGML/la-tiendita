# Delta for frontend-core

## MODIFIED Requirements

### Requirement: Application Shell Layout and Routing

The system MUST create `HeaderComponent`, `FooterComponent`, `HomeComponent`. `AppComponent` MUST wrap `<router-outlet>`. Routes MUST include lazy-loaded: home, auth, product, cart (JWT), checkout (JWT), orders (JWT), profile wishlist (`/perfil/wishlist`, JWT), admin promotions (`/admin/promociones`, admin), and wildcard redirect.
(Previously: Did not include /perfil/wishlist or /admin/promociones routes)

#### Scenario: Wishlist route renders and requires auth
- GIVEN authenticated user navigates to `/perfil/wishlist`
- WHEN the router resolves the lazy-loaded WishlistModule
- THEN the wishlist grid page with product cards renders

#### Scenario: Admin promotions route requires admin guard
- GIVEN non-admin user navigates to `/admin/promociones`
- WHEN the router activates the guarded route
- THEN user is redirected to `/`

### Requirement: Angular Material Integration

The system MUST install `@angular/material@22` and configure one prebuilt theme. `SharedModule` SHALL re-export commonly used Material modules including `MatButtonModule`, `MatToolbarModule`, `MatIconModule`, `MatGridListModule`, `MatChipsModule`, `MatSliderModule`, `MatTabsModule`, and `MatIconModule` (for star icons).
(Previously: No explicit star-icon usage. No change to module list — MatIconModule already included.)

## ADDED Requirements

### Requirement: Star-Rating Shared Component

The system SHALL provide a `StarRatingComponent` in `shared/components/star-rating/`. It MUST accept `@Input() rating: number` (1-5) and `@Input() readonly: boolean` (default true). In read-only mode it renders filled/empty stars. In editable mode it emits `@Output() ratingChange = new EventEmitter<number>()` on click.

#### Scenario: Read-only star display
- GIVEN rating=4, readonly=true
- WHEN component renders
- THEN 4 filled stars (★) and 1 empty star (☆) display

#### Scenario: Editable star selection
- GIVEN readonly=false, current rating=3
- WHEN user clicks 5th star
- THEN ratingChange emits 5, display updates to 5 filled stars

#### Scenario: Zero rating renders all empty
- GIVEN rating=0
- WHEN component renders
- THEN 5 empty stars display
