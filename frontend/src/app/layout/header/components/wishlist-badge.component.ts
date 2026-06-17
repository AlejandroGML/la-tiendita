import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef, OnDestroy, OnInit } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { AuthStateService } from '../../../core/services/auth-state.service';
import { WishlistService } from '../../../core/services/wishlist.service';
import { svgIcon } from '../../../shared/utils/svg-icons';

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
  private readonly sanitizer = inject(DomSanitizer);
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

  protected svg(name: string, className = 'w-5 h-5'): SafeHtml {
    return svgIcon(name, className, this.sanitizer) as SafeHtml;
  }

  ngOnDestroy(): void {
    this.wishlistSub?.unsubscribe();
  }
}
