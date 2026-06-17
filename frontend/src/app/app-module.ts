import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { TranslateModule } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeuix/themes/aura';

import { AppRoutingModule } from './app-routing-module';
import { LayoutModule } from './layout/layout-module';
import { AdminLayoutModule } from './layout/admin-layout/admin-layout-module';
import { App } from './app';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { provideTokenStorage } from './core/services/token-storage.service';

@NgModule({
  declarations: [App],
  imports: [
    BrowserModule,
    AppRoutingModule,
    LayoutModule,
    AdminLayoutModule,
    TranslateModule.forRoot({ defaultLanguage: 'es' }),
  ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideAnimations(),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
    provideTokenStorage(),
    provideTranslateHttpLoader(),
    providePrimeNG({
      theme: {
        preset: Aura,
        options: {
          darkModeSelector: '.dark-theme',
          cssLayer: { name: 'primeng', order: 'tailwind-base, primeng, tailwind-utilities' }
        }
      }
    }),
  ],
  bootstrap: [App],
})
export class AppModule {}
