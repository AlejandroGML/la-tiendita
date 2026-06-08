import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-star-rating',
  templateUrl: './star-rating.html',
  styleUrls: ['./star-rating.scss'],
  standalone: false,
})
export class StarRatingComponent {
  @Input() rating = 0;
  @Input() readonly = true;
  @Output() ratingChange = new EventEmitter<number>();

  onRate(event: { value: number }): void {
    this.ratingChange.emit(event.value);
  }
}
