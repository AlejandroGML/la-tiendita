import { Component, inject, computed } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CartStore } from '../../core/stores/cart.store';
import { AuthStateService } from '../../core/services/auth-state.service';
import { WishlistService } from '../../core/services/wishlist.service';

@Component({
  selector: 'app-mobile-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './mobile-nav.html'
})
export class MobileNavComponent {
  cartStore = inject(CartStore);
  auth = inject(AuthStateService);
  wishlist = inject(WishlistService);

  cartCount = computed(() => this.cartStore.totalItems());
  wishlistCount = computed(() => this.wishlist.wishlistCount());
  isAuth = computed(() => this.auth.isAuthenticated());
}
