import { Component, EventEmitter, Input, Output } from '@angular/core';

type StarSize = 'small' | 'medium';

@Component({
  selector: 'app-star-rating',
  templateUrl: './star-rating.html',
  styleUrls: ['./star-rating.scss'],
  standalone: false,
})
export class StarRatingComponent {
  @Input() rating = 0;
  @Input() readonly = true;
  @Input() size: StarSize = 'medium';
  @Output() ratingChange = new EventEmitter<number>();

  get stars(): number[] {
    return [1, 2, 3, 4, 5];
  }

  get starSize(): string {
    return this.size === 'small' ? 'text-lg' : 'text-2xl';
  }

  get starGap(): string {
    return this.size === 'small' ? 'gap-0.5' : 'gap-1';
  }

  starFill(starIndex: number): 'full' | 'half' | 'empty' {
    const diff = this.rating - (starIndex - 1);
    if (diff >= 1) return 'full';
    if (diff > 0 && diff < 1) return 'half';
    return 'empty';
  }

  starIcon(starIndex: number): string {
    const fill = this.starFill(starIndex);
    if (fill === 'full') return 'star';
    if (fill === 'half') return 'star_half';
    return 'star_border';
  }

  handleClick(starIndex: number): void {
    if (this.readonly) return;
    this.rating = starIndex;
    this.ratingChange.emit(starIndex);
  }

  handleKeydown(event: KeyboardEvent, starIndex: number): void {
    if (this.readonly) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.handleClick(starIndex);
    }
  }
}
