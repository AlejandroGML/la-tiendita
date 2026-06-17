import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-product-rating',
  templateUrl: './product-rating.component.html',
  standalone: false,
})
export class ProductRatingComponent {
  @Input({ required: true }) avgRating!: number;
  @Input({ required: true }) totalReviews!: number;

  get hasReviews(): boolean {
    return this.totalReviews > 0;
  }
}
