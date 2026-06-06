import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';
import { TranslateModule } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';

import { AppRoutingModule } from './app-routing-module';
import { LayoutModule } from './layout/layout-module';
import { App } from './app';

@NgModule({
  declarations: [App],
  imports: [
    BrowserModule,
    AppRoutingModule,
    LayoutModule,
    TranslateModule.forRoot({ defaultLanguage: 'es' }),
  ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideAnimations(),
    provideHttpClient(),
    provideTranslateHttpLoader(),
  ],
  bootstrap: [App],
})
export class AppModule {}
