import { NgModule } from '@angular/core';
import { type CanMatchFn, RouterModule, Routes } from '@angular/router';

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
