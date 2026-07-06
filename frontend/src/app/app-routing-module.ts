import { NgModule } from '@angular/core';
import { type CanMatchFn, RouterModule, Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { AdminLayoutComponent } from './layout/admin-layout/admin-layout';
import { RegistrationSuccess } from './features/auth/registration-success/registration-success';
import { AdminLogin } from './features/admin/login/admin-login';
import { AdminVerify2fa } from './features/admin/login/admin-verify-2fa';
import { PrivacyComponent } from './features/legal/privacy/privacy';
import { TermsComponent } from './features/legal/terms/terms';

/** Only match auth-prefixed paths so the AuthModule is lazy-loaded on demand. */
const authCanMatch: CanMatchFn = (_route, segments) => {
  if (segments.length >= 1) {
    const path = segments[0].path;
    return path === 'login' || path === 'register';
  }
  return false;
};

const routes: Routes = [
  {
    path: 'recuperar',
    redirectTo: '/login',
  },
  {
    path: 'reset-password',
    redirectTo: '/login',
  },
  {
    path: '',
    canMatch: [authCanMatch],
    loadChildren: () =>
      import('./features/auth/auth-module').then((m) => m.AuthModule),
  },
  {
    path: 'productos',
    children: [
      {
        path: '',
        loadChildren: () =>
          import('./features/products/product-list-module').then(
            (m) => m.ProductListModule,
          ),
      },
      {
        path: ':slug',
        loadChildren: () =>
          import('./features/product-detail/product-detail-module').then(
            (m) => m.ProductDetailModule,
          ),
      },
    ],
  },
  {
    path: 'admin/login/verify-2fa',
    component: AdminVerify2fa,
  },
  {
    path: 'admin/login',
    component: AdminLogin,
  },
  {
    path: 'admin',
    canActivate: [authGuard, adminGuard],
    component: AdminLayoutComponent,
    children: [
      {
        path: '',
        loadChildren: () =>
          import('./features/admin/dashboard/admin-dashboard-module').then(
            (m) => m.AdminDashboardModule,
          ),
      },
      {
        path: 'productos',
        children: [
          {
            path: 'nuevo',
            loadChildren: () =>
              import('./features/admin/product-form/admin-product-form-module').then(
                (m) => m.AdminProductFormModule,
              ),
          },
          {
            path: ':slug',
            loadChildren: () =>
              import('./features/admin/product-form/admin-product-form-module').then(
                (m) => m.AdminProductFormModule,
              ),
          },
          {
            path: '',
            loadChildren: () =>
              import('./features/admin/products/admin-products-module').then(
                (m) => m.AdminProductsModule,
              ),
          },
        ],
      },
      {
        path: 'usuarios',
        loadChildren: () =>
          import('./features/admin/users/admin-users-module').then(
            (m) => m.AdminUsersModule,
          ),
      },
      {
        path: 'ordenes',
        loadChildren: () =>
          import('./features/admin/orders/admin-orders-module').then(
            (m) => m.AdminOrdersModule,
          ),
      },
      {
        path: 'categorias',
        loadChildren: () =>
          import('./features/admin/categories/admin-categories-module').then(
            (m) => m.AdminCategoriesModule,
          ),
      },
      {
        path: 'promociones',
        loadChildren: () =>
          import('./features/admin/promotions/admin-promotions-module').then(
            (m) => m.AdminPromotionsModule,
          ),
      },
    ],
  },
  {
    path: 'registro-exitoso',
    component: RegistrationSuccess,
  },
  {
    path: 'carrito',
    loadChildren: () =>
      import('./features/cart/cart-module').then((m) => m.CartModule),
  },
  {
    path: 'checkout',
    children: [
      {
        path: 'success',
        loadChildren: () =>
          import('./features/checkout/success/checkout-success-module').then(
            (m) => m.CheckoutSuccessModule,
          ),
      },
      {
        path: '',
        loadChildren: () =>
          import('./features/checkout/checkout-module').then(
            (m) => m.CheckoutModule,
          ),
      },
    ],
  },
  {
    path: 'wishlist',
    canActivate: [],
    loadChildren: () =>
      import('./features/profile/wishlist/wishlist-module').then(
        (m) => m.WishlistModule,
      ),
  },
  {
    path: 'perfil',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadChildren: () =>
          import('./features/profile/profile-view/profile-view-module').then(
            (m) => m.ProfileViewModule,
          ),
      },
      {
        path: 'wishlist',
        loadChildren: () =>
          import('./features/profile/wishlist/wishlist-module').then(
            (m) => m.WishlistModule,
          ),
      },
      {
        path: 'ordenes',
        children: [
          {
            path: ':id',
            loadChildren: () =>
              import('./features/profile/order-detail/order-detail-module').then(
                (m) => m.OrderDetailModule,
              ),
          },
          {
            path: '',
            loadChildren: () =>
              import('./features/profile/order-list/order-list-module').then(
                (m) => m.OrderListModule,
              ),
          },
        ],
      },
    ],
  },
  {
    path: 'nuevos',
    loadChildren: () =>
      import('./features/new-arrivals/new-arrivals.module').then(
        (m) => m.NewArrivalsModule,
      ),
  },
  {
    path: 'ofertas',
    loadChildren: () =>
      import('./features/sale/sale.module').then((m) => m.SaleModule),
  },
  {
    path: '',
    loadChildren: () =>
      import('./features/home/home-module').then((m) => m.HomeModule),
  },
  {
    path: 'privacidad',
    component: PrivacyComponent,
  },
  {
    path: 'terminos',
    component: TermsComponent,
  },
  { path: '**', redirectTo: '' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
