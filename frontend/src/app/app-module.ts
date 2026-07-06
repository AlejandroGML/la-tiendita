import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { TranslateModule } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { providePrimeNG } from 'primeng/config';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialog } from 'primeng/confirmdialog';
import Aura from '@primeuix/themes/aura';

import { AppRoutingModule } from './app-routing-module';
import { SharedModule } from './shared/shared-module';
import { LayoutModule } from './layout/layout-module';
import { AdminLayoutModule } from './layout/admin-layout/admin-layout-module';
import { App } from './app';
import { CookieConsentComponent } from './shared/components/cookie-consent/cookie-consent';
import { NewsletterPopupComponent } from './shared/components/newsletter-popup/newsletter-popup';
import { MobileNavComponent } from './layout/mobile-nav/mobile-nav';
import { ScrollTopComponent } from './shared/components/scroll-top/scroll-top';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { provideTokenStorage } from './core/services/token-storage.service';

@NgModule({
  declarations: [App],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SharedModule,
    LayoutModule,
    AdminLayoutModule,
    ConfirmDialog,
    CookieConsentComponent,
    NewsletterPopupComponent,
    MobileNavComponent,
    ScrollTopComponent,
    TranslateModule.forRoot(),
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
    ConfirmationService,
  ],
  bootstrap: [App],
})
export class AppModule {}
