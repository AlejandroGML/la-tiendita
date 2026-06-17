import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../shared/shared-module';
import { Header } from './header/header';
import { Footer } from './footer/footer';
import { CartBadgeComponent } from './header/components/cart-badge.component';
import { WishlistBadgeComponent } from './header/components/wishlist-badge.component';
import { UserMenuComponent } from './header/components/user-menu.component';
import { ThemeToggleComponent } from './header/components/theme-toggle.component';
import { LanguageSwitcherComponent } from './header/components/language-switcher.component';
import { CurrencySwitcherComponent } from './header/components/currency-switcher.component';

@NgModule({
  declarations: [
    Header,
    Footer,
    CartBadgeComponent,
    WishlistBadgeComponent,
    UserMenuComponent,
    ThemeToggleComponent,
    LanguageSwitcherComponent,
    CurrencySwitcherComponent,
  ],
  imports: [CommonModule, SharedModule, RouterModule],
  exports: [Header, Footer],
})
export class LayoutModule {}
