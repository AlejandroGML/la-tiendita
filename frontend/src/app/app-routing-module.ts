import { NgModule } from '@angular/core';
import { type CanMatchFn, RouterModule, Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { AdminLayoutComponent } from './layout/admin-layout/admin-layout';

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
          import('./features/admin/dashboard/admin-dashboard-module').then(
            (m) => m.AdminDashboardModule,
          ),
      },
    ],
  },
  {
    path: 'carrito',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/cart/cart-module').then((m) => m.CartModule),
  },
  {
    path: 'checkout',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/checkout/checkout-module').then(
        (m) => m.CheckoutModule,
      ),
  },
  {
    path: 'perfil',
    canActivate: [authGuard],
    children: [
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
    path: '',
    loadChildren: () =>
      import('./features/home/home-module').then((m) => m.HomeModule),
  },
  { path: '**', redirectTo: '' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
