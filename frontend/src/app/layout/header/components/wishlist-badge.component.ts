import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { WishlistService } from '../../../core/services/wishlist.service';

@Component({
  selector: 'app-wishlist-badge',
  templateUrl: './wishlist-badge.component.html',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WishlistBadgeComponent implements OnInit, OnDestroy {
  private readonly wishlistService = inject(WishlistService);
  private readonly authState = inject(AuthStateService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  wishlistCount = 0;
  private wishlistSub: Subscription | null = null;

  ngOnInit(): void {
    this.wishlistSub = this.wishlistService.wishlist$.subscribe((wishlist) => {
      this.wishlistCount = wishlist?.items?.length ?? 0;
      this.cdr.markForCheck();
    });

    // Fetch wishlist for authenticated users only
    if (this.authState.isAuthenticated()) {
      this.wishlistService.getWishlist().subscribe();
    }
  }

  protected navigateToWishlist(): void {
    this.router.navigate(['/wishlist']);
  }

  ngOnDestroy(): void {
    this.wishlistSub?.unsubscribe();
  }
}
