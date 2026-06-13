import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-checkout-success',
  templateUrl: './checkout-success.html',
  standalone: false,
})
export class CheckoutSuccessComponent implements OnInit {
  orderId: string | null = null;
  isGuest = false;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.orderId = params['order_id'] ?? null;
      const guestParam = params['guest'];

      if (guestParam === '1') {
        this.isGuest = true;
        return;
      }

      // Authenticated user or no guest flag: redirect to order detail
      if (this.orderId) {
        this.router.navigate(['/perfil/ordenes', this.orderId]);
      } else {
        this.router.navigate(['/']);
      }
    });
  }
}
