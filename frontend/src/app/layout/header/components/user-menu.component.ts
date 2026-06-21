import {
  Component,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  OnDestroy,
  DoCheck,
  HostListener,
} from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { TOKEN_STORAGE, type TokenStorage } from '../../../core/services/token-storage.service';
import { CartService } from '../../../core/services/cart.service';
import { WishlistService } from '../../../core/services/wishlist.service';

@Component({
  selector: 'app-user-menu',
  templateUrl: './user-menu.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserMenuComponent implements DoCheck, OnDestroy {
  private readonly authService = inject(AuthService);
  private readonly authState = inject(AuthStateService);
  private readonly router = inject(Router);
  private readonly tokenStorage: TokenStorage = inject(TOKEN_STORAGE);
  private readonly cartService = inject(CartService);
  private readonly wishlistService = inject(WishlistService);
  private readonly cdr = inject(ChangeDetectorRef);

  userMenuOpen = false;
  private userMenuTimeout: ReturnType<typeof setTimeout> | null = null;
  private previousIsLoggedIn = false;

  protected get isLoggedIn(): boolean {
    return this.authState.isAuthenticated();
  }

  protected get currentUser() {
    return this.authState.currentUser();
  }

  protected get userName(): string {
    return this.currentUser?.name || '';
  }

  // ── Lifecycle ──

  ngDoCheck(): void {
    const current = this.isLoggedIn;
    if (current !== this.previousIsLoggedIn) {
      this.previousIsLoggedIn = current;
      this.cdr.markForCheck();
    }
  }

  ngOnDestroy(): void {
    this.clearUserMenuTimeout();
  }

  // ── Hover logic ──

  protected onUserMenuEnter(): void {
    this.clearUserMenuTimeout();
    this.userMenuOpen = true;
  }

  protected onUserMenuLeave(): void {
    this.userMenuTimeout = setTimeout(() => {
      this.userMenuOpen = false;
      this.cdr.markForCheck();
    }, 200);
  }

  protected clearUserMenuTimeout(): void {
    if (this.userMenuTimeout !== null) {
      clearTimeout(this.userMenuTimeout);
      this.userMenuTimeout = null;
    }
  }

  // ── Click-outside ──

  @HostListener('document:click', ['$event'])
  protected onDocumentClick(event: MouseEvent): void {
    if (this.userMenuOpen) {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-user-menu]')) {
        this.userMenuOpen = false;
        this.cdr.markForCheck();
      }
    }
  }

  // ── Auth actions ──

  protected logout(): void {
    this.userMenuOpen = false;
    this.cartService.resetState();
    this.wishlistService.resetState();
    this.authService.logout().subscribe({
      next: () => this.router.navigate(['/']),
      error: () => {
        // Even if the server call fails, clear local tokens
        this.tokenStorage.clear();
        this.authState.clearUser();
        this.router.navigate(['/']);
      },
    });
  }
}
