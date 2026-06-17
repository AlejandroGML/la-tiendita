import { Component, EventEmitter, Input, OnDestroy, OnInit, Output, signal, inject } from '@angular/core';
import { Subscription } from 'rxjs';
import { TranslateService } from '@ngx-translate/core';
import { MessageService } from 'primeng/api';
import { ReviewService } from '../../../core/services/review.service';
import { AuthStateService } from '../../../core/services/auth-state.service';
import type { Review } from '../../../shared/models/review.model';

@Component({
  selector: 'app-product-detail-reviews',
  templateUrl: './reviews.component.html',
  standalone: false,
})
export class ProductDetailReviewsComponent implements OnInit, OnDestroy {
  @Input() productId!: string;
  @Input() productSlug!: string;
  @Output() reviewSubmitted = new EventEmitter<void>();

  readonly reviews = signal<Review[]>([]);
  readonly avgRating = signal(0);
  readonly totalReviews = signal(0);
  readonly reviewPage = signal(1);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly showWriteForm = signal(false);
  readonly newRating = signal(0);
  readonly newComment = signal('');
  readonly submitting = signal(false);
  readonly submitError = signal<string | null>(null);

  private reviewService = inject(ReviewService);
  private translate = inject(TranslateService);
  readonly authState = inject(AuthStateService);
  private messageService = inject(MessageService);
  private reviewSub: Subscription | null = null;
  private submitReviewSub: Subscription | null = null;

  ngOnInit(): void {
    this.loadReviews();
  }

  ngOnDestroy(): void {
    this.reviewSub?.unsubscribe();
    this.submitReviewSub?.unsubscribe();
  }

  loadReviews(page = 1): void {
    this.reviewSub?.unsubscribe();

    this.loading.set(true);
    this.error.set(null);
    this.reviewSub = this.reviewService.getProductReviews(this.productSlug, page, 12).subscribe({
      next: (res) => {
        this.reviews.set(res.reviews);
        this.avgRating.set(res.avg_rating);
        this.totalReviews.set(res.total_reviews);
        this.reviewPage.set(res.page);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('reviews.loadError');
        this.loading.set(false);
      },
    });
  }

  onReviewPageChange(page: number): void {
    this.loadReviews(page);
  }

  submitReview(): void {
    if (this.newRating() < 1) {
      this.submitError.set('reviews.ratingRequired');
      return;
    }

    this.submitting.set(true);
    this.submitError.set(null);

    const payload = {
      rating: this.newRating(),
      comment: this.newComment().trim() || undefined,
    };

    this.submitReviewSub?.unsubscribe();
    this.submitReviewSub = this.reviewService.createReview(this.productId, payload).subscribe({
      next: () => {
        this.submitting.set(false);
        this.resetWriteForm();
        this.loadReviews();
        this.reviewSubmitted.emit();
      },
      error: (err) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          this.submitError.set('reviews.duplicate');
        } else if (err?.status === 403) {
          this.submitError.set('reviews.nonBuyer');
        } else {
          this.submitError.set('reviews.error');
        }
      },
    });
  }

  resetWriteForm(): void {
    this.showWriteForm.set(false);
    this.newRating.set(0);
    this.newComment.set('');
    this.submitError.set(null);
  }
}
