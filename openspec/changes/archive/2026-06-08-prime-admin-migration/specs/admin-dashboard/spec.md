# Delta for admin-dashboard

## MODIFIED Requirements

### Requirement: Admin Layout with Sidebar Navigation

The frontend MUST provide a shared `AdminLayout` component with a Tailwind flex sidebar (`flex h-screen`, `w-60` sidebar + `flex-1 overflow-auto` content) using a `p-toolbar` header. Navigation items MUST use plain `<a routerLink>` tags with PrimeIcons `pi` classes instead of `mat-icon` and `mat-nav-list`. Sidebar MUST list admin sections: Dashboard, Products, Users, Orders. Active route MUST show left-border highlight. All admin child routes MUST render inside this layout's `<router-outlet>`.

(Previously: Required `MatSidenav` sidebar with `mat-nav-list` and `mat-icon` under a `mat-toolbar` header.)

#### Scenario: Admin navigates via sidebar

- GIVEN an admin user is on `/admin/dashboard`
- WHEN they click "Users" in the sidebar
- THEN the router navigates to `/admin/usuarios` and the users component renders

#### Scenario: Non-admin redirected from admin route

- GIVEN a customer tries to access `/admin/dashboard`
- WHEN the route guard executes
- THEN the user is redirected to `/`

#### Scenario: Sidebar renders with PrimeNG toolbar and icons

- GIVEN admin layout initializes
- WHEN the admin panel loads
- THEN `p-toolbar` renders at top with app branding
- AND sidebar links display `pi` icons (e.g., `pi-home`, `pi-box`, `pi-users`, `pi-shopping-cart`)
- AND active route shows `border-l-4 border-primary` highlight
